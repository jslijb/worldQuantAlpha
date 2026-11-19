from __future__ import annotations

import json

import pytest

from alpha_loop import idea_spec


def _write(tmp_path, rows):
    p = tmp_path / "ideas.jsonl"
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    return p


def _full(**over):
    base = {
        "id": "t1", "mechanism": "营收上调且利润上调才可信",
        "why_field": "同数据集同14天口径的家数统计",
        "why_layer": "净修正比例可比，条件过滤体现先验证再采信",
        "falsify": "若一致性高组跑输则机制不成立",
        "prediction": {"S": [0.2, 0.6], "TO": [0.05, 0.2], "sign": "+"},
        "expr": "group_zscore(x, subindustry)", "dataset": "fundamental23",
        "settings": {"region": "EUR", "universe": "TOP2500"},
    }
    base.update(over)
    return base


def test_load_ok(tmp_path):
    p = _write(tmp_path, [_full()])
    items = idea_spec.load(p)
    assert len(items) == 1 and items[0]["id"] == "t1"


def test_missing_field_rejected(tmp_path):
    row = _full()
    row.pop("why_field")
    p = _write(tmp_path, [row])
    with pytest.raises(idea_spec.SpecError) as exc:
        idea_spec.load(p)
    assert "why_field" in str(exc.value)


def test_blank_value_rejected(tmp_path):
    p = _write(tmp_path, [_full(falsify="   ")])
    with pytest.raises(idea_spec.SpecError):
        idea_spec.load(p)


def test_falsify_equals_mechanism_rejected(tmp_path):
    p = _write(tmp_path, [_full(falsify="营收上调且利润上调才可信")])
    with pytest.raises(idea_spec.SpecError) as exc:
        idea_spec.load(p)
    assert "falsify" in str(exc.value)


def test_bad_json_rejected(tmp_path):
    p = tmp_path / "bad.jsonl"
    p.write_text("{not json", encoding="utf-8")
    with pytest.raises(idea_spec.SpecError):
        idea_spec.load(p)