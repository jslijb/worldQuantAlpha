from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from alpha_loop import config, knowledge, queue, repair, submit
from alpha_loop.judge import verdict


@pytest.fixture(autouse=True)
def isolate_state(tmp_path, monkeypatch):
    monkeypatch.setattr(queue, "PENDING", tmp_path / "pending.json")
    monkeypatch.setattr(config, "KNOWLEDGE_DIR", tmp_path / "knowledge")
    config.KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(knowledge, "INDEX", config.KNOWLEDGE_DIR / "index.json")
    yield


def _bj(h, m=0, s=0):
    return datetime(2026, 11, 16, h, m, s, tzinfo=timezone(timedelta(hours=8)))


def test_clock_boundaries():
    assert not submit.clock_gate(_bj(13, 59, 59))
    assert submit.clock_gate(_bj(14, 0, 0))


def test_queue_survives_day_and_dedupes():
    unit = {"unit_id": "u1", "region": "GLB"}
    item = queue.enqueue("A1", unit, {"S": 2.0}, day_target="2026-11-16")
    assert item["status"] == "ready"
    queue.enqueue("A1", unit, {"S": 2.0})
    assert len(queue.peek()) == 1
    assert len(queue.peek(day_target="2026-11-15")) == 0
    assert len(queue.peek(day_target="2026-11-17")) == 1
    queue.mark("A1", "submitted")
    assert queue.peek() == []


def test_repair_branches():
    unit = {"params": {"shape": "A", "g": "industry"}}
    a = repair.next_action(unit, {"status": "FAIL", "fail_codes": ["LOW_SHARPE"]})
    assert a["kind"] == "RESHAPE" and a["params"]["shape"] == "B"
    a = repair.next_action(unit, {"status": "FAIL", "fail_codes": ["LOW_FITNESS"]})
    assert a["kind"] == "RETUNE_DECAY_UP"
    a = repair.next_action(unit, {"status": "FAIL", "fail_codes": ["CONCENTRATED_WEIGHT"]})
    assert a["kind"] == "SWITCH_RELATION"
    a = repair.next_action(unit, {"status": "FAIL", "fail_codes": ["LOW_ROBUST_UNIVERSE_SHARPE"]})
    assert a["kind"] == "ABANDON"
    a = repair.next_action(unit, {"status": "FAIL", "fail_codes": ["LOW_SHARPE"]},
                           history=[{"codes": ["LOW_SHARPE"]}] * 3)
    assert a["kind"] == "ABANDON"


def test_decay_steps():
    s = {"decay": 20}
    assert repair.apply_decay_step(s, 1)["decay"] == 32
    assert repair.apply_decay_step({"decay": 0}, -1)["decay"] == 0
    assert repair.apply_decay_step({"decay": 64}, 1)["decay"] == 64


def test_judge_pass_and_fail():
    alpha = {"id": "A1", "is": {"sharpe": 2.0, "fitness": 1.2, "turnover": 0.2,
                                "checks": [{"name": "LOW_SHARPE", "result": "PASS"}]}}
    v = verdict(alpha, "GLB")
    assert v["status"] == "PASS_READY"
    alpha["is"]["sharpe"] = 1.0
    v = verdict(alpha, "GLB")
    assert v["status"] == "FAIL" and "LOW_SHARPE_LOCAL" in v["fail_codes"]
    v = verdict({}, "GLB")
    assert v["status"] == "FATAL"


def test_knowledge_audit_rules():
    kid = knowledge.record("expr_pattern", "比值差分优先于独立归一化相加", "L1", 5,
                           {"depth": "2层", "shape": "A", "params": "n=60"}, "test")
    assert knowledge.query(status="candidate")
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.record("expr_pattern", "bad", "L1", 1, {}, "test")
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.verify(kid, "L4", 3, "blog")
    assert knowledge.verify(kid, "L1", 6, "rerun") == "candidate"
    assert knowledge.verify(kid, "L1", 7, "rerun2") == "verified"
    assert knowledge.promote(kid, min_samples=5) == "promoted"
    assert knowledge.conflict(kid, "反例") == "conflicted"
    with pytest.raises(knowledge.KnowledgeError):
        knowledge.promote(kid, min_samples=1)