from __future__ import annotations

import json
import sys
import time

from . import config
from .auth import Brain

API = "https://api.worldquantbrain.com"

COMBO_DESC = (
    "Equal-weight blend of the ten production alphas that the platform ranks as least "
    "self-correlated against our current submitted pool, so that the assembled super alpha "
    "adds genuinely orthogonal information instead of re-expressing crowded existing streams."
)

SEL_DESC = (
    "Selection expression {sel} ranks every eligible production alpha by one minus its "
    "self-correlation against the current submitted pool, then keeps the ten least-correlated "
    "components under positive handling, minimising overlap with crowded existing alpha "
    "streams and maximising the incremental information this super alpha contributes."
)


def build(sel: str, decay: int, region: str, universe: str, trunc: float, limit: int) -> dict:
    return {
        "type": "SUPER",
        "settings": {
            "instrumentType": "EQUITY", "region": region, "universe": universe,
            "delay": 1, "decay": decay, "neutralization": "SUBINDUSTRY",
            "truncation": trunc, "pasteurization": "ON", "unitHandling": "VERIFY",
            "nanHandling": "OFF", "language": "FASTEXPR", "visualization": False,
            "testPeriod": "P0Y0M", "selectionHandling": "POSITIVE",
            "selectionLimit": limit,
        },
        "combo": "1",
        "selection": sel,
    }


def main() -> int:
    sel = '(1-self_correlation)*in(datasets,"fundamental23")'
    body = build(sel, decay=25, region="EUR", universe="TOP2500", trunc=0.08, limit=10)
    b = Brain()
    b.login()
    if not b.authenticated:
        print("LOGIN_FAIL")
        return 2

    print("POST /simulations", json.dumps(body, ensure_ascii=False)[:400], flush=True)
    r = b.post("/simulations", json=body)
    print("HTTP", r.status_code, (r.text or "")[:400], flush=True)
    if r.status_code in (400, 403):
        return 3

    loc = r.headers.get("Location")
    if not loc:
        print("NO_LOCATION")
        return 4

    aid = None
    for i in range(60):
        time.sleep(10)
        rr = b.get(loc)
        if rr.status_code != 200:
            print(f"poll{i} http={rr.status_code} {(rr.text or '')[:120]}", flush=True)
            continue
        progress = rr.headers.get("Retry-After")
        d = rr.json() if rr.text else {}
        if d.get("id") or d.get("alpha"):
            aid = d.get("id") or d.get("alpha")
            print("SIM_DONE alpha=", aid, flush=True)
            break
        print(f"poll{i} progress={progress} {(rr.text or '')[:120]}", flush=True)
    if not aid:
        print("SIM_TIMEOUT")
        return 5

    print("GET /alphas/" + aid, flush=True)
    j = b.get_json("/alphas/" + aid) or {}
    print("type=", j.get("type"), "S=", (j.get("is") or {}).get("sharpe"),
          "F=", (j.get("is") or {}).get("fitness"), flush=True)

    pr = b.patch("/alphas/" + aid, json={
        "combo": {"code": "1", "description": COMBO_DESC},
        "selection": {"code": sel, "description": SEL_DESC.format(sel=sel)},
    })
    print("PATCH", pr.status_code, (pr.text or "")[:200], flush=True)
    if pr.status_code not in (200, 201):
        return 6

    sr = b.post(f"/alphas/{aid}/submit")
    print("POST submit", sr.status_code, (sr.text or "")[:300], flush=True)
    if sr.status_code == 403:
        d = sr.json()
        fails = [c.get("name") for c in (d.get("is") or {}).get("checks", [])
                 if c.get("result") == "FAIL"]
        (config.VERDICT_DIR / f"{aid}.json").write_text(
            json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
        print("REJECTED fails=", fails, flush=True)
        return 7

    for i in range(60):
        time.sleep(15)
        aj = b.get_json("/alphas/" + aid) or {}
        if aj.get("dateSubmitted") or aj.get("status") == "ACTIVE":
            print("★ ACTIVE", aid, aj.get("dateSubmitted"),
                  (aj.get("is") or {}).get("sharpe"),
                  (aj.get("is") or {}).get("fitness"), flush=True)
            return 0
        ck = {c.get("name"): c.get("result")
              for c in ((aj.get("is") or {}).get("checks") or [])}
        if "FAIL" in (ck.get("SELF_CORRELATION"), ck.get("PROD_CORRELATION")):
            print("✘ FAIL", ck, flush=True)
            return 8
        print(f"poll{i} status={aj.get('status')} SELF={ck.get('SELF_CORRELATION')} "
              f"PROD={ck.get('PROD_CORRELATION')}", flush=True)
    print("SUBMIT_TIMEOUT", aid)
    return 9


if __name__ == "__main__":
    sys.exit(main())