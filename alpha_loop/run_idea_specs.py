from __future__ import annotations

import csv
import io
import time

from . import composer, config, gates, idea_spec, judge, submit
from .auth import Brain
from .fielddb import FieldDB
from .sim import run

LEDGER = config.ROOT / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
SPECS = config.PKG_DIR / "specs" / "ideas.jsonl"


def append(row: list) -> None:
    with io.open(LEDGER, "a", encoding="utf-8-sig", newline="") as f:
        csv.writer(f).writerow(row + [time.strftime("%Y-%m-%d %H:%M:%S")])


def main(only: str | None = None, skip: set[str] | None = None) -> int:
    items = idea_spec.load(SPECS)
    skip = skip or set()
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    for idx, spec in enumerate(items, 1):
        if only and spec["id"] != only:
            continue
        if spec["id"] in skip:
            continue
        st = spec["settings"]
        region, uni = st["region"], st["universe"]
        fdb.load(region, uni)
        expr = spec["expr"]
        print(f"\n[{idx}/{len(items)}] {spec['id']}  ds={spec['dataset']}", flush=True)
        print(f"  mechanism: {spec['mechanism']}", flush=True)
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        ok_a, d_a = gates.atom.atom_pass(expr, region, fdb)
        ok_s, d_s = gates.dataset.dataset_pass(spec["dataset"], region, set())
        if not (ok_o and ok_d and ok_a and ok_s):
            print("  SKIP", d_d.get("reason"), d_a.get("reason"), d_s.get("reason"), flush=True)
            append([spec["id"], spec["mechanism"], spec["falsify"], idx, spec["id"], "-", expr,
                    spec["dataset"], region, uni, st.get("neutralization"), st.get("decay"),
                    "", "", "", "GATE_FAIL", str(d_d.get("reason") or d_a.get("reason")), "", "换 spec"])
            continue
        settings = composer.choose_settings(region, uni, idx)
        settings.update({"neutralization": st["neutralization"], "decay": st["decay"],
                         "truncation": st["truncation"]})
        unit = {"unit_id": spec["id"], "idea_id": spec["id"], "region": region, "shape": "spec",
                "params": {"neut": st["neutralization"], "decay": st["decay"]}, "expr": expr,
                "dataset": d_a["datasets"][0], "fields": d_a["fields"], "settings": settings}
        res = None
        for attempt in range(5):
            res = run(brain, unit)
            if res.get("status") == "done":
                break
            print(f"  TRY{attempt+1} {res.get('status')} {res.get('http')} {str(res.get('body'))[:80]}", flush=True)
            if str(res.get("http")) == "401":
                brain.relogin()
            time.sleep(20)
        if not res or res.get("status") != "done":
            append([spec["id"], spec["mechanism"], spec["falsify"], idx, spec["id"], "-", expr,
                    spec["dataset"], region, uni, st.get("neutralization"), st.get("decay"),
                    "", "", "", "SIM_ERROR", str(res.get("body") if res else "")[:80], "", "换 spec"])
            continue
        v = judge.verdict(res.get("alpha") or {}, region)
        m = v.get("metrics") or {}
        print(f"  {res['alpha_id']} S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {v.get('fail_codes')}", flush=True)
        append([spec["id"], spec["mechanism"], spec["falsify"], idx, spec["id"], res["alpha_id"], expr,
                spec["dataset"], region, uni, st.get("neutralization"), st.get("decay"),
                m.get("S"), m.get("F"), m.get("TO"), v.get("status"),
                ",".join(v.get("fail_codes") or []), "", "合格即提交" if v["status"] == "PASS_READY" else "按 falsify 判定"])
        if v["status"] == "PASS_READY":
            r = brain.post(f"/alphas/{res['alpha_id']}/submit")
            loc = r.headers.get("Location")
            body = {}
            if r.status_code == 403:
                body = r.json()
            elif loc:
                for _ in range(10):
                    rr = brain.get(loc)
                    if (rr.text or "").strip():
                        try:
                            body = rr.json()
                        except Exception:
                            body = {}
                        break
                    time.sleep(15)
            fails = [c.get("name") for c in body.get("is", {}).get("checks") or [] if str(c.get("result")).upper() == "FAIL"]
            print(f"  SUBMIT {r.status_code} fails={fails}", flush=True)
        time.sleep(2)
    print("\nSPEC_RUN_DONE", flush=True)
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=None)
    a = ap.parse_args()
    raise SystemExit(main(only=a.only, skip={a.only} if a.only == "v_multi_ifelse" else {"v_multi_ifelse"}))