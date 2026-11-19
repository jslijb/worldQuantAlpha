from __future__ import annotations

import math

from .. import config
from .operators import xop_of


def _entropy(counts: list[int]) -> float:
    total = sum(counts)
    if total <= 0:
        return 0.0
    h = -sum((c / total) * math.log(c / total) for c in counts if c > 0)
    return h / math.log(len(counts)) if len(counts) > 1 else 0.0


def check(batch: list[dict], used_fields: set[str]) -> tuple[bool, dict]:
    detail = {}
    if not batch:
        return False, {"reason": "EMPTY_BATCH"}

    over = [u["unit_id"] for u in batch if len(u.get("fields") or []) > config.MAX_FIELDS_PER_ALPHA]
    if over:
        return False, {"reason": "V1_TOO_MANY_FIELDS", "units": over}

    new_fields = {f for u in batch for f in (u.get("fields") or []) if f not in used_fields}
    detail["new_fields"] = sorted(new_fields)
    if len(new_fields) < config.MIN_NEW_FIELDS_PER_BATCH:
        return False, {"reason": "V2_NOT_ENOUGH_NEW_FIELDS", **detail}

    ds_counts = {}
    for u in batch:
        ds_counts[u.get("dataset")] = ds_counts.get(u.get("dataset"), 0) + 1
    ent = _entropy(list(ds_counts.values()))
    detail["dataset_entropy"] = round(ent, 4)
    if ent < config.MIN_DATASET_ENTROPY:
        return False, {"reason": "V3_DATASET_TOO_CONCENTRATED", **detail}

    idea_counts = {}
    for u in batch:
        idea_counts[u.get("idea_id")] = idea_counts.get(u.get("idea_id"), 0) + 1
    top_idea, top_n = max(idea_counts.items(), key=lambda kv: kv[1])
    share = top_n / len(batch)
    detail["top_idea_share"] = round(share, 4)
    if len(batch) >= 4 and share > config.MAX_IDEA_SHARE:
        return False, {"reason": "V4_IDEA_TOO_CONCENTRATED", "idea": top_idea, **detail}

    xop_counts = {}
    for u in batch:
        x = xop_of(u.get("expr", "")) or "none"
        xop_counts[x] = xop_counts.get(x, 0) + 1
    top_xop, top_xn = max(xop_counts.items(), key=lambda kv: kv[1])
    xshare = top_xn / len(batch)
    detail["top_xop"] = top_xop
    detail["top_xop_share"] = round(xshare, 4)
    if xshare > config.XOP_MAX_SHARE:
        return False, {"reason": "V5_XOP_TOO_CONCENTRATED", **detail}

    detail["reason"] = "OK"
    return True, detail