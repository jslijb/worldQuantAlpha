from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "现金流覆盖短债 × 分红意愿 × 第三质量腿"
BASE = "cashflow_op / current_liabilities_total_4"

CANDIDATES = [
    ("eur_cover3_cash", "覆盖短债 × 分红历史位置 × 现金储备厚度:三条都是现金真实性证据",
     f"group_zscore(({BASE}) * ts_rank(dividend_per_share_declared / eps, 250) * rank(cash_equivalents_total / assets), subindustry)"),
    ("eur_cover3_debt", "覆盖短债 × 分红历史位置 × 债务长期化(负向短期占比)",
     f"group_zscore(({BASE}) * ts_rank(dividend_per_share_declared / eps, 250) * rank(-(debt_st / debt_lt)), subindustry)"),
    ("eur_cover3_add", "覆盖短债 + 现金覆盖总债(相加而非相乘) 再乘分红历史位置",
     f"group_zscore(({BASE} + cash_equivalents_total / debt) * ts_rank(dividend_per_share_declared / eps, 250), subindustry)"),
]


def append(row: list) -> None:
    with io.open(LEDGER, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row + [time.strftime("%Y-%m-%d %H:%M:%S")])


def main() -> int:
    brain = Brain()
    brain.login()
    fdb = FieldDB()
    fdb.load("EUR", "TOP2500")
    for idx, (tag, mech, expr) in enumerate(CANDIDATES, 1):
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, "EUR", fdb)
        ds = (d_a.get("datasets") or ["?"])[0]
        ok_s, d_s = gates.dataset.dataset_pass(ds, "EUR", set())
        print(f"\n[{idx}/{len(CANDIDATES)}] {tag}", flush=True)
        print(f"  gates op={ok_o} depth={ok_d} atom={ok_a} ds={ds}", flush=True)
        if not (ok_o and ok_d and ok_a and ok_s):
            print("  SKIP", d_d.get("reason"), d_a.get("reason"), flush=True)
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    8, "", "", "", "GATE_FAIL", str(d_d.get("reason") or d_a.get("reason")), "", "换下一条"])
            continue
        settings = composer.choose_settings("EUR", "TOP2500", idx)
        settings["neutralization"] = "SUBINDUSTRY"
        settings["decay"] = 8
        settings["truncation"] = 0.05
        unit = {"unit_id": tag, "idea_id": tag, "region": "EUR", "shape": "custom",
                "params": {"neut": "SUBINDUSTRY", "decay": 8}, "expr": expr,
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
                    8, "", "", "", "SIM_ERROR", str(res.get("body") if res else "")[:80], "", "换下一条"])
            continue
        v = judge.verdict(res.get("alpha") or {}, "EUR")
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        append([tag, mech, MECH, idx, tag, res["alpha_id"], expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                8, m.get("S"), m.get("F"), m.get("TO"), v.get("status"),
                ",".join(v.get("fail_codes") or []), "", "合格即提交" if v["status"] == "PASS_READY" else "换下一条"])
        if v["status"] == "PASS_READY":
            sr = submit.submit(brain, res["alpha_id"])
            print(f"  submit {sr.get('result')} {sr.get('fails')}")
            if sr.get("result") != "REJECTED" and submit.confirm(brain, res["alpha_id"]):
                print("  ACCEPTED")
        time.sleep(2)
    print("\nLOOP5_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())