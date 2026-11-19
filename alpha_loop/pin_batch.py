from __future__ import annotations

from . import composer, config, gates
from .auth import Brain
from .fielddb import FieldDB
from .judge import summarize, verdict
from .sim import run

PAIRS = [
    ("rev_diffusion", "analyst_upward_revision_count_fq1_earnings_14d_5",
     "analyst_downward_revision_count_fq1_earnings_14d_4",
     "analyst_revision_horizons", "A", 60, "industry"),
    ("anl15_updn", "anl15_gr_12_m_ests_up", "anl15_gr_12_m_ests_dn",
     "analyst15", "A", 60, "industry"),
    ("anl15_meanstd", "anl15_gr_12_m_mean", "anl15_gr_12_m_st_dev",
     "analyst15", "B", 45, "sector"),
    ("fnd_ar_assets", "accounts_receivable_total_5", "accounts_total_current_assets",
     "fundamental23", "A", 120, "industry"),
    ("fnd_ni_assets", "annual_net_income_value", "assets_total_2",
     "fundamental23", "A", 120, "industry"),
    ("fnd_cf_assets", "annual_statement_of_cash_flows", "assets_total_2",
     "fundamental23", "C", 120, "sector"),
    ("star_margin", "actual_last_year_ebitda_2", "actual_last_year_revenue_2",
     "predictive_starmine", "A", 60, "industry"),
    ("eps_mag_skew", "eps_y1_estimate_change_3mo", "eps_y1_estimate_skewness",
     "analyst_factor_signals", "E", 45, "sector"),
]


def _one(brain, fdb, market, idx, item):
    name, a, b, ds, shape, n, g = item
    params = {"shape": shape, "n": n, "n2": n, "g": g, "rel": "div"}
    expr = composer.compose(shape, a, b, params)
    ok_o, d_o = gates.operators.check(expr)
    ok_d, d_d = gates.depth.check(expr)
    ok_a, d_a = gates.atom.atom_pass(expr, market, fdb)
    if not (ok_o and ok_d and ok_a):
        return {"name": name, "status": "gate_fail",
                "detail": (d_o.get("reason"), d_d.get("reason"), d_a.get("reason"))}
    unit = {"unit_id": f"pin2_{name}", "idea_id": name, "region": market,
            "shape": shape, "params": params, "expr": expr,
            "dataset": d_a.get("datasets", [ds])[0], "fields": [a, b],
            "settings": composer.choose_settings(market, config.UNIVERSES[market][0], idx)}
    res = run(brain, unit)
    if res.get("status") != "done":
        return {"name": name, "status": "sim_error", "detail": str(res.get("body"))[:220]}
    v = verdict(res.get("alpha") or {}, market, extra={"shape": shape})
    return {"name": name, "status": v["status"], "alpha_id": res["alpha_id"],
            "metrics": v.get("metrics"), "fails": v.get("fail_codes"), "expr": expr}


def main(market: str = "GLB", limit: int = 8, start: int = 0, conc: int = 2) -> int:
    from concurrent.futures import ThreadPoolExecutor
    import threading

    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load(market, config.UNIVERSES[market][0])
    todo = [(i, it) for i, it in enumerate(PAIRS) if i >= start][:limit]
    print("BATCH", [t[1][0] for t in todo], "conc", conc, flush=True)
    lock = threading.Lock()

    def work(pair):
        i, it = pair
        r = _one(brain, fdb, market, i, it)
        with lock:
            if r["status"] in ("gate_fail", "sim_error"):
                print(f"[{r['name']}] {r['status']} {r['detail']}", flush=True)
            else:
                m = r.get("metrics") or {}
                print(f"[{r['name']}] {r['alpha_id']} {r['status']} "
                      f"S={m.get('S')} F={m.get('F')} TO={m.get('TO')} "
                      f"{','.join(r.get('fails') or [])}", flush=True)
        return r

    with ThreadPoolExecutor(max_workers=conc) as ex:
        results = list(ex.map(work, todo))
    ok = [r for r in results if r["status"] == "PASS_READY"]
    print("DONE total=", len(results), "pass=", len(ok))
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=8)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--market", default="GLB")
    ap.add_argument("--conc", type=int, default=2)
    a = ap.parse_args()
    raise SystemExit(main(market=a.market, limit=a.limit, start=a.start, conc=a.conc))