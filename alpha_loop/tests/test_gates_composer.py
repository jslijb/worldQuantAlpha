from __future__ import annotations

import pytest

from alpha_loop import composer, config
from alpha_loop.fielddb import FieldDB
from alpha_loop.gates import atom, dataset, depth, diversity, operators


@pytest.fixture
def fdb():
    f = FieldDB()
    f._cache["GLB"] = {"region": "GLB", "universe": "TOP3000", "fields": {
        "fnd_a": {"id": "fnd_a", "dataset": "fundamental23", "coverage": 0.95,
                  "alphaCount": 10, "description": "cash flow from operations"},
        "fnd_b": {"id": "fnd_b", "dataset": "fundamental23", "coverage": 0.95,
                  "alphaCount": 10, "description": "enterprise value total"},
        "anl_a": {"id": "anl_a", "dataset": "analyst14", "coverage": 0.90,
                  "alphaCount": 5, "description": "estimate revision change"},
        "anl_b": {"id": "anl_b", "dataset": "analyst14", "coverage": 0.90,
                  "alphaCount": 5, "description": "estimate dispersion standard deviation"},
    }}
    return f


def test_group_rank_allowed_after_unban(monkeypatch):
    from alpha_loop import config
    for expr in ["group_rank(close, industry)", "group_zscore(group_rank(close, industry), sector)"]:
        ok, detail = operators.check(expr)
        assert ok, (expr, detail)
    monkeypatch.setitem(config.BANNED_OPERATORS, "group_rank", "2099-01-01")
    ok, detail = operators.check("group_rank(close, industry)")
    assert not ok and detail["reason"] == "BANNED_OPERATOR"


def test_operators_allow_replacements():
    for expr in ["group_scale(x, industry)", "group_zscore(x, sector)", "rank(ts_mean(x,20))"]:
        ok, _ = operators.check(expr)
        assert ok, expr


def test_depth_all_shapes_pass(fdb):
    for shape in composer.SHAPES:
        expr = composer.compose(shape, "anl_a", "anl_b",
                                {"shape": shape, "n": 60, "n2": 45, "m": 120, "g": "industry", "rel": "div"})
        ok, detail = depth.check(expr)
        assert ok, (shape, expr, detail)


def test_depth_rejects_shallow_and_norm_sum():
    bad = [
        "ts_rank(close, 20)",
        "rank(close)",
        "group_zscore(cashflow_op, industry) + group_zscore(enterprise_value, industry)",
        "rank(ts_mean(a,20)) + rank(ts_mean(b,20))",
    ]
    for expr in bad:
        ok, _ = depth.check(expr)
        assert not ok, expr


def test_atom_rules(fdb):
    ok, d = atom.atom_pass("group_scale(ts_av_diff(fnd_a/fnd_b,60), industry)", "GLB", fdb)
    assert ok and d["datasets"] == ["fundamental23"]
    ok, d = atom.atom_pass("group_scale(ts_av_diff(fnd_a/anl_a,60), industry)", "GLB", fdb)
    assert not ok and d["reason"] == "CROSS_DATASET"
    ok, d = atom.atom_pass("group_scale(close, industry)", "GLB", fdb)
    assert not ok and d["reason"] == "UNKNOWN_DATASET"


def test_atom_ignores_operators_and_named_params(fdb):
    expr = 'quantile(ts_av_diff(fnd_a/fnd_b,60), driver="gaussian")'
    fields = fdb.business_fields(expr)
    assert set(fields) == {"fnd_a", "fnd_b"}


def test_usa_dataset_gate():
    used = {"fundamental23"}
    ok, _ = dataset.dataset_pass("fundamental23", "USA", used)
    assert not ok
    ok, _ = dataset.dataset_pass("fundamental23", "GLB", used)
    assert ok
    ok, _ = dataset.dataset_pass("analyst14", "USA", used)
    assert ok


def _unit(uid, idea="i1", ds="d1", fields=None, expr="group_scale(ts_av_diff(a/b,60),industry)"):
    return {"unit_id": uid, "idea_id": idea, "dataset": ds, "fields": fields or ["a", "b"], "expr": expr}


def test_diversity_pass_and_fail():
    batch = [_unit("u1", idea="i1", ds="d1", expr="group_scale(ts_av_diff(a/b,60),industry)"),
             _unit("u2", idea="i2", ds="d2", expr="group_zscore(ts_corr(a,b,45),sector)")]
    ok, d = diversity.check(batch, used_fields=set())
    assert ok, d
    ok, _ = diversity.check([_unit("u1", fields=["a", "b", "c"])], set())
    assert not ok
    ok, _ = diversity.check([_unit("u1"), _unit("u2")], used_fields={"a", "b"})
    assert not ok
    ok, _ = diversity.check([_unit("u1", idea="x", ds="d1"), _unit("u2", idea="x", ds="d1"),
                             _unit("u3", idea="x", ds="d1")], set())
    assert not ok


def test_composer_never_emits_group_rank(fdb):
    for shape in composer.SHAPES:
        expr = composer.compose(shape, "anl_a", "anl_b",
                                {"shape": shape, "n": 60, "n2": 45, "m": 120, "g": "industry", "rel": "div"})
        assert "group_rank" not in expr.replace(" ", "").lower()

def test_banned_dataset_blacklist():
    from alpha_loop import config
    for ds in ("pv1", "pv13", "pv", "pv20"):
        ok, d = dataset.dataset_pass(ds, "USA", set())
        assert not ok and d["reason"] == "BANNED_DATASET_CROWDED", ds
    for ds in ("pv1", "pv13"):
        ok, _ = dataset.dataset_pass(ds, "EUR", set())
        assert ok, ds
    for ds in ("fundamental23", "analyst10", "option8"):
        ok, _ = dataset.dataset_pass(ds, "EUR", set())
        assert ok, ds
    assert config.MAX_CONCURRENT == 1
