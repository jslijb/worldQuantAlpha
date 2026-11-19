from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import config

IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class FieldDB:
    def __init__(self):
        self._cache: dict[str, dict] = {}

    def path(self, region: str) -> Path:
        return config.FIELDB_DIR / f"{region}.json"

    def load(self, region: str, universe: str, brain=None, force: bool = False,
             max_pages: int = 400) -> int:
        p = self.path(region)
        if p.exists() and not force:
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if data.get("region") == region and data.get("fields"):
                    age_days = (time.time() - data.get("fetched_at", 0)) / 86400
                    if age_days <= config.FIELDB_TTL_DAYS:
                        self._cache[region] = data
                        return len(data["fields"])
            except Exception:
                pass
        if brain is None:
            if region in self._cache:
                return len(self._cache[region]["fields"])
            raise RuntimeError(f"fielddb {region} cache missing and no brain supplied")
        fields: dict[str, dict] = {}
        offset = 0
        page = 0
        while page < max_pages:
            params = {
                "instrumentType": "EQUITY", "region": region, "delay": config.DELAY,
                "universe": universe, "limit": 50, "offset": offset,
            }
            r = brain.get("/data-fields", params=params)
            if r.status_code != 200:
                break
            body = r.json()
            recs = body.get("results") or []
            for rec in recs:
                fid = rec.get("id")
                if not fid:
                    continue
                ds = rec.get("dataset") or {}
                ds_id = ds.get("id") if isinstance(ds, dict) else str(ds)
                fields[fid] = {
                    "id": fid,
                    "dataset": ds_id,
                    "dataset_name": ds.get("name") if isinstance(ds, dict) else None,
                    "type": rec.get("type"),
                    "coverage": rec.get("coverage"),
                    "userCount": rec.get("userCount"),
                    "alphaCount": rec.get("alphaCount"),
                    "description": rec.get("description") or "",
                }
            total = body.get("count") or 0
            offset += len(recs)
            page += 1
            if not recs or offset >= total:
                break
        data = {"region": region, "universe": universe, "fetched_at": time.time(),
                "fields": fields}
        p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        self._cache[region] = data
        return len(fields)

    def _region_data(self, region: str) -> dict:
        if region not in self._cache:
            p = self.path(region)
            if not p.exists():
                return {"fields": {}}
            data = json.loads(p.read_text(encoding="utf-8"))
            if data.get("region") != region:
                raise RuntimeError(f"region mismatch in cache for {region}")
            self._cache[region] = data
        return self._cache[region]

    def dataset_of(self, field_id: str, region: str) -> str | None:
        rec = self._region_data(region)["fields"].get(field_id)
        return (rec or {}).get("dataset")

    def meta(self, field_id: str, region: str) -> dict | None:
        return self._region_data(region)["fields"].get(field_id)

    def fields_of(self, dataset_id: str, region: str) -> list[dict]:
        return [v for v in self._region_data(region)["fields"].values()
                if v.get("dataset") == dataset_id]

    def dataset_universe(self, region: str) -> dict[str, list[dict]]:
        out: dict[str, list[dict]] = {}
        for rec in self._region_data(region)["fields"].values():
            ds = rec.get("dataset")
            if ds:
                out.setdefault(ds, []).append(rec)
        return out

    @staticmethod
    def business_fields(expr: str) -> list[str]:
        assigned = {m.group(1).lower()
                    for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*=", expr)}
        called = {m.group(1).lower()
                  for m in re.finditer(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(", expr)}
        cleaned = re.sub(r'"[^"]*"', " ", expr)
        cleaned = re.sub(r"'[^']*'", " ", cleaned)
        cleaned = re.sub(r"[A-Za-z_][A-Za-z0-9_]*\s*=", " ", cleaned)
        uniq: list[str] = []
        for tok in IDENT_RE.findall(cleaned):
            low = tok.lower()
            if low in config.OPERATORS or low in config.GROUP_FIELDS or low in called:
                continue
            if low in config.NAMED_PARAMS or low in assigned:
                continue
            if tok not in uniq:
                uniq.append(tok)
        return uniq

    def match_roles(self, region: str, roles: list[dict], used_fields: set[str],
                    forbid_datasets: set[str] | None = None,
                    limit: int = 8) -> list[dict]:
        forbid_datasets = forbid_datasets or set()
        by_ds = self.dataset_universe(region)
        scored = []
        for ds_id, fields in by_ds.items():
            if ds_id in forbid_datasets:
                continue
            usable = [f for f in fields if f["id"] not in used_fields]
            if len(usable) < len(roles):
                continue
            matched, score = [], 0.0
            for role in roles:
                best, best_s = None, -1.0
                for f in usable:
                    if f in matched:
                        continue
                    s = self._score_role(role, f)
                    if s > best_s:
                        best, best_s = f, s
                if best is None:
                    break
                matched.append(best)
                score += best_s
            if len(matched) != len(roles):
                continue
            ds_use = max((f.get("alphaCount") or 0) for f in fields)
            score -= ds_use / 1e6
            scored.append({"dataset": ds_id, "fields": matched, "score": score})
        scored.sort(key=lambda x: -x["score"])
        return scored[:limit]

    @staticmethod
    def _score_role(role: dict, field: dict) -> float:
        if (field.get("type") or "").upper() != "MATRIX":
            return -1.0
        text = f"{field.get('id', '')} {field.get('description') or ''}".lower()
        key = (role.get("semantic") or "").lower()
        words = {w for w in re.findall(r"[a-z]+", key) if len(w) > 2}
        for syn in config.ROLE_SYNONYMS.get(role.get("type", ""), []):
            words.add(syn)
        words -= {"the", "and", "for", "with", "per", "from", "total", "value", "level"}
        hits = sum(1 for w in words if w in text)
        if hits == 0:
            return -1.0
        cov = field.get("coverage") or 0
        if cov < config.COV_MIN:
            return -1.0
        ac = field.get("alphaCount") or 0
        return hits * 2.0 + cov - min(ac, 5000) / 5000.0