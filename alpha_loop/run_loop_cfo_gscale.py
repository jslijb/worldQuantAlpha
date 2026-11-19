from __future__ import annotations

import csv
import io
import json
import time

from . import composer, config, gates, judge
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
MECH = "group_scale 外壳被证明能把五腿件 PROD 压过线；把同一外壳套到 S 强但 PROD 死的 CFO 比值族，验证是否普适"

CANDIDATES = [
    ("cfo_ev_gscale",
     "经营现金流相对企业价值 = 用真实现金买入未来现金流的便宜程度；企业价值含债务，比市值更贴近整体资本成本",
     "group_scale(cashflow_op / enterprise_value, subindustry)"),
    ("cfo_assets_gscale",
     "经营现金流相对总资产 = 资产产生现金的效率，剥离规模与行业差异后看谁把资产变成现金",
     "group_scale(cashflow_op / assets, subindustry)"),
    ("cfo_ca_gscale",
     "经营现金流相对流动资产 = 短期资产回收现金的速度，对营运资本管理质量最敏感",
     "group_scale(cashflow_op / accounts_total_current_assets, subindustry)"),
    ("cfo_ev_delta_gscale",
     "两年累计经营现金流相对企业价值 = 用跨年累积而不是单年数字，剔除单季经营波动",
     "group_scale((cashflow_op + ts_delta(cashflow_op, 252)) / enterprise_value, subindustry)"),
]


def append(row: list) -> None:
    with io.open(LEDGER, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row + [time.strftime("%Y-%m-%d %H:%M:%S")])


def submit_and_judge(brain, alpha_id: str) -> list:
    r = brain.post(f"/alphas/{alpha_id}/submit")
    if r.status_code == 403:
        body = r.json() if r.text else {}
        fails = [c.get("name") for c in body.get("checks") or []
                 if str(c.get("result")).upper() == "FAIL"]
        (config.VERDICT_DIR / f"{alpha_id}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        return fails or ["403_NO_CHECKS"]
    if r.status_code not in (200, 201):
        return [f"HTTP_{r.status_code}"]
    loc = r.headers.get("Location")
    if not loc:
        return ["PENDING_NO_LOCATION"]
    out = brain.poll(loc, timeout=900, interval=10)
    body = out if isinstance(out, dict) else {}
    fails = [c.get("name") for c in body.get("checks") or []
             if str(c.get("result")).upper() == "FAIL"]
    if fails or body:
        (config.VERDICT_DIR / f"{alpha_id}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
    return fails or ["PENDING_NO_CHECKS"]


def main() -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load("EUR", "TOP2500")
    for idx, (tag, mech, expr) in enumerate(CANDIDATES, 1):
        print(f"\n[{idx}/{len(CANDIDATES)}] {tag}", flush=True)
        print(f"  {mech}", flush=True)
        ok_o, d_o = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, "EUR", fdb)
        ds = (d_a.get("datasets") or ["fundamental23"])[0]
        ok_s, d_s = gates.dataset.dataset_pass(ds, "EUR", set())
        print(f"  gates op={ok_o} depth={ok_d} atom={ok_a} ds={ds}", flush=True)
        if not (ok_o and ok_d and ok_a and ok_s):
            append([tag, mech, MECH, idx, tag, "-", expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                    0, "", "", "", "GATE_FAIL",
                    str(d_d.get("reason") or d_a.get("reason") or d_o.get("reason")), "", "换下一条"])
            continue
        settings = composer.choose_settings("EUR", "TOP2500", idx)
        settings["neutralization"] = "SUBINDUSTRY"
        settings["decay"] = 0
        settings["truncation"] = 0.05
        unit = {"unit_id": tag, "idea_id": "cfo_gscale", "region": "EUR", "shape": "custom",
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
        fails = submit_and_judge(brain, res["alpha_id"]) if v["status"] == "PASS_READY" else []
        if fails:
            print(f"  submit_fails={fails}", flush=True)
        append([tag, mech, MECH, idx, tag, res["alpha_id"], expr, ds, "EUR", "TOP2500", "SUBINDUSTRY",
                0, m.get("S"), m.get("F"), m.get("TO"),
                "SUBMITTED" if v["status"] == "PASS_READY" and not fails else v.get("status"),
                ",".join(v.get("fail_codes") or []), ",".join(fails), "看 falsify"])
        time.sleep(2)
    print("\nCFO_GSCALE_DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())