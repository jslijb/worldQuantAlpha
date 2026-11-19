from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "CFO/短债 五腿内核固定，只换最终外壳与权重形状，目标把 PROD 从 0.7020 压到 0.69 以下"

CORE = ("(cashflow_op / current_liabilities_total_4)"
        " * ts_rank(dividend_per_share_declared / eps, 140)"
        " * rank(cash_equivalents_total / assets)"
        " * rank(cashflow_op / ebitda)"
        " * rank(current_ratio)")

DIV = "ts_rank(dividend_per_share_declared / eps, 140)"

CANDIDATES = [
    ("c5_shell_gscale",
     "五个现金流真实性证据同向相乘 = 只有现金创造、分红兑现、低杠杆、现金厚、短偿能力都好的公司才拿高分；外壳换成有界 min-max，避免离群股拿极端权重",
     f"group_scale({CORE}, subindustry)"),
    ("c5_shell_grank",
     "同一内核换秩外壳：只看同业相对名次，对冲掉规模与行业量纲；与池内 group_rank 骨架对照，验证拥挤是否来自同一排序语义",
     f"group_rank({CORE}, subindustry)"),
    ("c5_shell_smooth",
     "同一内核外面加线性衰减平滑：五腿都是季频慢变量，平滑只改持仓迁移路径不改信号方向，用来检验 PROD 是否被短窗抖动放大",
     f"group_zscore(ts_decay_linear({CORE}, 10), subindustry)"),
    ("c5_shell_softgate",
     "把分红腿由线性乘子改成平方软门槛：分红覆盖低的企业其现金创造不被采信（可能是财务粉饰），高覆盖者权重放大但不做 if_else 硬切换以免持仓集合跳变",
     f"group_scale({CORE.replace(DIV, DIV + ' * ' + DIV)}, subindustry)"),
]


def append(row: list) -> None:
    with io.open(LEDGER, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row + [time.strftime("%Y-%m-%d %H:%M:%S")])


def main(only: str | None = None) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load("EUR", "TOP2500")
    for idx, (tag, mech, expr) in enumerate(CANDIDATES, 1):
        if only and tag != only:
            continue
        print(f"\n[{idx}/{len(CANDIDATES)}] {tag}", flush=True)
        print(f"  {mech}", flush=True)
        ok_o, d_o = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, "EUR", fdb)
        ds = (d_a.get("datasets") or ["fundamental23"])[0]
        ok_s, d_s = gates.dataset.dataset_pass(ds, "EUR", set())
        print(f"  gates op={ok_o} depth={ok_d} atom={ok_a} ds={ds}", flush=True)
        if not (ok_o and ok_d and ok_a and ok_s):
            print("  SKIP", d_o.get("reason"), d_d.get("reason"), d_a.get("reason"), flush=True)
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    0, "", "", "", "GATE_FAIL",
                    str(d_d.get("reason") or d_a.get("reason") or d_o.get("reason")), "", "换下一条"])
            continue
        settings = composer.choose_settings("EUR", "TOP2500", idx)
        settings["neutralization"] = "SUBINDUSTRY"
        settings["decay"] = 0
        settings["truncation"] = 0.05
        unit = {"unit_id": tag, "idea_id": "cover5_shell", "region": "EUR", "shape": "custom",
                "params": {"neut": "SUBINDUSTRY", "decay": 0}, "expr": expr,
                "dataset": ds, "fields": d_a["fields"], "settings": settings}
        res = None
        for attempt in range(6):
            res = run(brain, unit)
            if res.get("status") == "done":
                break
            print(f"  TRY{attempt+1} {res.get('status')} {res.get('http')}", flush=True)
            if str(res.get("http")) == "401":
                brain.relogin()
            time.sleep(20)
        if not res or res.get("status") != "done":
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    0, "", "", "", "SIM_ERROR", str(res.get("body") if res else "")[:80], "", "换下一条"])
            continue
        v = judge.verdict(res.get("alpha") or {}, "EUR")
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        append([tag, mech, MECH, idx, tag, res["alpha_id"], expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                0, m.get("S"), m.get("F"), m.get("TO"), v.get("status"),
                ",".join(v.get("fail_codes") or []), "", "合格即提交" if v["status"] == "PASS_READY" else "看 falsify"])
        if v["status"] == "PASS_READY":
            sr = submit.submit(brain, res["alpha_id"])
            print(f"  submit {sr.get('result')} {sr.get('fails')}", flush=True)
            if sr.get("result") != "REJECTED" and submit.confirm(brain, res["alpha_id"]):
                print("  ACCEPTED", flush=True)
        time.sleep(2)
    print("\nCOVER5_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())