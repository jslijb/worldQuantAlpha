from __future__ import annotations

import argparse
import threading
from concurrent.futures import ThreadPoolExecutor

from . import composer, config, gates, judge, queue
from .auth import Brain
from .fielddb import FieldDB
from .sim import run


def main(market: str, a: str, b: str, n: int, conc: int, shapes: list[str],
         groups: list[str], universes: list[str]) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load(market, universes[0])
    ok_a, d_a = gates.atom.atom_pass(f"({a} / {b})", market, fdb)
    if not ok_a:
        print("ATOM_FAIL", d_a)
        return 3
    ds = d_a["datasets"][0]
    print(f"PAIR {a} / {b} ds={ds} n={n}", flush=True)
    tasks = []
    idx = 0
    for shape in shapes:
        for g in groups:
            for uni in universes:
                tasks.append((shape, g, uni, idx))
                idx += 1
    lock = threading.Lock()
    results = []

    def work(t):
        shape, g, uni, i = t
        params = {"shape": shape, "n": n, "n2": n, "g": g, "rel": "div"}
        expr = composer.compose(shape, a, b, params)
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        if not (ok_o and ok_d):
            with lock:
                print(f"[{shape}/{g}/{uni}] GATE {d_d.get('reason')}", flush=True)
            return None
        unit = {"unit_id": f"scan_{abs(hash(expr)) % 10**10}", "idea_id": f"scan_{a}_{b}",
                "region": market, "shape": shape, "params": params, "expr": expr,
                "dataset": ds, "fields": [a, b],
                "settings": composer.choose_settings(market, uni, i)}
        res = run(brain, unit)
        if res.get("status") != "done":
            with lock:
                print(f"[{shape}/{g}/{uni}] ERR {str(res.get('body'))[:160]}", flush=True)
            return None
        v = judge.verdict(res.get("alpha") or {}, market)
        m = v.get("metrics") or {}
        with lock:
            print(f"[{shape}/{g}/{uni}] {res['alpha_id']} S={m.get('S')} F={m.get('F')} "
                  f"TO={m.get('TO')} {'PASS' if v['status'] == 'PASS_READY' else 'fail'}",
                  flush=True)
        if v["status"] == "PASS_READY":
            queue.enqueue(res["alpha_id"], unit, m)
        return v

    with ThreadPoolExecutor(max_workers=conc) as ex:
        for r in ex.map(work, tasks):
            if r:
                results.append(r)
    passed = [r for r in results if r["status"] == "PASS_READY"]
    print("SCAN_DONE", len(results), "pass", len(passed))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="GLB")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--conc", type=int, default=2)
    ap.add_argument("--shapes", default="ABCDEFGHI")
    ap.add_argument("--groups", default="industry,sector")
    ap.add_argument("--universes", default="")
    args = ap.parse_args()
    unis = args.universes.split(",") if args.universes else config.UNIVERSES[args.market][:1]
    raise SystemExit(main(args.market, args.a, args.b, args.n, args.conc,
                          list(args.shapes), args.groups.split(","), unis))