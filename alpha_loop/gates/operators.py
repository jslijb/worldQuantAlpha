from __future__ import annotations

import re

from .. import config

CALL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")


def banned_hits(expr: str, on_date=None) -> list[str]:
    names = {m.group(1).lower() for m in CALL_RE.finditer(expr)}
    names |= {t.lower() for t in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", expr)}
    hits = []
    for name, until in config.BANNED_OPERATORS.items():
        if name in names and config.is_operator_banned(name, on_date):
            hits.append(f"{name}->{until}")
    return hits


def check(expr: str, on_date=None) -> tuple[bool, dict]:
    hits = banned_hits(expr, on_date)
    if hits:
        return False, {"reason": "BANNED_OPERATOR", "hits": hits}

    return True, {"reason": "OK"}


def xop_of(expr: str) -> str:
    found = [m.group(1).lower() for m in CALL_RE.finditer(expr)
             if m.group(1).lower() in config.XOP_WHITELIST]
    return found[0] if found else ""