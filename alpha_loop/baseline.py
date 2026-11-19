from __future__ import annotations

import json
import time

from . import config

RAW = config.STATE_DIR / "alphas_raw.json"


def fetch_alphas(brain, ttl_hours: int | None = None, max_alphas: int = 1500) -> dict:
    ttl = config.BASELINE_TTL_HOURS if ttl_hours is None else ttl_hours
    if RAW.exists():
        try:
            data = json.loads(RAW.read_text(encoding="utf-8"))
            if (time.time() - data.get("fetched_at", 0)) / 3600 <= ttl:
                return data
        except Exception:
            pass
    records = []
    seen = 0
    offset = 0
    while seen < max_alphas:
        r = brain.get("/users/self/alphas", params={"limit": 100, "offset": offset})
        if r.status_code != 200:
            break
        body = r.json()
        recs = body.get("results") or []
        if not recs:
            break
        for rec in recs:
            seen += 1
            code = ((rec.get("regular") or {}).get("code") or "")
            region = (rec.get("settings") or {}).get("region")
            if not code or not region:
                continue
            records.append({
                "id": rec.get("id"), "region": region, "code": code,
                "dateSubmitted": rec.get("dateSubmitted"),
                "submitted": bool(rec.get("dateSubmitted")),
            })
        offset += len(recs)
        if offset >= (body.get("count") or 0):
            break
    data = {"fetched_at": time.time(), "alphas_seen": seen,
            "records": records, "complete": seen < max_alphas}
    RAW.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def parse_region(fdb, region: str, records: list[dict]) -> dict:
    used_fields: set[str] = set()
    used_datasets: set[str] = set()
    missing = 0
    parsed = 0
    for rec in records:
        if rec.get("region") != region or not rec.get("submitted"):
            continue
        parsed += 1
        for fid in fdb.business_fields(rec.get("code") or ""):
            ds = fdb.dataset_of(fid, region)
            if ds:
                used_fields.add(fid)
                used_datasets.add(ds)
            else:
                missing += 1
    return {"used_fields": used_fields, "used_datasets": used_datasets,
            "parsed": parsed, "unmapped_fields": missing}


def sets_of(parsed: dict) -> tuple[set[str], set[str]]:
    return parsed.get("used_fields", set()), parsed.get("used_datasets", set())