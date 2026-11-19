from __future__ import annotations

import json
import re
import time
from pathlib import Path

from . import config

INDEX = config.KNOWLEDGE_DIR / "index.json"
ALLOWED_EVIDENCE = {"L1", "L2", "L3", "L4"}
VERIFY_EVIDENCE = {"L1", "L2"}
STATUSES = {"candidate", "verified", "promoted", "deprecated", "conflicted"}
KTYPES = {"idea_pattern", "expr_pattern", "failure_mode", "param_effect", "op_permission"}


class KnowledgeError(ValueError):
    pass


def _slug(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s[:48] or "entry"


def _load_index() -> dict:
    if INDEX.exists():
        try:
            return json.loads(INDEX.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"entries": {}}


def _save_index(idx: dict) -> None:
    tmp = INDEX.with_suffix(".tmp")
    tmp.write_text(json.dumps(idx, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(INDEX)


def record(ktype: str, statement: str, evidence_level: str, samples: int,
           controls: dict, source: str, region: str | None = None) -> str:
    if ktype not in KTYPES:
        raise KnowledgeError(f"bad ktype {ktype}")
    if evidence_level not in ALLOWED_EVIDENCE:
        raise KnowledgeError(f"bad evidence_level {evidence_level}")
    if not controls or not all(k in controls for k in ("depth", "shape", "params")):
        raise KnowledgeError("controls must include depth/shape/params")
    if not statement.strip():
        raise KnowledgeError("statement empty")
    if samples < 0:
        raise KnowledgeError("samples must be >=0")
    kid = f"{ktype}_{_slug(statement)}"
    idx = _load_index()
    path = config.KNOWLEDGE_DIR / f"{kid}.md"
    entry = {
        "id": kid, "ktype": ktype, "statement": statement.strip(),
        "evidence_level": evidence_level, "samples": samples, "controls": controls,
        "source": source, "region": region, "first_seen": time.strftime("%Y-%m-%d"),
        "last_verified": None, "verify_count": 0, "status": "candidate",
        "supersedes": None, "conflicts_with": [],
    }
    if kid in idx["entries"]:
        old = idx["entries"][kid]
        entry["first_seen"] = old.get("first_seen")
        entry["verify_count"] = old.get("verify_count", 0)
        entry["status"] = old.get("status", "candidate")
    idx["entries"][kid] = entry
    _save_index(idx)
    path.write_text(_render(entry), encoding="utf-8")
    return kid


def _render(e: dict) -> str:
    head = json.dumps(e, ensure_ascii=False, indent=2)
    body = (
        f"\n# {e['statement']}\n\n"
        f"- 类型：{e['ktype']}\n"
        f"- 证据等级：{e['evidence_level']}（{e['source']}）\n"
        f"- 状态：{e['status']}\n"
        f"- 样本量：{e['samples']}\n"
        f"- 控制项：深度={e['controls'].get('depth')}，形态={e['controls'].get('shape')}，"
        f"参数={e['controls'].get('params')}\n"
        f"- 复验次数：{e['verify_count']}\n"
    )
    return "---\n" + head + "\n---\n" + body


def verify(kid: str, evidence_level: str, samples: int, source: str) -> str:
    if evidence_level not in VERIFY_EVIDENCE:
        raise KnowledgeError("only L1/L2 can verify")
    idx = _load_index()
    e = idx["entries"].get(kid)
    if not e:
        raise KnowledgeError(f"unknown entry {kid}")
    e["verify_count"] = e.get("verify_count", 0) + 1
    e["samples"] = max(e.get("samples") or 0, samples)
    e["last_verified"] = time.strftime("%Y-%m-%d")
    if e["verify_count"] >= 2 and e["status"] == "candidate":
        e["status"] = "verified"
    idx["entries"][kid] = e
    _save_index(idx)
    (config.KNOWLEDGE_DIR / f"{kid}.md").write_text(_render(e), encoding="utf-8")
    return e["status"]


def promote(kid: str, min_samples: int = 10) -> str:
    idx = _load_index()
    e = idx["entries"].get(kid)
    if not e:
        raise KnowledgeError(f"unknown entry {kid}")
    if (e.get("samples") or 0) < min_samples:
        raise KnowledgeError("not enough samples to promote")
    if e.get("conflicts_with"):
        raise KnowledgeError("entry has conflicts")
    if e["status"] not in ("verified",):
        raise KnowledgeError("only verified can be promoted")
    e["status"] = "promoted"
    idx["entries"][kid] = e
    _save_index(idx)
    (config.KNOWLEDGE_DIR / f"{kid}.md").write_text(_render(e), encoding="utf-8")
    return e["status"]


def conflict(kid: str, counter_evidence: str) -> str:
    idx = _load_index()
    e = idx["entries"].get(kid)
    if not e:
        raise KnowledgeError(f"unknown entry {kid}")
    e["status"] = "conflicted"
    e["conflicts_with"] = list(set(e.get("conflicts_with") or []) | {counter_evidence[:120]})
    idx["entries"][kid] = e
    _save_index(idx)
    (config.KNOWLEDGE_DIR / f"{kid}.md").write_text(_render(e), encoding="utf-8")
    return e["status"]


def query(ktype: str | None = None, status: str | None = None) -> list[dict]:
    idx = _load_index()
    out = list(idx["entries"].values())
    if ktype:
        out = [e for e in out if e["ktype"] == ktype]
    if status:
        out = [e for e in out if e["status"] == status]
    return out


def feed(verdict: dict) -> None:
    cache = config.KNOWLEDGE_DIR / "feed_stats.json"
    stats = {"shape": {}, "fail_code": {}, "idea_kind": {}}
    if cache.exists():
        try:
            stats = json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass
    shape = verdict.get("shape") or "unknown"
    stats.setdefault("shape", {})
    stats["shape"][shape] = stats["shape"].get(shape, 0) + 1
    for code in verdict.get("fail_codes") or ["PASS"]:
        stats.setdefault("fail_code", {})
        stats["fail_code"][code] = stats["fail_code"].get(code, 0) + 1
    kind = verdict.get("idea_kind") or "other"
    stats.setdefault("idea_kind", {})
    stats["idea_kind"][kind] = stats["idea_kind"].get(kind, 0) + 1
    cache.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")


def stats() -> dict:
    cache = config.KNOWLEDGE_DIR / "feed_stats.json"
    if cache.exists():
        try:
            return json.loads(cache.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"shape": {}, "fail_code": {}, "idea_kind": {}}