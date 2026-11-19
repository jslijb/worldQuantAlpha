from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "单数据集盈利质量/资本政策"

CANDIDATES = [
    ("eur_q_payout", "分红率=每股分红/EPS:管理层对未来现金流的信心,分红是对账面利润的验伪",
     "group_zscore(dividend_per_share_declared / eps, subindustry)", 10, 0.05),
    ("eur_q_extr", "非经常项目/税前利润:一次性损益占比高=盈利不可持续",
     "group_zscore(-(extraordinary_items_total_2 / earnings_before_tax), subindustry)", 10, 0.05),
    ("eur_q_extrnet", "非经常净收益/总资产:一次性收益越多越不可靠",
     "group_zscore(-(extraordinary_net_income_credits / assets), subindustry)", 10, 0.05),
    ("eur_q_cashres", "现金及等价物/总资产:流动性储备厚度,危机抗压",
     "group_zscore(cash_equivalents_total / assets, subindustry)", 10, 0.05),
    ("eur_q_gwillimp", "递延商誉费用/总资产:商誉摊销压力,高者未来减值风险",
     "group_zscore(-(deferred_charge_goodwill / assets), subindustry)", 10, 0.05),
    ("eur_q_fincost", "财务费用/EBIT:利息负担占经营利润比,高者盈利脆弱",
     "group_zscore(-(finance_costs_deferred_payment / ebit), subindustry)", 10, 0.05),
    ("eur_q_eqcorr", "权益修正/权益:会计修正占权益比,高者历史报表质量差",
     "group_zscore(-(equity_corrections / equity), subindustry)", 10, 0.05),
    ("eur_q_capstock", "股本发行/权益:靠增发融资的程度,高者股东稀释",
     "group_zscore(-(capital_stock_issued / equity), subindustry)", 10, 0.05),
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
        print(f"  gates op={ok_o} depth={ok_d} atom={ok_a} ds={ds} dsgate={ok_s}", flush=True)
        if not (ok_o and ok_d and ok_a and ok_s):
            print("  SKIP", d_d.get("reason"), d_a.get("reason"), d_s.get("reason"), flush=True)
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
    print("\nLOOP2_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())