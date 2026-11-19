from __future__ import annotations

import csv
import importlib.util
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (ROOT / ".codeartsdoer" / "skills" / "alpha-production-loop"
          / "scripts" / "sync_evidence.py")


def load_mod():
    spec = importlib.util.spec_from_file_location("sync_evidence", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def write_csv(path: Path, rows: list[dict]) -> None:
    cols = ["idea_id", "dataset", "region", "S", "verdict", "failChecks"]
    with io.open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in cols})


def test_empty_ledger():
    mod = load_mod()
    s = mod.summarize([], [], [])
    assert s["total"] == 0
    text = mod.render(s, "2026-01-01 00:00", {"ledger": "L", "verdicts": "V", "verdict_files": 0})
    assert "n=0" in text


def test_single_round():
    mod = load_mod()
    s = mod.summarize([{"verdict": "FAIL", "region": "EUR", "dataset": "fundamental23",
                        "S": "1.20", "failChecks": "LOW_SHARPE"}], [], [])
    assert s["total"] == 1
    assert s["verdict"]["FAIL"] == 1


def test_fail_code_parsing_strips_threshold():
    mod = load_mod()
    codes = mod.fail_codes("LOW_SUB_UNIVERSE_SHARPE(1.13<1.14), LOW_SHARPE, LOW_FITNESS(0.9)")
    assert codes == ["LOW_SUB_UNIVERSE_SHARPE", "LOW_SHARPE", "LOW_FITNESS"]


def test_region_and_dataset_grouping_with_submit():
    mod = load_mod()
    rows = [
        {"verdict": "SUBMITTED", "region": "EUR", "dataset": "d1", "S": "2.0", "failChecks": ""},
        {"verdict": "FAIL", "region": "EUR", "dataset": "d1", "S": "0.5", "failChecks": "LOW_SHARPE"},
        {"verdict": "FAIL", "region": "USA", "dataset": "d2", "S": "1.6", "failChecks": "LOW_FITNESS"},
    ]
    s = mod.summarize(rows, [], [])
    assert s["by_region"]["EUR"] == 2
    assert s["submit_by_region"]["EUR"] == 1
    assert s["by_dataset"]["d1"] == 2
    assert s["sharpe_pass"] == 2
    assert s["sharpe_n"] == 3


def test_verdict_correlation_extraction():
    mod = load_mod()
    v = [{"is": {"checks": [
        {"name": "PROD_CORRELATION", "value": 0.81},
        {"name": "SELF_CORRELATION", "value": 0.60},
        {"name": "SELF_CORRELATION", "value": None},
        {"name": "LOW_SHARPE", "value": 1.9},
    ]}}]
    s = mod.summarize([], v, [])
    assert s["prod"] == [0.81]
    assert s["self"] == [0.60]


def test_idempotent_hash_ignores_timestamp():
    mod = load_mod()
    a = "# t\n生成时间：2026-01-01 00:00\nbody n=1"
    b = "# t\n生成时间：2026-02-02 23:59\nbody n=1"
    assert mod.body_hash(a) == mod.body_hash(b)
    c = "# t\n生成时间：2026-01-01 00:00\nbody n=2"
    assert mod.body_hash(a) != mod.body_hash(c)


def test_render_always_labels_sample_size():
    mod = load_mod()
    s = mod.summarize(
        [{"verdict": "FAIL", "region": "EUR", "dataset": "d", "S": "1.0",
          "failChecks": "LOW_SHARPE"}],
        [{"is": {"checks": [{"name": "PROD_CORRELATION", "value": 0.71}]}}],
        [{"status": "verified"}],
    )
    text = mod.render(s, "2026-01-01 00:00", {"ledger": "L", "verdicts": "V", "verdict_files": 1})
    for token in ("台账轮次：n=", "PROD_CORRELATION 有值件数：n=", "verified n="):
        assert token in text

def test_malformed_verdict_is_classified_not_hidden():
    mod = load_mod()
    s = mod.summarize([
        {"verdict": "0.0777", "region": "EUR", "dataset": "d", "S": "", "failChecks": ""},
        {"verdict": "FAIL", "region": "EUR", "dataset": "d", "S": "", "failChecks": ""},
    ], [], [])
    assert s["verdict"]["OTHER_MALFORMED"] == 1
    assert s["verdict"]["FAIL"] == 1


def test_normalize_21_col_inserts_language_before_sharpe():
    mod = load_mod()
    raw = ["idea", "desc", "econ", "1", "cid", "aid", "expr", "ds", "EUR", "TOP2500",
           "INDUSTRY", "0", "FASTEXPR", "2.10", "1.40", "0.04", "SUBMITTED", "",
           "", "ok", "2026-11-18"]
    rec = mod.normalize_row(raw)
    assert rec["language"] == "FASTEXPR"
    assert rec["S"] == "2.10"
    assert rec["verdict"] == "SUBMITTED"


def test_normalize_19_col_missing_error_msg():
    mod = load_mod()
    raw = ["idea", "desc", "econ", "12", "cid", "aid", "expr", "ds", "EUR", "TOP2500",
           "SUBINDUSTRY", "10", "2.01", "1.43", "0.08", "FAIL", "Sub0.99", "降decay",
           "2026-11-17"]
    rec = mod.normalize_row(raw)
    assert rec["S"] == "2.01"
    assert rec["verdict"] == "FAIL"
    assert rec["failChecks"] == "Sub0.99"
    assert rec["fix_action"] == "降decay"


def test_normalize_unknown_length_returns_empty():
    mod = load_mod()
    assert mod.normalize_row(["a", "b", "c"]) == {}


def test_known_status_codes_are_accepted():
    mod = load_mod()
    s = mod.summarize([
        {"verdict": "SIM_OK", "region": "EUR", "dataset": "d", "S": "1.0", "failChecks": ""},
        {"verdict": "GATE_BLOCK", "region": "EUR", "dataset": "d", "S": "", "failChecks": ""},
        {"verdict": "REJECTED", "region": "EUR", "dataset": "d", "S": "", "failChecks": ""},
    ], [], [])
    assert s["verdict"].get("OTHER_MALFORMED", 0) == 0
    assert s["verdict"]["SIM_OK"] == 1
    assert s["verdict"]["GATE_BLOCK"] == 1
