from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "慢变存量改用历史位置/年度变化（算子-数据匹配）"

CANDIDATES = [
    ("eur_h_pay", "应付/流动资产的历史位置:议价权相对自身过去更强=新信息",
     "group_zscore(ts_rank(accounts_payable_notes / accounts_total_current_assets, 500), subindustry)", 10, 0.05),
    ("eur_h_recv", "应收/流动资产的历史位置(负向):被下游占款相对过去更重=坏",
     "group_zscore(-ts_rank(accounts_receivable_total_5 / accounts_total_current_assets, 500), subindustry)", 10, 0.05),
    ("eur_h_accrued", "应计费用/流动资产的年度变化(负向):隐性义务加速堆积",
     "group_zscore(-ts_delta(accrued_expenses_current / accounts_total_current_assets, 252), subindustry)", 10, 0.05),
    ("eur_h_payout", "分红率历史位置:持续提高分红=现金流真实性被反复验证",
     "group_zscore(ts_rank(dividend_per_share_declared / eps, 500), subindustry)", 10, 0.05),
    ("eur_h_extr", "非经常项目/税前利润的年度变化(负向):一次性损益突然放大=质量下滑",
     "group_zscore(-ts_delta(extraordinary_items_total_2 / earnings_before_tax, 252), subindustry)", 10, 0.05),
    ("eur_h_capstock", "股本发行/权益历史位置(负向):反复增发=持续稀释",
     "group_zscore(-ts_rank(capital_stock_issued / equity, 500), subindustry)", 10, 0.05),
    ("eur_h_cashres", "现金/资产年度变化:流动性储备的边际改善",
     "group_zscore(ts_delta(cash_equivalents_total / assets, 252), subindustry)", 10, 0.05),
    ("eur_h_acq", "收购/资产历史位置(负向):并购强度处于自身高位=商誉风险",
     "group_zscore(-ts_rank(acquisition_of_businesses / assets, 500), subindustry)", 10, 0.05),
    ("eur_h_cfo_lvl", "CFO/总资产历史位置:现金创造的相对自身改善(对照,流量科目也应有效)",
     "group_zscore(ts_rank(cashflow_op / assets, 500), subindustry)", 10, 0.05),
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
    print("\nLOOP3_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())