from __future__ import annotations

import json
from pathlib import Path

REQUIRED = ("id", "mechanism", "why_field", "why_layer", "falsify", "prediction", "expr", "dataset", "settings")


class SpecError(ValueError):
    pass


def load(path: str | Path) -> list[dict]:
    p = Path(path)
    out = []
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            raise SpecError(f"line {n}: invalid json ({exc})") from exc
        missing = [k for k in REQUIRED if not str(item.get(k, "")).strip()]
        if missing:
            raise SpecError(f"line {n} ({item.get('id', '?')}): missing {missing}")
        if str(item["falsify"]).strip() == str(item["mechanism"]).strip():
            raise SpecError(f"line {n} ({item['id']}): falsify must differ from mechanism")
        out.append(item)
    return out


def summarize(items: list[dict]) -> list[str]:
    return [f"{i['id']}: {i['mechanism']}" for i in items]