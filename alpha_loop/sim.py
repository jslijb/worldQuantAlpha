from __future__ import annotations

import json
import time

from . import config


class SimError(RuntimeError):
    pass


def run(brain, unit: dict, timeout: int | None = None) -> dict:
    payload = {"type": "REGULAR", "settings": unit["settings"], "regular": unit["expr"]}
    r = brain.post("/simulations", json=payload)
    if r.status_code not in (200, 201):
        return {"status": "error", "http": r.status_code, "body": (r.text or "")[:2000]}
    loc = r.headers.get("Location") or ""
    if not loc:
        return {"status": "error", "http": r.status_code, "body": "no Location header"}
    body = brain.poll(loc, timeout=timeout or config.SIM_TIMEOUT)
    if body.get("_timeout"):
        return {"status": "timeout", "location": loc}
    if body.get("_http_status"):
        return {"status": "error", "http": body["_http_status"], "body": body.get("_body")}
    alpha_id = body.get("alpha")
    if not alpha_id:
        return {"status": "error",
                "body": json.dumps(body, ensure_ascii=False)[:1500]}
    alpha = _wait_metrics(brain, alpha_id)
    out = {"status": "done", "alpha_id": alpha_id, "alpha": alpha, "location": loc,
           "unit": unit, "raw_poll": body}
    raw = config.RAW_DIR / f"{unit['unit_id']}.json"
    raw.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    return out


def _wait_metrics(brain, alpha_id: str, tries: int = 6) -> dict:
    for i in range(tries):
        alpha = brain.get_json(f"/alphas/{alpha_id}")
        if not isinstance(alpha, dict):
            alpha = {}
        is_ = alpha.get("is") or {}
        if is_.get("sharpe") is not None:
            return alpha
        time.sleep(3 if i else 1)
    return alpha if isinstance(alpha, dict) else {}