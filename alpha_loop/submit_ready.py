from __future__ import annotations

import argparse
import json
from datetime import date

from . import config, judge, ledger, submit
from .auth import Brain


def today_submitted(brain, east_date=None) -> int:
    east_date = east_date or config.today_east()
    d = brain.get_json("/users/self/alphas", params={"limit": 100, "offset": 0}) or {}
    n = 0
    for rec in d.get("results") or []:
        ds = rec.get("dateSubmitted")
        if ds and str(ds).startswith(str(east_date)):
            n += 1
    return n


def recent(brain, limit: int = 10) -> list[dict]:
    d = brain.get_json("/users/self/alphas", params={"limit": limit, "offset": 0}) or {}
    return d.get("results") or []


def main(limit: int = 6, apply: bool = False) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    used_today = today_submitted(brain)
    room = config.DAILY_REGULAR_QUOTA - used_today
    print(f"QUOTA east={config.today_east()} used={used_today} room={room} "
          f"window_open={submit.clock_gate()}", flush=True)
    candidates = []
    for rec in recent(brain, limit):
        region = (rec.get("settings") or {}).get("region")
        v = judge.verdict(rec, region or "GLB")
        print(f"  {rec.get('id')} {region} {judge.summarize(v)}", flush=True)
        if v["status"] == "PASS_READY" and not rec.get("dateSubmitted"):
            candidates.append(rec)
    print("PASS_CANDIDATES", len(candidates), flush=True)
    if not apply or not submit.clock_gate():
        print("DRY_RUN or window closed")
        return 0
    for rec in candidates[:max(0, room)]:
        aid = rec["id"]
        ok, pre = submit.precheck(brain, aid)
        print("  precheck", aid, ok, pre, flush=True)
        if not ok:
            continue
        res = submit.submit(brain, aid)
        print("  submit", aid, res.get("result"), res.get("fails") or res.get("remainingAttempts"),
              flush=True)
        if res.get("result") == "REJECTED":
            continue
        if submit.confirm(brain, aid):
            alpha = brain.get_json(f"/alphas/{aid}") or {}
            is_ = alpha.get("is") or {}
            ledger.append({
                "id": aid, "expr": (alpha.get("regular") or {}).get("code"),
                "S": is_.get("sharpe"), "F": is_.get("fitness"), "T": is_.get("turnover"),
                "R": is_.get("returns"), "DD": is_.get("drawdown"),
                "dateSubmitted": alpha.get("dateSubmitted"),
                "region": (alpha.get("settings") or {}).get("region"),
                "universe": (alpha.get("settings") or {}).get("universe"),
                "neutralization": (alpha.get("settings") or {}).get("neutralization"),
            })
            print("  ACCEPTED", aid, flush=True)
        else:
            print("  NOT_CONFIRMED", aid, flush=True)
    print("LEDGER_TOTAL", len(ledger.rows()))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    raise SystemExit(main(limit=a.limit, apply=a.apply))