from __future__ import annotations

import argparse
import json

from . import composer, config, gates, judge
from .auth import Brain
from .fielddb import FieldDB
from .sim import run


def main(market: str, expr: str, universe: str, neut: str, decay: int,
         trunc: float, tag: str) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load(market, universe)
    ok_o, d_o = gates.operators.check(expr)
    ok_d, d_d = gates.depth.check(expr)
    ok_a, d_a = gates.atom.atom_pass(expr, market, fdb)
    print("GATES", {"operators": ok_o, "depth": ok_d, "atom": ok_a})
    if not ok_a:
        print("ATOM", json.dumps(d_a, ensure_ascii=False))
    if not ok_d:
        print("DEPTH", json.dumps(d_d, ensure_ascii=False))
    if not (ok_o and ok_d and ok_a):
        return 3
    settings = composer.choose_settings(market, universe, 0)
    settings["neutralization"] = neut
    settings["decay"] = decay
    settings["truncation"] = trunc
    unit = {"unit_id": tag, "idea_id": tag, "region": market, "shape": "custom",
            "params": {"neut": neut, "decay": decay}, "expr": expr,
            "dataset": d_a["datasets"][0], "fields": d_a["fields"],
            "settings": settings}
    print("DS", unit["dataset"], "FIELDS", unit["fields"])
    print("EXPR", expr)
    res = run(brain, unit)
    if res.get("status") != "done":
        print("SIM_ERROR", res.get("http"), str(res.get("body"))[:400])
        return 4
    v = judge.verdict(res.get("alpha") or {}, market)
    print("ALPHA", res["alpha_id"])
    print("VERDICT", judge.summarize(v))
    print("CHECKS", json.dumps(v.get("checks"), ensure_ascii=False)[:900])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="GLB")
    ap.add_argument("--expr", required=True)
    ap.add_argument("--universe", default="")
    ap.add_argument("--neut", default="SUBINDUSTRY")
    ap.add_argument("--decay", type=int, default=20)
    ap.add_argument("--trunc", type=float, default=0.08)
    ap.add_argument("--tag", default="custom")
    a = ap.parse_args()
    uni = a.universe or config.UNIVERSES[a.market][0]
    raise SystemExit(main(a.market, a.expr, uni, a.neut, a.decay, a.trunc, a.tag))