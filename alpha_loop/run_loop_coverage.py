from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "覆盖/偿债能力（分子用已验证有信号的现金流）"

CANDIDATES = [
    ("eur_c_debt", "经营现金流/总负债:用真实现金覆盖债务的能力,比利润更可信",
     "group_zscore(cashflow_op / debt, subindustry)", 10, 0.05),
    ("eur_c_cashdebt", "现金及等价物/总负债:静态流动性对债务的覆盖厚度",
     "group_zscore(cash_equivalents_total / debt, subindustry)", 10, 0.05),
    ("eur_c_intcov", "EBITDA/财务费用:利息覆盖倍数,高者盈利不易被利息吞噬",
     "group_zscore(ebitda / finance_costs_deferred_payment, subindustry)", 10, 0.05),
    ("eur_c_debtshort", "短期负债/长期负债(负向):债务短期化=再融资压力",
     "group_zscore(-(debt_st / debt_lt), subindustry)", 10, 0.05),
    ("eur_c_divcov", "经营现金流/应付股利:分红被现金流覆盖的程度",
     "group_zscore(cashflow_op / dividends_payable_short_term, subindustry)", 10, 0.05),
    ("eur_c_cfo_lt", "经营现金流/长期负债:长债偿付的现金保障",
     "group_zscore(cashflow_op / debt_lt, subindustry)", 10, 0.05),
    ("eur_c_curliab", "经营现金流/流动负债:短期偿债的现金保障",
     "group_zscore(cashflow_op / current_liabilities_total_4, subindustry)", 10, 0.05),
    ("eur_c_equitydbt", "权益/总负债:资本结构中权益缓冲厚度",
     "group_zscore(equity / debt, subindustry)", 10, 0.05),
]


def append(row: list) -> None:
    with io.open(LEDGER, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row + [time.strftime("%Y-%m-%d %H:%M:%S")])


def main() -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load("EUR", "TOP2500")
    for idx, (tag, mech, expr, decay, trunc) in enumerate(CANDIDATES, 1):
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
                    decay, "", "", "", "GATE_FAIL", str(d_d.get("reason") or d_a.get("reason")), "", "换下一条"])
            continue
        settings = composer.choose_settings("EUR", "TOP2500", idx)
        settings["neutralization"] = "SUBINDUSTRY"
        settings["decay"] = decay
        settings["truncation"] = trunc
        unit = {"unit_id": tag, "idea_id": tag, "region": "EUR", "shape": "custom",
                "params": {"neut": "SUBINDUSTRY", "decay": decay}, "expr": expr,
                "dataset": ds, "fields": d_a["fields"], "settings": settings}
        res = None
        for attempt in range(5):
            res = run(brain, unit)
            if res.get("status") == "done":
                break
            print(f"  TRY{attempt+1} {res.get('status')} {res.get('http')} {str(res.get('body'))[:90]}", flush=True)
            if str(res.get("http")) == "401":
                brain.relogin()
            time.sleep(15)
        if not res or res.get("status") != "done":
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    decay, "", "", "", "SIM_ERROR", str(res.get("body") if res else "")[:80], "", "换下一条"])
            continue
        v = judge.verdict(res.get("alpha") or {}, "EUR")
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        append([tag, mech, MECH, idx, tag, res["alpha_id"], expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                decay, m.get("S"), m.get("F"), m.get("TO"), v.get("status"),
                ",".join(v.get("fail_codes") or []), "", "合格即提交" if v["status"] == "PASS_READY" else "换下一条"])
        if v["status"] == "PASS_READY":
            sr = submit.submit(brain, res["alpha_id"])
            print(f"  submit {sr.get('result')} {sr.get('fails')}")
            if sr.get("result") != "REJECTED" and submit.confirm(brain, res["alpha_id"]):
                print("  ACCEPTED")
        time.sleep(2)
    print("\nLOOP4_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())