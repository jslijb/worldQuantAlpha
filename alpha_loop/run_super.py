from __future__ import annotations

import argparse
import json
import sys
import time

from . import config
from .auth import Brain

COMBO_DESC = (
    "Equal-weight blend of the ten production alphas that the platform ranks as least "
    "self-correlated against our current submitted pool, so that the assembled super alpha "
    "adds genuinely orthogonal information instead of re-expressing crowded existing streams."
)

SEL_DESC = (
    "Selection expression {sel} ranks every eligible production alpha by one minus its "
    "self-correlation against the current submitted pool, then keeps the {limit} least-"
    "correlated components under positive handling, minimising overlap with crowded existing "
    "alpha streams and maximising the incremental information this super alpha contributes."
)


def build(sel: str, decay: int, region: str, universe: str, trunc: float, limit: int,
          neut: str = "SUBINDUSTRY", combo: str = "1") -> dict:
    return {
        "type": "SUPER",
        "settings": {
            "instrumentType": "EQUITY", "region": region, "universe": universe,
            "delay": 1, "decay": decay, "neutralization": neut, "truncation": trunc,
            "pasteurization": "ON", "unitHandling": "VERIFY",
            "nanHandling": "OFF", "language": "FASTEXPR", "visualization": False,
            "testPeriod": "P0Y0M", "selectionHandling": "POSITIVE",
            "selectionLimit": limit,
        },
        "combo": combo,
        "selection": sel,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="USA")
    ap.add_argument("--universe", default="TOP3000")
    ap.add_argument("--decay", type=int, default=32)
    ap.add_argument("--trunc", type=float, default=0.08)
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--sel", default="(1-self_correlation)")
    ap.add_argument("--neut", default="SUBINDUSTRY")
    ap.add_argument("--combo", default="1")
    args = ap.parse_args()

    body = build(args.sel, args.decay, args.region, args.universe, args.trunc, args.limit, args.neut, args.combo)
    b = Brain()
    b.login()
    if not b.authenticated:
        print("LOGIN_FAIL")
        return 2

    print("POST /simulations", json.dumps(body, ensure_ascii=False), flush=True)
    r = b.post("/simulations", json=body)
    print("HTTP", r.status_code, (r.text or "")[:300], flush=True)
    if r.status_code in (400, 403):
        return 3

    loc = r.headers.get("Location")
    if not loc:
        print("NO_LOCATION")
        return 4

    aid = None
    for i in range(90):
        time.sleep(10)
        rr = b.get(loc)
        d = rr.json() if rr.text else {}
        if rr.status_code != 200:
            print(f"poll{i} http={rr.status_code} {(rr.text or '')[:150]}", flush=True)
            continue
        if d.get("status") == "ERROR":
            print("SIM_ERROR", json.dumps(d, ensure_ascii=False)[:400], flush=True)
            return 5
        if d.get("alpha"):
            aid = d["alpha"]
            print("SIM_DONE alpha=", aid, flush=True)
            break
        print(f"poll{i} status={d.get('status')} {(rr.text or '')[:100]}", flush=True)
    if not aid:
        print("SIM_TIMEOUT")
        return 6

    time.sleep(5)
    j = b.get_json("/alphas/" + aid) or {}
    isd = j.get("is") or {}
    print("type=", j.get("type"), "status=", j.get("status"),
          "S=", isd.get("sharpe"), "F=", isd.get("fitness"), "TO=", isd.get("turnover"),
          flush=True)

    pr = b.patch("/alphas/" + aid, json={
        "combo": {"code": args.combo, "description": COMBO_DESC},
        "selection": {"code": args.sel,
                      "description": SEL_DESC.format(sel=args.sel, limit=args.limit)},
    })
    print("PATCH", pr.status_code, (pr.text or "")[:300], flush=True)
    if pr.status_code not in (200, 201):
        return 7

    sr = b.post(f"/alphas/{aid}/submit")
    print("POST submit", sr.status_code, (sr.text or "")[:300], flush=True)
    if sr.status_code == 403:
        d = sr.json()
        (config.VERDICT_DIR / f"{aid}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        fails = [(c.get("name"), c.get("value")) for c in (d.get("is") or {}).get("checks", [])
                 if c.get("result") == "FAIL"]
        print("REJECTED fails=", fails, flush=True)
        return 8

    for i in range(80):
        time.sleep(20)
        aj = b.get_json("/alphas/" + aid) or {}
        if aj.get("dateSubmitted") or aj.get("status") == "ACTIVE":
            i2 = aj.get("is") or {}
            print("★ ACTIVE", aid, aj.get("dateSubmitted"),
                  "S=", i2.get("sharpe"), "F=", i2.get("fitness"), "TO=", i2.get("turnover"),
                  flush=True)
            return 0
        ck = {c.get("name"): (c.get("result"), c.get("value"))
              for c in ((aj.get("is") or {}).get("checks") or [])}
        sf = ck.get("SELF_CORRELATION"); pf = ck.get("PROD_CORRELATION")
        if (sf and sf[0] == "FAIL") or (pf and pf[0] == "FAIL"):
            print("✘ FAIL SELF=", sf, "PROD=", pf, flush=True)
            return 9
        print(f"poll{i} status={aj.get('status')} SELF={sf} PROD={pf}", flush=True)
    print("SUBMIT_TIMEOUT", aid)
    return 10


if __name__ == "__main__":
    sys.exit(main())