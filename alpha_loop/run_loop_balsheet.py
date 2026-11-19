from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "单数据集资产负债表质量/现金创造"

CANDIDATES = [
    ("eur_cfo_assets2", "经营现金流/总资产:单位资产现金创造,与CFO/EV、CFO/流动资产不同分母",
     "group_zscore(cashflow_op / assets, subindustry)", 10, 0.05),
    ("eur_bs_pay2", "应付账款/流动资产:占用上游资金能力=议价权",
     "group_zscore(accounts_payable_notes / accounts_total_current_assets, subindustry)", 10, 0.05),
    ("eur_bs_payrecv2", "应付/应收:净营运资本地位,高者不垫资",
     "group_zscore(accounts_payable_notes / accounts_receivable_total_5, subindustry)", 10, 0.05),
    ("eur_bs_accrued2", "应计费用/流动资产:隐性义务占比,低者报表更干净",
     "group_zscore(-(accrued_expenses_current / accounts_total_current_assets), subindustry)", 10, 0.05),
    ("eur_bs_acq2", "并购支出/总资产:扩张强度,高者商誉减值风险",
     "group_zscore(-(acquisition_of_businesses / assets), subindustry)", 10, 0.05),
    ("eur_bs_aging2", "累计折旧/总资产:资产老化,高者投资不足",
     "group_zscore(-(accumulated_depreciation_total_assets / assets), subindustry)", 10, 0.05),
    ("eur_bs_recmix2", "应收/(应收+应付):客户账期压力",
     "group_zscore(-(accounts_receivable_total_5 / (accounts_receivable_total_5 + accounts_payable_notes)), subindustry)", 10, 0.05),
    ("eur_bs_capex", "资本开支/总资产:投资强度",
     "group_zscore(-(capex / assets), subindustry)", 10, 0.05),
    ("eur_bs_lev", "长期负债/总资产:杠杆",
     "group_zscore(-(debt_lt / assets), subindustry)", 10, 0.05),
    ("eur_bs_cur", "流动比率:短期偿付能力",
     "group_zscore(current_ratio, subindustry)", 10, 0.05),
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
                    decay, "", "", "", "SIM_ERROR", str(res.get("body") if res else "")[:80], "", "重试或换式"])
            continue
        v = judge.verdict(res.get("alpha") or {}, "EUR")
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        append([tag, mech, MECH, idx, tag, res["alpha_id"], expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                decay, m.get("S"), m.get("F"), m.get("TO"), v.get("status"),
                ",".join(v.get("fail_codes") or []), "", "合格即提交" if v["status"] == "PASS_READY" else "换下一条"])
        if v["status"] == "PASS_READY":
            ok, pre = submit.precheck(brain, res["alpha_id"])
            print(f"  precheck {ok} {pre}", flush=True)
            if ok:
                sr = submit.submit(brain, res["alpha_id"])
                print(f"  submit {sr.get('result')} {sr.get('fails')}", flush=True)
                if sr.get("result") != "REJECTED" and submit.confirm(brain, res["alpha_id"]):
                    print("  ACCEPTED", flush=True)
        time.sleep(2)
    print("\nLOOP_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())