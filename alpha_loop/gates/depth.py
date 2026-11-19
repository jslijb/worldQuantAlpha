from __future__ import annotations

import re

from .. import config

CALL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
REL_OPS = {"/", "*", "if_else", "ts_corr", "ts_regression", "bucket"}
NORM_OPS = {"group_zscore", "group_rank", "group_scale", "group_neutralize", "rank",
            "zscore", "normalize", "scale", "quantile", "winsorize"}


def _calls(expr: str) -> list[str]:
    return [m.group(1).lower() for m in CALL_RE.finditer(expr)]


def d1_relation(expr: str) -> tuple[bool, list[str]]:
    flat = re.sub(r"\s+", "", expr)
    hits = [op for op in REL_OPS if op in flat]
    if "/" in flat:
        hits.append("/")
    inner = re.sub(r"^[A-Za-z_][A-Za-z0-9_]*\((.*)\)$", r"\1", flat)
    if re.search(r"[A-Za-z_][A-Za-z0-9_]*\([^()]*\)[^()]*[-+][^()]*[A-Za-z_][A-Za-z0-9_]*\(", flat):
        hits.append("field_diff")
    if re.search(r"[A-Za-z_][A-Za-z0-9_]*[-+][A-Za-z_][A-Za-z0-9_]*(?!\()", inner):
        hits.append("field_diff")
    return (len(hits) > 0, sorted(set(hits)))


def d2_layers(expr: str) -> tuple[bool, int]:
    stack, depth, max_depth = 0, 0, 0
    for ch in expr:
        if ch == "(":
            stack += 1
            max_depth = max(max_depth, stack)
        elif ch == ")":
            stack -= 1
    ops = _calls(expr)
    transform_ops = [o for o in ops
                     if o.startswith("ts_") or o in NORM_OPS or o in ("hump", "if_else", "bucket")]
    relation = d1_relation(expr)[0]
    enough = len(transform_ops) >= 2 or (relation and len(transform_ops) >= 1)
    return (enough, len(transform_ops))


def d3_independent_norm_sum(expr: str) -> tuple[bool, list[str]]:
    flat = re.sub(r"\s+", "", expr)
    hits = []
    pattern = re.compile(
        r"(" + "|".join(sorted(NORM_OPS)) + r")\([^()]*\)[^()]{0,20}[+\-]"
        r"[^()]{0,20}(" + "|".join(sorted(NORM_OPS)) + r")\(")
    for m in pattern.finditer(flat):
        hits.append(f"{m.group(1)}+{m.group(2)}")
    return (len(hits) > 0, hits)


def check(expr: str) -> tuple[bool, dict]:
    ok1, r1 = d1_relation(expr)
    ok2, layers = d2_layers(expr)
    bad3, r3 = d3_independent_norm_sum(expr)
    detail = {"D1": ok1, "D1_hits": r1, "D2_layers": layers, "D3_bad": bad3, "D3_hits": r3}
    if bad3:
        detail["reason"] = "INDEPENDENT_NORM_SUM"
        return False, detail
    if not ok1:
        detail["reason"] = "NO_FIELD_RELATION"
        return False, detail
    if not ok2:
        detail["reason"] = "NOT_ENOUGH_LAYERS"
        return False, detail
    detail["reason"] = "OK"
    return True, detail