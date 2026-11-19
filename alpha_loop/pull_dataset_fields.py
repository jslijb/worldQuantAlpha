from __future__ import annotations

import argparse
import json
import sys
import time

from . import config
from .auth import Brain


def fetch_dataset(brain: Brain, region: str, universe: str, dataset: str) -> dict:
    out: dict[str, dict] = {}
    offset = 0
    while True:
        params = {"instrumentType": "EQUITY", "region": region, "delay": config.DELAY,
                  "universe": universe, "dataset.id": dataset,
                  "limit": 50, "offset": offset}
        r = brain.get("/data-fields", params=params)
        if r.status_code != 200:
            print(f"  {dataset} http={r.status_code} {(r.text or '')[:80]}", flush=True)
            break
        body = r.json()
        recs = body.get("results") or []
        for rec in recs:
            fid = rec.get("id")
            if not fid:
                continue
            ds = rec.get("dataset") or {}
            out[fid] = {
                "id": fid,
                "dataset": ds.get("id") if isinstance(ds, dict) else str(ds),
                "dataset_name": ds.get("name") if isinstance(ds, dict) else None,
                "type": rec.get("type"),
                "coverage": rec.get("coverage"),
                "userCount": rec.get("userCount"),
                "alphaCount": rec.get("alphaCount"),
                "description": rec.get("description") or "",
            }
        total = body.get("count") or 0
        offset += len(recs)
        if not recs or offset >= total:
            break
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--dataset", action="append", required=True)
    args = ap.parse_args()

    path = config.FIELDB_DIR / f"{args.region}.json"
    data = {"region": args.region, "universe": args.universe, "fetched_at": time.time(),
            "fields": {}}
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("region") != args.region:
            print("REGION_MISMATCH")
            return 2

    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 3

    for ds in args.dataset:
        got = fetch_dataset(brain, args.region, args.universe, ds)
        data["fields"].update(got)
        print(f"{ds}: +{len(got)}", flush=True)

    data["fetched_at"] = time.time()
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print("TOTAL", len(data["fields"]), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())