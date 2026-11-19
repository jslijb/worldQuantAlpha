from __future__ import annotations

import argparse
import time

from . import composer, config, gates, judge
from .auth import Brain
from .fielddb import FieldDB
from .sim import run


def main(market: str, expr: str, universe: str, neut: str, decay: int, tag: str,
         tries: int = 15, wait: int = 60) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load(market, universe)
    ok_o, _ = gates.operators.check(expr)
    ok_d, _ = gates.depth.check(expr)
    ok_a, d_a = gates.atom.atom_pass(expr, market, fdb)
    if not (ok_o and ok_d and ok_a):
        print("GATE_FAIL", ok_o, ok_d, ok_a, d_a)
        return 3
    settings = composer.choose_settings(market, universe, 0)
    settings["neutralization"] = neut
    settings["decay"] = decay
    unit = {"unit_id": tag, "idea_id": tag, "region": market, "shape": "custom",
            "params": {"neut": neut, "decay": decay}, "expr": expr,
            "dataset": d_a["datasets"][0], "fields": d_a["fields"], "settings": settings}
    for i in range(1, tries + 1):
        res = run(brain, unit)
        st = res.get("status")
        if st == "done":
            v = judge.verdict(res.get("alpha") or {}, market)
            print("OK", i, res["alpha_id"], judge.summarize(v), flush=True)
            print("CHECKS", str(v.get("checks"))[:700], flush=True)
            return 0
        code = str(res.get("http"))
        body = str(res.get("body"))[:120]
        print(f"TRY{i} {st} {code} {body}", flush=True)
        if code == "401":
            brain.relogin()
        if "400" in code and "CONCURRENT" not in body:
            return 4
        time.sleep(wait)
    print("GAVE_UP", tries)
    return 5


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="EUR")
    ap.add_argument("--expr", required=True)
    ap.add_argument("--universe", default="")
    ap.add_argument("--neut", default="SUBINDUSTRY")
    ap.add_argument("--decay", type=int, default=12)
    ap.add_argument("--tag", default="retry")
    ap.add_argument("--tries", type=int, default=15)
    ap.add_argument("--wait", type=int, default=60)
    a = ap.parse_args()
    uni = a.universe or config.UNIVERSES[a.market][0]
    raise SystemExit(main(a.market, a.expr, uni, a.neut, a.decay, a.tag, a.tries, a.wait))