from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "EUR可达性验证：非量价能否S>=1.58且PROD干净"

CANDIDATES = [
    ("v_a1_consist2", "营收与利润修正一致性：同向上修=真实改善，背离=成本操纵或价格战",
     "group_zscore((analyst_upward_revision_count_fq1_revenue_14d_5 - analyst_downward_revision_count_fq1_revenue_14d_4) / (analyst_upward_revision_count_fq1_revenue_14d_5 + analyst_downward_revision_count_fq1_revenue_14d_4 + 1) * (analyst_upward_revision_count_fq1_earnings_14d_5 - analyst_downward_revision_count_fq1_earnings_14d_4) / (analyst_upward_revision_count_fq1_earnings_14d_5 + analyst_downward_revision_count_fq1_earnings_14d_4 + 1), subindustry)"),
    ("v_tpd_dev", "目标价扩散度偏离自身常态：扩散度异常升高=分歧加剧",
     "group_zscore(analyst_target_price_diffusion_1m - ts_mean(analyst_target_price_diffusion_1m, 250), subindustry)"),
    ("v_empdiv_dev", "员工多元化偏离自身常态：组织质量边际变化",
     "group_zscore(employee_diversity_industry_percentile_score - ts_mean(employee_diversity_industry_percentile_score, 250), subindustry)"),
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
    summary = []
    for idx, (tag, mech, expr) in enumerate(CANDIDATES, 1):
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, "EUR", fdb)
        ds = (d_a.get("datasets") or ["?"])[0]
        print(f"\n[{idx}/5] {tag} ds={ds} atom={ok_a} depth={ok_d}", flush=True)
        if not (ok_o and ok_d and ok_a):
            print("  SKIP", d_d.get("reason"), d_a.get("reason"), flush=True)
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    0, "", "", "", "GATE_FAIL", str(d_d.get("reason") or d_a.get("reason")), "", "换下一条"])
            summary.append((tag, "GATE_FAIL", None, None, None))
            continue
        settings = composer.choose_settings("EUR", "TOP2500", idx)
        settings["neutralization"] = "SUBINDUSTRY"
        settings["decay"] = 0
        settings["truncation"] = 0.05
        unit = {"unit_id": tag, "idea_id": tag, "region": "EUR", "shape": "custom",
                "params": {"neut": "SUBINDUSTRY", "decay": 0}, "expr": expr,
                "dataset": ds, "fields": d_a["fields"], "settings": settings}
        res = None
        for attempt in range(5):
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
            summary.append((tag, "SIM_ERROR", None, None, None))
            continue
        v = judge.verdict(res.get("alpha") or {}, "EUR")
        m = v.get("metrics") or {}
        aid = res["alpha_id"]
        print(f"  {aid} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        verdict = v.get("status")
        prod = None
        if v["status"] == "PASS_READY":
            r = brain.post(f"/alphas/{aid}/submit")
            loc = r.headers.get("Location")
            body = {}
            if r.status_code == 403:
                body = r.json()
            elif loc:
                for i in range(10):
                    rr = b_get(brain, loc)
                    if rr:
                        body = rr
                        break
                    time.sleep(15)
            fails = [c.get("name") for c in body.get("is", {}).get("checks") or [] if str(c.get("result")).upper() == "FAIL"]
            prod = next((c.get("value") for c in body.get("is", {}).get("checks") or [] if c.get("name") == "PROD_CORRELATION"), None)
            print(f"  SUBMIT {r.status_code} fails={fails} prod={prod}", flush=True)
            verdict = f"SUBMIT:{','.join(fails) or 'ACCEPT'}"
        append([tag, mech, MECH, idx, tag, aid, expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                0, m.get("S"), m.get("F"), m.get("TO"), verdict,
                ",".join(v.get("fail_codes") or []), "", f"PROD={prod}" if prod is not None else "S未过线未提交"])
        summary.append((tag, verdict, m.get("S"), m.get("F"), prod))
        time.sleep(2)
    print("\n=== 可达性验证汇总 ===", flush=True)
    for t, vd, s, f, p in summary:
        print(f"  {t:14} {str(vd):28} S={s} F={f} PROD={p}", flush=True)
    return 0


def b_get(brain, loc):
    r = brain.get(loc)
    txt = (r.text or "").strip()
    if not txt:
        return None
    try:
        return r.json()
    except Exception:
        return None


if __name__ == "__main__":
    raise SystemExit(main())