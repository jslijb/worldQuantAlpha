from __future__ import annotations

from .. import config


def dataset_pass(dataset_id: str, region: str, used_datasets: set[str]) -> tuple[bool, dict]:
    if config.is_banned_dataset(dataset_id, region):
        return False, {"reason": "BANNED_DATASET_CROWDED", "dataset": dataset_id}
    if region == "USA" and config.USA_UNUSED_DATASET_ONLY and dataset_id in used_datasets:
        return False, {"reason": "USA_DATASET_ALREADY_USED", "dataset": dataset_id}
    return True, {"reason": "OK", "dataset": dataset_id}
