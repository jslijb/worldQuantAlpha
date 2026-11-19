"""从事实源生成判据快照（幂等）。

事实源（只读）：
  - data/alpha_quality_analysis/IDEA_LOOP_LEDGER.csv
  - alpha_loop/state/verdicts/*.json
  - alpha_loop/state/knowledge/index.json

输出：
  - references/evidence/criteria_snapshot.md

约束：
  - 只输出可由事实源直接算出的统计量；不生成任何"机制成立/不成立"的判断。
  - 每个统计数字都带 n= 样本量。
  - 正文（剔除时间戳行）无变化时不写盘、不追加 CHANGELOG。
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import sys
import time
from collections import Counter
from pathlib import Path

SNAPSHOT_REL = "references/evidence/criteria_snapshot.md"
CHANGELOG_REL = "CHANGELOG.md"
GEN_MARK = "生成时间："

OP_NAMES = set("""
group_rank group_zscore group_scale group_neutralize rank ts_rank ts_zscore ts_mean
ts_std_dev ts_delta ts_sum ts_av_diff ts_decay_linear ts_delay ts_backfill ts_corr
ts_regression winsorize normalize quantile bucket if_else trade_when power log sign abs
max min add subtract multiply divide vec_avg vec_sum zscore scale hump signed_power
arc_tan tanh pasteurize filter reverse is_nan not and or less greater densify vec_ir
group_max group_min group_mean nan_mask ts_arg_max ts_arg_min ts_count_nans ts_product
ts_scale ts_quantile ts_min ts_max days_from_last_change last_diff_value kth_element
jump_decay
""".split())

GROUP_PARAMS = {"subindustry", "industry", "sector", "market", "country",
                "exchange", "true", "false", "nan"}

IDENT_CALL = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
IDENT_ANY = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)")


def expression_balance(rows: list[dict]) -> dict:
    """统计可解析表达式的算子频次与字段频次（只做计数，不做判断）。"""
    ops: Counter = Counter()
    flds: Counter = Counter()
    n = 0
    for r in rows:
        expr = (r.get("expression") or "").strip()
        if len(expr) < 12:
            continue
        n += 1
        ops.update(IDENT_CALL.findall(expr))
        for tok in IDENT_ANY.findall(expr):
            if tok in OP_NAMES or tok in GROUP_PARAMS:
                continue
            flds[tok] += 1
    op_total = sum(ops.values())
    fld_total = sum(flds.values())
    return {
        "expr_n": n,
        "ops": ops,
        "op_total": op_total,
        "op_top": ops.most_common(5),
        "single_op_share": (ops.most_common(1)[0][1] / op_total) if op_total else None,
        "fields": flds,
        "field_kinds": len(flds),
        "fld_total": fld_total,
        "field_top": flds.most_common(5),
        "top5_share": (sum(v for _, v in flds.most_common(5)) / fld_total) if fld_total else None,
    }

VERDICT_HEADS = {
    "FAIL", "FAIL(403)", "SUBMITTED", "SUBMIT", "SUBMIT_READY", "PASS_READY",
    "ACCEPTED", "ACCEPTED_CANDIDATE", "REJECTED",
    "GATE_FAIL", "GATE_BLOCK", "SIM_ERROR", "SIM_OK",
    "EMPTY", "SKIP", "IDEA_EXHAUSTED", "STILL_RUNNING",
    "OTHER_MALFORMED",
}


def find_repo_root(start: Path) -> Path:
    for p in [start, *start.parents]:
        if (p / "alpha_loop").is_dir() and (p / "data").is_dir():
            return p
    raise RuntimeError("repo root not found (need alpha_loop/ and data/)")


LEDGER_HEADER = [
    "idea_id", "idea_desc", "econ_check", "round", "cid", "alpha_id", "expression",
    "dataset", "region", "universe", "neutralization", "decay", "S", "F", "TO",
    "verdict", "failChecks", "error_msg", "fix_action", "timestamp",
]


def normalize_row(raw: list[str]) -> dict:
    """历史台账存在三种列数（19/20/21），按已知版本差异归一化。

    21 列：在第 12 位多插入了 language（PYTHON/FASTEXPR）
    19 列：缺少 error_msg
    其他长度：返回空 dict，由调用方计入 malformed。
    """
    n = len(raw)
    if n == len(LEDGER_HEADER):
        keys = LEDGER_HEADER
    elif n == len(LEDGER_HEADER) + 1:
        keys = LEDGER_HEADER[:12] + ["language"] + LEDGER_HEADER[12:]
    elif n == len(LEDGER_HEADER) - 1:
        keys = LEDGER_HEADER[:17] + LEDGER_HEADER[18:]
    else:
        return {}
    return dict(zip(keys, raw))


def load_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with io.open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return []
    out = []
    for raw in rows[1:]:
        if not raw or not any(x.strip() for x in raw):
            continue
        rec = normalize_row(raw)
        if not rec:
            continue
        out.append(rec)
    return out


def _num(v) -> float | None:
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def fail_codes(raw: str) -> list[str]:
    out = []
    for part in (raw or "").split(","):
        name = part.strip().split("(")[0].strip()
        if name:
            out.append(name)
    return out


def summarize(rows: list[dict], verdicts: list[dict], knowledge: list[dict]) -> dict:
    total = len(rows)
    verdict = Counter()
    fails = Counter()
    by_region = Counter()
    by_dataset = Counter()
    submit_by_region = Counter()
    submit_by_dataset = Counter()
    sharpe_pass = 0
    sharpe_n = 0

    for r in rows:
        v = (r.get("verdict") or "").strip()
        head = v.split(":")[0] if v else "EMPTY"
        if head not in VERDICT_HEADS:
            head = "OTHER_MALFORMED"
        verdict[head] += 1
        for f in fail_codes(r.get("failChecks") or r.get("fail_checks") or ""):
            fails[f] += 1
        region = (r.get("region") or "?").strip()
        ds = (r.get("dataset") or "?").strip()
        by_region[region] += 1
        by_dataset[ds] += 1
        if head in ("SUBMITTED", "SUBMIT"):
            submit_by_region[region] += 1
            submit_by_dataset[ds] += 1
        s = _num(r.get("S"))
        if s is not None:
            sharpe_n += 1
            if s >= 1.58:
                sharpe_pass += 1

    prod_vals = []
    self_vals = []
    for d in verdicts:
        for scope in ("is", "os"):
            for c in (d.get(scope) or {}).get("checks", []) or []:
                name = c.get("name")
                if c.get("value") is None:
                    continue
                if name == "PROD_CORRELATION":
                    prod_vals.append(float(c["value"]))
                elif name == "SELF_CORRELATION":
                    self_vals.append(float(c["value"]))

    return {
        "total": total,
        "verdict": verdict,
        "fails": fails,
        "by_region": by_region,
        "by_dataset": by_dataset,
        "submit_by_region": submit_by_region,
        "submit_by_dataset": submit_by_dataset,
        "sharpe_pass": sharpe_pass,
        "sharpe_n": sharpe_n,
        "prod": sorted(prod_vals),
        "self": sorted(self_vals),
        "knowledge_total": len(knowledge),
        "knowledge_verified": sum(1 for k in knowledge if k.get("status") == "verified"),
        "balance": expression_balance(rows),
    }


def _pct(part: int, whole: int) -> str:
    if whole <= 0:
        return "n/a"
    return f"{part / whole * 100:.1f}%"


def render(summ: dict, generated_at: str, sources: dict) -> str:
    s = summ
    lines = [
        "# 判据快照（自动生成，勿手改）",
        "",
        f"{GEN_MARK}{generated_at}",
        f"生成脚本：`scripts/sync_evidence.py`",
        "",
        "> 本文件只包含可由台账 / 平台判决书直接算出的统计量。机制类结论见 SKILL.md 与 knowledge。",
        "",
        "## 样本",
        "",
        f"- 台账轮次：n={s['total']}（来源 `{sources['ledger']}`）",
        f"- 判决书文件：n={sources['verdict_files']}（来源 `{sources['verdicts']}`）",
        f"- 经验条目：n={s['knowledge_total']}，其中 verified n={s['knowledge_verified']}",
        "",
        "## 判决分布",
        "",
    ]
    for k, v in s["verdict"].most_common():
        lines.append(f"- {k}: n={v}（占 n={s['total']} 的 {_pct(v, s['total'])}）")
    if not s["verdict"]:
        lines.append("- （无数据）")

    lines += ["", "## FAIL 项频次（前 10）", ""]
    for k, v in s["fails"].most_common(10):
        lines.append(f"- {k}: n={v}")
    if not s["fails"]:
        lines.append("- （无数据）")

    lines += ["", "## 按区域", "", "| 区域 | 轮次 | 提交 | 提交率 |", "|---|---|---|---|"]
    for k, v in s["by_region"].most_common():
        sub = s["submit_by_region"].get(k, 0)
        lines.append(f"| {k} | n={v} | n={sub} | {_pct(sub, v)} |")
    if not s["by_region"]:
        lines.append("| （无数据） | n=0 | n=0 | n/a |")

    lines += ["", "## 按数据集（前 10）", "", "| 数据集 | 轮次 | 提交 | 提交率 |", "|---|---|---|---|"]
    for k, v in s["by_dataset"].most_common(10):
        sub = s["submit_by_dataset"].get(k, 0)
        lines.append(f"| {k} | n={v} | n={sub} | {_pct(sub, v)} |")
    if not s["by_dataset"]:
        lines.append("| （无数据） | n=0 | n=0 | n/a |")

    lines += [
        "",
        "## 台账内 Sharpe 过线率",
        "",
        f"- S≥1.58：n={s['sharpe_pass']} / n={s['sharpe_n']}（n/a 表示台账未记录 S）",
        "",
        "## 平台相关性实测值（来自判决书）",
        "",
        f"- PROD_CORRELATION 有值件数：n={len(s['prod'])}",
    ]
    if s["prod"]:
        lines.append(f"  - 最小 {s['prod'][0]:.4f} / 中位 {s['prod'][len(s['prod']) // 2]:.4f} / 最大 {s['prod'][-1]:.4f}")
    lines.append(f"- SELF_CORRELATION 有值件数：n={len(s['self'])}")
    if s["self"]:
        lines.append(f"  - 最小 {s['self'][0]:.4f} / 中位 {s['self'][len(s['self']) // 2]:.4f} / 最大 {s['self'][-1]:.4f}")
    lines.append("")
    return "\n".join(lines)


def body_hash(text: str) -> str:
    kept = [ln for ln in text.splitlines() if not ln.startswith(GEN_MARK)]
    return hashlib.sha256("\n".join(kept).encode("utf-8")).hexdigest()


def main() -> int:
    skill_dir = Path(__file__).resolve().parents[1]
    repo = find_repo_root(skill_dir)

    ledger = repo / "data" / "alpha_quality_analysis" / "IDEA_LOOP_LEDGER.csv"
    verdict_dir = repo / "alpha_loop" / "state" / "verdicts"
    knowledge_index = repo / "alpha_loop" / "state" / "knowledge" / "index.json"

    rows = load_ledger(ledger)
    verdicts = []
    if verdict_dir.is_dir():
        for p in sorted(verdict_dir.glob("*.json")):
            try:
                verdicts.append(json.loads(p.read_text(encoding="utf-8")))
            except Exception:
                continue
    knowledge = []
    if knowledge_index.exists():
        try:
            idx = json.loads(knowledge_index.read_text(encoding="utf-8"))
            knowledge = list((idx.get("entries") or {}).values())
        except Exception:
            knowledge = []

    summ = summarize(rows, verdicts, knowledge)
    sources = {
        "ledger": "data/alpha_quality_analysis/IDEA_LOOP_LEDGER.csv",
        "verdicts": "alpha_loop/state/verdicts/*.json",
        "verdict_files": len(verdicts),
    }
    now = time.strftime("%Y-%m-%d %H:%M")
    text = render(summ, now, sources)

    target = skill_dir / SNAPSHOT_REL
    target.parent.mkdir(parents=True, exist_ok=True)
    new_hash = body_hash(text)

    if target.exists():
        old = target.read_text(encoding="utf-8")
        if body_hash(old) == new_hash:
            print("NO_CHANGE", target)
            return 0

    target.write_text(text, encoding="utf-8")
    log = skill_dir / CHANGELOG_REL
    with io.open(log, "a", encoding="utf-8") as f:
        f.write(f"- {now} [AUTO] 快照更新：轮次 n={summ['total']} / "
                f"判决书 n={sources['verdict_files']} / "
                f"FAIL 首位 {summ['fails'].most_common(1) or 'none'}\n")
    print("UPDATED", target)
    return 0


if __name__ == "__main__":
    sys.exit(main())