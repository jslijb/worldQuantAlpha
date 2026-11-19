from __future__ import annotations

from . import config


def _checks(alpha: dict) -> list[dict]:
    is_ = alpha.get("is") or {}
    checks = is_.get("checks") or alpha.get("checks") or []
    return checks if isinstance(checks, list) else []


def _metric(alpha: dict, key: str):
    is_ = alpha.get("is") or {}
    return is_.get(key)


def verdict(alpha: dict, region: str, extra: dict | None = None) -> dict:
    extra = extra or {}
    if not alpha or not isinstance(alpha, dict):
        return {"status": "FATAL", "fail_codes": ["METRIC_MISSING"], "detail": "no alpha json", **extra}
    checks = _checks(alpha)
    metrics = {
        "S": _metric(alpha, "sharpe"),
        "F": _metric(alpha, "fitness"),
        "TO": _metric(alpha, "turnover"),
        "R": _metric(alpha, "returns"),
        "DD": _metric(alpha, "drawdown"),
    }
    if metrics["S"] is None and not checks:
        return {"status": "FATAL", "fail_codes": ["METRIC_MISSING"], "metrics": metrics, **extra}
    fails = [c.get("name") for c in checks if str(c.get("result")).upper() == "FAIL"]
    detail = {c.get("name"): {"result": c.get("result"), "limit": c.get("limit"),
                              "value": c.get("value")} for c in checks}
    if metrics["S"] is not None and metrics["S"] < config.THRESHOLDS["sharpe"]:
        fails.append("LOW_SHARPE_LOCAL")
    if metrics["F"] is not None and metrics["F"] < config.THRESHOLDS["fitness"]:
        fails.append("LOW_FITNESS_LOCAL")
    if metrics["TO"] is not None and metrics["TO"] > config.THRESHOLDS["turnover_max"]:
        fails.append("HIGH_TURNOVER_LOCAL")
    fails = sorted(set(fails))
    status = "FAIL" if fails else "PASS_READY"
    return {"status": status, "fail_codes": fails, "metrics": metrics,
            "checks": detail, "alpha_id": alpha.get("id"),
            "settings": alpha.get("settings"), **extra}


def summarize(v: dict) -> str:
    m = v.get("metrics") or {}
    parts = [f"S={m.get('S')}", f"F={m.get('F')}", f"TO={m.get('TO')}"]
    if v.get("fail_codes"):
        parts.append("FAIL:" + ",".join(v["fail_codes"]))
    else:
        parts.append("PASS")
    return " ".join(parts)