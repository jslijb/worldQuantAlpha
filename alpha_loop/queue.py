from __future__ import annotations

import json
import os
import time
from pathlib import Path

from . import config

PENDING = config.STATE_DIR / "pending.json"


def _load() -> dict:
    if PENDING.exists():
        try:
            return json.loads(PENDING.read_text(encoding="utf-8"))
        except Exception:
            return {"items": []}
    return {"items": []}


def _save(data: dict) -> None:
    tmp = PENDING.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, PENDING)


def enqueue(alpha_id: str, unit: dict, metrics: dict, day_target: str | None = None) -> dict:
    data = _load()
    if any(i["alpha_id"] == alpha_id for i in data["items"]):
        return {"status": "duplicate", "alpha_id": alpha_id}
    item = {
        "alpha_id": alpha_id, "unit_id": unit.get("unit_id"), "market": unit.get("region"),
        "S": metrics.get("S"), "F": metrics.get("F"), "TO": metrics.get("TO"),
        "day_target": day_target or str(config.today_bj()),
        "status": "ready", "enqueued_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    data["items"].append(item)
    _save(data)
    return item


def peek(day_target: str | None = None) -> list[dict]:
    items = [i for i in _load()["items"] if i.get("status") == "ready"]
    if day_target:
        items = [i for i in items if str(i.get("day_target")) <= day_target]
    return sorted(items, key=lambda i: -(i.get("S") or 0))


def mark(alpha_id: str, status: str, reason: str = "") -> None:
    data = _load()
    for i in data["items"]:
        if i["alpha_id"] == alpha_id:
            i["status"] = status
            if reason:
                i["reason"] = reason
            i["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save(data)


def pending_for(alpha_id: str) -> dict | None:
    return next((i for i in _load()["items"] if i["alpha_id"] == alpha_id), None)


def stats() -> dict:
    items = _load()["items"]
    out = {}
    for i in items:
        out[i.get("status", "unknown")] = out.get(i.get("status", "unknown"), 0) + 1
    return out