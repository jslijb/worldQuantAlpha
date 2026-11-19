from __future__ import annotations

import json

from . import config


def clock_gate(now=None) -> bool:
    now = now or config.now_bj()
    return now.hour >= config.SUBMIT_HOUR_BJ


def _corr_max(brain, alpha_id: str, kind: str) -> float | None:
    for _ in range(3):
        body = brain.get_json(f"/alphas/{alpha_id}/correlations/{kind}")
        if isinstance(body, dict):
            mx = body.get("max")
            if mx is not None:
                return float(mx)
        body2 = brain.get_json(f"/alphas/{alpha_id}/check")
        if isinstance(body2, dict):
            for chk in body2.get("checks") or []:
                name = str(chk.get("name", ""))
                if kind.upper() in name and chk.get("value") is not None:
                    return float(chk["value"])
    return None


def precheck(brain, alpha_id: str) -> tuple[bool, dict]:
    prod = _corr_max(brain, alpha_id, "prod")
    selfc = _corr_max(brain, alpha_id, "self")
    detail = {"prod": prod, "self": selfc}
    if prod is None or selfc is None:
        detail["reason"] = "CHECK_UNAVAILABLE"
        return False, detail
    if prod > config.PRECHECK_MAX or selfc > config.PRECHECK_MAX:
        detail["reason"] = "CORR_TOO_HIGH"
        return False, detail
    if prod >= config.PRECHECK_HARD_BAND or selfc >= config.PRECHECK_HARD_BAND:
        detail["reason"] = "CORR_HARD_BAND"
        return False, detail
    detail["reason"] = "OK"
    return True, detail


def submit(brain, alpha_id: str) -> dict:
    r = brain.post(f"/alphas/{alpha_id}/submit")
    if r.status_code == 403:
        try:
            body = r.json()
        except ValueError:
            body = {"_raw": (r.text or "")[:2000]}
        (config.VERDICT_DIR / f"{alpha_id}.json").write_text(
            json.dumps(body, ensure_ascii=False, indent=2), encoding="utf-8")
        checks = body.get("checks") or []
        fails = [c.get("name") for c in checks if str(c.get("result")).upper() == "FAIL"]
        return {"result": "REJECTED", "http": 403, "fails": fails, "body": body}
    if r.status_code not in (200, 201):
        return {"result": "ERROR", "http": r.status_code, "body": (r.text or "")[:1000]}
    loc = r.headers.get("Location")
    if loc:
        out = brain.poll(loc, timeout=300, interval=5)
    else:
        out = {}
    ra = out.get("remainingAttempts") if isinstance(out, dict) else None
    return {"result": "ACCEPTED_CANDIDATE", "http": r.status_code, "body": out,
            "remainingAttempts": ra}


def confirm(brain, alpha_id: str) -> bool:
    alpha = brain.get_json(f"/alphas/{alpha_id}")
    if not isinstance(alpha, dict):
        return False
    return alpha.get("status") == "ACTIVE" and bool(alpha.get("dateSubmitted"))