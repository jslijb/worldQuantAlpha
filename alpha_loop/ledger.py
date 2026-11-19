from __future__ import annotations

import csv
import io
from pathlib import Path

from . import config

LEDGER = config.STATE_DIR / "ledger.csv"
COLUMNS = ["id", "expr", "S", "F", "T", "R", "DD", "selfCorr", "dateSubmitted",
           "decay", "region", "universe", "neutralization", "idea_id", "shape", "xop"]


def append(row: dict) -> None:
    new_file = not LEDGER.exists()
    with LEDGER.open("a", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLUMNS, extrasaction="ignore")
        if new_file:
            w.writeheader()
        w.writerow({c: row.get(c, "") for c in COLUMNS})


def rows() -> list[dict]:
    if not LEDGER.exists():
        return []
    with LEDGER.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def daily_count(east_date) -> dict:
    n_reg = 0
    for r in rows():
        if str(r.get("dateSubmitted", "")).startswith(str(east_date)):
            n_reg += 1
    return {"regular": n_reg, "total": len(rows())}


def used_alpha_ids() -> set[str]:
    return {r.get("id") for r in rows() if r.get("id")}