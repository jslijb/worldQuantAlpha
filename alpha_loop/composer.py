from __future__ import annotations

import hashlib

from . import config

SHAPES = ["A", "B", "C", "D", "E", "F", "G", "H", "I"]
RELATIONS = {"div": "({a} / {b})", "mul": "({a} * {b})", "sub": "({a} - {b})"}


def _rel(kind: str, a: str, b: str) -> str:
    return RELATIONS[kind].format(a=a, b=b)


def compose(shape: str, a: str, b: str, params: dict) -> str:
    n = params.get("n", 60)
    n2 = params.get("n2", 45)
    m = params.get("m", 120)
    g = params.get("g", "industry")
    rel = params.get("rel", "div")
    core = _rel(rel, a, b)
    if shape == "A":
        return f"group_scale(ts_av_diff({core}, {n}), {g})"
    if shape == "B":
        return f"group_zscore(ts_av_diff({a}, {n}) - ts_av_diff({b}, {n2}), {g})"
    if shape == "C":
        return f"group_scale(ts_av_diff({core}, {n}) / ts_std_dev({core}, {m}), {g})"
    if shape == "D":
        return f'group_zscore(if_else({a} > {b}, ({a} / {b}), ({b} / {a})), {g})'
    if shape == "E":
        return f"group_scale(ts_corr({a}, {b}, {n}), {g})"
    if shape == "F":
        return f"group_zscore(ts_regression({a}, {b}, {n}, lag=0, rettype=0), {g})"
    if shape == "G":
        return f"rank(ts_av_diff({core}, {n}))"
    if shape == "H":
        return f"group_neutralize(ts_av_diff({core}, {n}), {g})"
    if shape == "I":
        return f'quantile(ts_av_diff({core}, {n}), driver="gaussian")'
    raise ValueError(f"unknown shape {shape}")


def param_grid(region: str, shapes: list[str] | None = None) -> list[dict]:
    shapes = shapes or SHAPES
    out = []
    for shape in shapes:
        for n in config.WINDOWS_N:
            for g in config.GROUPS:
                if shape == "G":
                    out.append({"shape": shape, "n": n, "g": g, "rel": "div"})
                    continue
                if shape == "I":
                    out.append({"shape": shape, "n": n, "g": g, "rel": "div"})
                    continue
                out.append({"shape": shape, "n": n, "n2": config.WINDOWS_N[(config.WINDOWS_N.index(n) + 1) % len(config.WINDOWS_N)],
                            "m": config.WINDOWS_M[len(out) % len(config.WINDOWS_M)], "g": g, "rel": "div"})
    return out


def unit_key(market: str, idea_id: str, params: dict, expr: str) -> str:
    raw = f"{market}|{idea_id}|{params.get('shape')}|{params.get('n')}|{params.get('g')}|{params.get('rel')}|{expr}"
    return f"{config.BATCH_TAG}_{market}_{idea_id[:24]}_{hashlib.sha1(raw.encode()).hexdigest()[:12]}"


def choose_settings(region: str, universe: str, idx: int) -> dict:
    neuts = [x for x in config.NEUTRALIZATIONS
             if x != "STATISTICAL" or region in config.NEUTRALIZATIONS_STAT_OK]
    return {
        "instrumentType": "EQUITY",
        "region": region,
        "universe": universe,
        "delay": config.DELAY,
        "decay": config.DECAYS[idx % len(config.DECAYS)],
        "neutralization": neuts[idx % len(neuts)],
        "truncation": config.TRUNCATION,
        "pasteurization": config.PASTEURIZATION,
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "language": "FASTEXPR",
        "visualization": False,
    }