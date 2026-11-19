from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PKG_DIR = Path(__file__).resolve().parent
STATE_DIR = PKG_DIR / "state"
FIELDB_DIR = STATE_DIR / "fielddb"
RAW_DIR = STATE_DIR / "raw"
VERDICT_DIR = STATE_DIR / "verdicts"
KNOWLEDGE_DIR = STATE_DIR / "knowledge"
REPORT_DIR = STATE_DIR / "reports"
TEST_DIR = PKG_DIR / "tests"

CRED_PATH = Path(os.environ.get("AQ_CRED", ROOT / "brain_credentials.txt"))
API_BASE = os.environ.get("AQ_API", "https://api.worldquantbrain.com")

MARKET_PRIORITY = ["GLB", "EUR", "ASI", "JPN", "CHN"]
USA_LAST_RESORT = True
USA_FALLBACK_ONLY = True
MARKET_PRIORITY_FULL = ["GLB", "EUR", "ASI", "JPN", "CHN", "USA"]

UNIVERSES = {
    "GLB": ["TOP3000", "MINVOL1M"],
    "EUR": ["TOP2500", "MINVOL1M"],
    "ASI": ["MINVOL1M"],
    "JPN": ["TOP800"],
    "CHN": ["TOP2000U", "TOP2000"],
    "USA": ["TOP3000", "TOP1000"],
}

NEUTRALIZATIONS = ["SUBINDUSTRY", "INDUSTRY", "MARKET", "STATISTICAL"]
NEUTRALIZATIONS_STAT_OK = {"GLB", "USA", "EUR"}
DECAYS = [0, 6, 12, 20, 32, 64]
TRUNCATION = 0.08
PASTEURIZATION = "ON"
DELAY = 1

GROUP_FIELDS = {"country", "exchange", "market", "sector", "industry", "subindustry"}
GROUPS = ["subindustry", "industry", "sector", "exchange", "sector+country"]

OPERATORS = {
    "add", "subtract", "multiply", "divide", "abs", "log", "sign", "power", "sqrt",
    "max", "min", "if_else", "inverse", "signed_power", "log_diff", "nan_mask",
    "ts_rank", "ts_zscore", "ts_scale", "ts_quantile", "ts_std_dev", "ts_mean",
    "ts_sum", "ts_delta", "ts_av_diff", "ts_corr", "ts_covariance", "ts_regression",
    "ts_decay_linear", "ts_decay_exp_window", "ts_arg_max", "ts_arg_min", "ts_max",
    "ts_min", "ts_median", "ts_product", "ts_returns", "ts_delay", "ts_backfill",
    "ts_count_nans", "ts_ir", "ts_skewness", "ts_kurtosis", "ts_moment",
    "ts_weighted_delay", "ts_step", "ts_min_max_cps", "ts_min_max_diff",
    "rank", "zscore", "normalize", "scale", "quantile", "winsorize", "bucket",
    "group_rank", "group_zscore", "group_scale", "group_neutralize", "group_mean",
    "group_sum", "group_max", "group_min", "group_median", "group_std_dev",
    "group_count", "group_backfill", "group_extra", "group_vector_neut",
    "hump", "hump_decay", "trade_when", "if_else", "kth_element",
    "vec_avg", "vec_sum", "vec_ir", "vec_max", "vec_min", "vec_count",
    "regression_neut", "regression_proj", "days_from_last_change",
    "last_diff_value", "jump_decay", "filter", "sigmoid", "tanh", "exp",
    "arc_tan", "arc_sin", "arc_cos", "inverse", "reverse", "s_log_1p",
    "fraction", "purify", "densify", "replace", "pasteurize", "to_nan",
    "left_tail", "right_tail", "clamp", "keep", "drop", "one_side",
    "simple_regression", "signed_log", "scaling", "linear_regression",
}

NAMED_PARAMS = {
    "driver", "std", "range", "rettype", "lag", "dense", "constant", "filter",
    "k", "ignore", "limit", "lower", "upper", "target", "distribution",
}

BANNED_OPERATORS: dict[str, str] = {}
XOP_WHITELIST = {"group_rank", "group_scale", "group_zscore", "group_neutralize",
                 "rank", "quantile"}
XOP_MAX_SHARE = 0.60

MAX_FIELDS_PER_ALPHA = 2
MIN_NEW_FIELDS_PER_BATCH = 2
MAX_IDEA_SHARE = 0.30
MIN_DATASET_ENTROPY = 0.50

MAX_CONCURRENT = 1
SIM_TIMEOUT = int(os.environ.get("AQ_SIM_TIMEOUT", 1800))
SIM_POLL_INTERVAL = 5
ROUND_INTERVAL = int(os.environ.get("AQ_ROUND_INTERVAL", 20))
BATCH_SIZE = 12
SIM_DAILY = int(os.environ.get("AQ_SIM_DAILY", 80))

IDEA_BUDGET = 12
DAILY_REGULAR_QUOTA = 4
SUBMIT_HOUR_BJ = 14

PRECHECK_MAX = 0.69
PRECHECK_HARD_BAND = 0.68
SELF_CORR_LIMIT = 0.70
PROD_CORR_LIMIT = 0.70

THRESHOLDS = {
    "sharpe": 1.58,
    "fitness": 1.0,
    "sharpe_2y": 1.58,
    "turnover_max": 0.70,
    "ladder_min": 2.02,
}
THRESHOLDS_CHN = {"sharpe": 2.07, "robust_factor": 0.4}
GLB_REGION_MIN = 1.0

BANNED_DATASET_PATTERNS = [r"^pv[0-9]*$", r"^pricevolume", r"^pv_"]


def is_banned_dataset(dataset_id, region=None) -> bool:
    if not dataset_id:
        return False
    if region is not None and str(region).upper() != "USA":
        return False
    low = str(dataset_id).lower()
    return any(re.match(pat, low) for pat in BANNED_DATASET_PATTERNS)


USA_UNUSED_DATASET_ONLY = True
BASELINE_TTL_HOURS = 24
FIELDB_TTL_DAYS = 7

COV_MIN = 0.80
USED_FIELD_PENALTY = 1000

WINDOWS_N = [20, 45, 60, 120]
WINDOWS_M = [60, 120, 250]

ROLE_SYNONYMS = {
    "ratio": ["ratio", "to", "per", "divided", "margin", "premium", "spread"],
    "level": ["level", "value", "amount", "total", "size"],
    "estimate": ["estimate", "consensus", "forecast", "expected", "target"],
    "revision": ["revision", "change", "upgrade", "downgrade", "momentum"],
    "dispersion": ["dispersion", "std", "deviation", "spread", "disagreement"],
    "volatility": ["volatility", "implied", "realized", "variance", "skew"],
    "sentiment": ["sentiment", "tone", "news", "score", "attention"],
    "flow": ["flow", "volume", "turnover", "buy", "sell", "net"],
    "quality": ["quality", "accrual", "profitable", "efficiency", "leverage"],
}

BATCH_TAG = "aq2"

for _d in (STATE_DIR, FIELDB_DIR, RAW_DIR, VERDICT_DIR, KNOWLEDGE_DIR, REPORT_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def today_bj():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=8))).date()


def now_bj():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=8)))


def today_east():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=-4))).date()


def is_operator_banned(name: str, on_date=None) -> bool:
    until = BANNED_OPERATORS.get(name.lower())
    if not until:
        return False
    from datetime import date
    return (on_date or date.today()) <= date.fromisoformat(until)


if __name__ == "__main__":
    print("MARKET_PRIORITY", MARKET_PRIORITY)
    print("SUBMIT_HOUR_BJ", SUBMIT_HOUR_BJ)
    print("BANNED_OPERATORS", BANNED_OPERATORS)
    print("USA_UNUSED_DATASET_ONLY", USA_UNUSED_DATASET_ONLY)
    print("STATE_DIR", STATE_DIR)
    print("group_rank banned today:", is_operator_banned("group_rank"))