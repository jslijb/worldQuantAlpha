from __future__ import annotations

from . import config

RESHAPE_ORDER = ["A", "B", "E", "F", "C", "H", "G", "I", "D"]

FAIL_MAP = {
    "LOW_SHARPE": "RESHAPE",
    "LOW_SHARPE_LOCAL": "RESHAPE",
    "LOW_FITNESS": "RETUNE_DECAY_UP",
    "LOW_FITNESS_LOCAL": "RETUNE_DECAY_UP",
    "HIGH_TURNOVER": "RETUNE_DECAY_UP",
    "HIGH_TURNOVER_LOCAL": "RETUNE_DECAY_UP",
    "LOW_TURNOVER": "RETUNE_DECAY_DOWN",
    "CONCENTRATED_WEIGHT": "SWITCH_RELATION",
    "LOW_SUB_UNIVERSE_SHARPE": "REUNIVERSE",
    "LOW_2Y_SHARPE": "RESHAPE",
    "LOW_ROBUST_UNIVERSE_SHARPE": "ABANDON",
    "SELF_CORRELATION": "REGROUP",
    "PROD_CORRELATION": "RETUNE_DECAY_UP",
    "LOW_AMER_SHARPE": "REGROUP",
    "LOW_EMEA_SHARPE": "REGROUP",
    "LOW_APAC_SHARPE": "REGROUP",
    "LOW_GLB_AMER_SHARPE": "REGROUP",
    "LOW_GLB_EMEA_SHARPE": "REGROUP",
    "LOW_GLB_APAC_SHARPE": "REGROUP",
}


def next_action(unit: dict, verdict: dict, history: list[dict] | None = None) -> dict:
    history = history or []
    codes = verdict.get("fail_codes") or []
    if verdict.get("status") == "FATAL":
        return {"kind": "ABANDON", "reason": "fatal", "codes": codes}
    if not codes:
        return {"kind": "QUEUE", "reason": "pass", "codes": []}

    if any(c == "LOW_ROBUST_UNIVERSE_SHARPE" for c in codes):
        return {"kind": "ABANDON", "reason": "chn_robust", "codes": codes}

    kinds = [FAIL_MAP.get(c) for c in codes if FAIL_MAP.get(c)]
    if not kinds:
        return {"kind": "ABANDON", "reason": "unmapped_fail", "codes": codes}

    same = [h for h in history if h.get("codes") == codes]
    if len(same) >= 3:
        return {"kind": "ABANDON", "reason": "no_improvement", "codes": codes}

    kind = kinds[0]
    action = {"kind": kind, "codes": codes, "attempt": len(history) + 1}

    params = dict(unit.get("params") or {})
    if kind == "RESHAPE":
        order = list(RESHAPE_ORDER)
        cur = params.get("shape")
        nxt = order[(order.index(cur) + 1) % len(order)] if cur in order else order[0]
        params["shape"] = nxt
        action["params"] = params
    elif kind == "RETUNE_DECAY_UP":
        params["decay_step"] = 1
        action["params"] = params
    elif kind == "RETUNE_DECAY_DOWN":
        params["decay_step"] = -1
        action["params"] = params
    elif kind in ("REGROUP", "SWITCH_RELATION"):
        groups = list(config.GROUPS)
        cur = params.get("g", groups[0])
        params["g"] = groups[(groups.index(cur) + 1) % len(groups)]
        if kind == "SWITCH_RELATION":
            rels = ["div", "sub", "mul"]
            params["rel"] = rels[(rels.index(params.get("rel", "div")) + 1) % len(rels)]
        action["params"] = params
    elif kind == "REUNIVERSE":
        action["universe_switch"] = True

    if len(history) >= config.IDEA_BUDGET:
        return {"kind": "ABANDON", "reason": "budget_exhausted", "codes": codes}
    return action


def apply_decay_step(settings: dict, step: int) -> dict:
    decays = config.DECAYS
    cur = settings.get("decay", decays[0])
    idx = decays.index(cur) if cur in decays else 0
    nidx = max(0, min(len(decays) - 1, idx + step))
    out = dict(settings)
    out["decay"] = decays[nidx]
    return out