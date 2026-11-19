from __future__ import annotations


def atom_pass(expr: str, region: str, fdb) -> tuple[bool, dict]:
    fields = fdb.business_fields(expr)
    ds_of: dict[str, str] = {}
    unknown: list[str] = []
    for fid in fields:
        ds = fdb.dataset_of(fid, region)
        if ds:
            ds_of[fid] = ds
        else:
            unknown.append(fid)
    if unknown:
        return False, {"reason": "UNKNOWN_DATASET", "fields": fields, "unknown": unknown}
    datasets = sorted(set(ds_of.values()))
    if len(fields) <= 1:
        return True, {"reason": "OK", "fields": fields, "datasets": datasets, "atom": "SINGLE_FIELD"}
    if len(datasets) == 1:
        return True, {"reason": "OK", "fields": fields, "datasets": datasets, "atom": "SAME_DATASET"}
    return False, {"reason": "CROSS_DATASET", "fields": fields, "datasets": datasets,
                   "map": ds_of}