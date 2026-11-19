from __future__ import annotations

import argparse
import threading
from concurrent.futures import ThreadPoolExecutor

from . import composer, config, gates, judge, queue
from .auth import Brain
from .fielddb import FieldDB
from .sim import run


def build_settings(market, universe, neut, decay):
    s = composer.choose_settings(market, universe, 0)
    s["neutralization"] = neut
    s["decay"] = decay
    return s


def main(market: str, a: str, b: str, n: int, shape: str, conc: int,
         groups: list[str], neuts: list[str], decays: list[int], universe: str) -> int:
    brain = Brain()
    brain.login()
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    fdb.load(market, universe)
    ok_a, d_a = gates.atom.atom_pass(f"({a} / {b})", market, fdb)
    if not ok_a:
        print("ATOM_FAIL", d_a)
        return 3
    ds = d_a["datasets"][0]
    tasks = [(g, nt, dc) for nt in neuts for dc in decays for g in groups]
    print(f"PAIR {a}/{b} ds={ds} shape={shape} n={n} tasks={len(tasks)}", flush=True)
    lock = threading.Lock()
    results = []

    def work(t):
        g, nt, dc = t
        params = {"shape": shape, "n": n, "n2": n, "g": g, "rel": "div"}
        expr = composer.compose(shape, a, b, params)
        ok_o, _ = gates.operators.check(expr)
        ok_d, d_d = gates.depth.check(expr)
        if not (ok_o and ok_d):
            with lock:
                print(f"[{g}/{nt}/d{dc}] GATE {d_d.get('reason')}", flush=True)
            return None
        unit = {"unit_id": f"sn_{abs(hash(expr + nt + str(dc))) % 10**10}",
                "idea_id": f"{a}__{b}", "region": market, "shape": shape,
                "params": params, "expr": expr, "dataset": ds, "fields": [a, b],
                "settings": build_settings(market, universe, nt, dc)}
        res = run(brain, unit)
        if res.get("status") != "done":
            with lock:
                print(f"[{g}/{nt}/d{dc}] ERR {str(res.get('body'))[:150]}", flush=True)
            return None
        v = judge.verdict(res.get("alpha") or {}, market)
        m = v.get("metrics") or {}
        with lock:
            print(f"[{g}/{nt}/d{dc}] {res['alpha_id']} S={m.get('S')} F={m.get('F')} "
                  f"TO={m.get('TO')} {'PASS' if v['status'] == 'PASS_READY' else 'fail'}",
                  flush=True)
        if v["status"] == "PASS_READY":
            queue.enqueue(res["alpha_id"], unit, m)
        return v

    with ThreadPoolExecutor(max_workers=conc) as ex:
        for r in ex.map(work, tasks):
            if r:
                results.append(r)
    best = max(results, key=lambda r: (r.get("metrics") or {}).get("S") or -9, default=None)
    if best:
        print("BEST", best.get("alpha_id"), best.get("metrics"))
    print("SCAN_DONE", len(results), "pass", sum(1 for r in results if r["status"] == "PASS_READY"))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--market", default="GLB")
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--n", type=int, default=60)
    ap.add_argument("--shape", default="A")
    ap.add_argument("--conc", type=int, default=2)
    ap.add_argument("--groups", default="industry,sector")
    ap.add_argument("--neuts", default="SUBINDUSTRY,INDUSTRY,MARKET,STATISTICAL")
    ap.add_argument("--decays", default="0,20")
    ap.add_argument("--universe", default="")
    args = ap.parse_args()
    uni = args.universe or config.UNIVERSES[args.market][0]
    raise SystemExit(main(args.market, args.a, args.b, args.n, args.shape, args.conc,
                          args.groups.split(","), args.neuts.split(","),
                          [int(x) for x in args.decays.split(",")], uni))