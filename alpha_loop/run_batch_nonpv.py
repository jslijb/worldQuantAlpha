from __future__ import annotations

import json
import time

from . import composer, config, gates, judge, ledger, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

CANDIDATES = [
    ("cfoev_d10_sub", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(cashflow_op / enterprise_value, subindustry)"),
    ("cfoev_d20_ind", "EUR", "TOP2500", "INDUSTRY", 20, 0.08,
     "group_zscore(cashflow_op / enterprise_value, industry)"),
    ("ebitda_ev", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(ebitda / enterprise_value, subindustry)"),
    ("cfo_ev_rank", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(ts_rank(cashflow_op / enterprise_value, 250), subindustry)"),
    ("cfo_assets", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(cashflow_op / accounts_total_current_assets, subindustry)"),
    ("ebitda_assets", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(ebitda / accounts_total_current_assets, subindustry)"),
    ("cfi_ev", "EUR", "TOP2500", "SUBINDUSTRY", 10, 0.05,
     "group_zscore(cash_flow_from_investing_value / enterprise_value, subindustry)"),
]


def main(brain=None) -> int:
    brain = brain or Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    passed = []
    for tag, market, uni, neut, decay, trunc, expr in CANDIDATES:
        fdb = FieldDB()
        fdb.load(market, uni)
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, market, fdb)
        ds = (d_a.get("datasets") or ["?"])[0]
        ok_s, d_s = gates.dataset.dataset_pass(ds, market, set())
        print(f"\n[{tag}] gates op={ok_o} depth={ok_d} atom={ok_a} ds={ds} dsgate={ok_s}", flush=True)
        if not (ok_o and ok_d and ok_a and ok_s):
            print("  SKIP", d_d.get("reason"), d_a.get("reason"), d_s.get("reason"), flush=True)
            time.sleep(1)
            continue
        settings = composer.choose_settings(market, uni, 0)
        settings["neutralization"] = neut
        settings["decay"] = decay
        settings["truncation"] = trunc
        unit = {"unit_id": tag, "idea_id": tag, "region": market, "shape": "custom",
                "params": {"neut": neut, "decay": decay}, "expr": expr,
                "dataset": ds, "fields": d_a["fields"], "settings": settings}
        for attempt in range(6):
            res = run(brain, unit)
            st = res.get("status")
            if st == "done":
                break
            code = str(res.get("http"))
            print(f"  TRY{attempt+1} {st} {code} {str(res.get('body'))[:100]}", flush=True)
            if code == "401":
                brain.relogin()
            time.sleep(20)
        else:
            print("  GAVE_UP", flush=True)
            continue
        v = judge.verdict(res.get("alpha") or {}, market)
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} "
              f"{(v.get('fail_codes') or [])}", flush=True)
        if v["status"] == "PASS_READY":
            passed.append((res["alpha_id"], unit, m, v))
            print("  *** PASS_READY ***", flush=True)
        time.sleep(2)
    print("\n=== BATCH DONE, pass =", len(passed), flush=True)
    for aid, unit, m, v in passed:
        if not submit.clock_gate():
            print(f"  {aid} 过线，等提交窗口", flush=True)
            continue
        ok, pre = submit.precheck(brain, aid)
        print(f"  precheck {aid} {ok} {pre}", flush=True)
        if not ok:
            continue
        res = submit.submit(brain, aid)
        print(f"  submit {aid} {res.get('result')} {res.get('fails')}", flush=True)
        if res.get("result") == "REJECTED":
            continue
        if submit.confirm(brain, aid):
            a = brain.get_json(f"/alphas/{aid}") or {}
            is_ = a.get("is") or {}
            ledger.append({"id": aid, "expr": unit["expr"], "S": is_.get("sharpe"),
                           "F": is_.get("fitness"), "T": is_.get("turnover"),
                           "R": is_.get("returns"), "DD": is_.get("drawdown"),
                           "dateSubmitted": a.get("dateSubmitted"),
                           "region": unit["region"], "universe": unit["settings"].get("universe"),
                           "neutralization": unit["settings"].get("neutralization"),
                           "idea_id": unit["idea_id"], "shape": "custom"})
            print(f"  ACCEPTED {aid} ledger={len(ledger.rows())}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())