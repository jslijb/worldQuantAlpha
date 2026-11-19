from __future__ import annotations

import json
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor

from . import (baseline, composer, config, gates, idea_lib, judge, knowledge,
               ledger, queue, repair, report, sim, submit)
from .auth import AuthError, Brain
from .fielddb import FieldDB

DB = config.STATE_DIR / "state.db"


class State:
    def __init__(self, path=DB):
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS units(
              unit_id TEXT PRIMARY KEY, idea_id TEXT, market TEXT, shape TEXT, xop TEXT,
              params TEXT, expr TEXT, dataset TEXT, fields TEXT, alpha_id TEXT,
              metrics TEXT, verdict TEXT, attempt INTEGER, parent TEXT, created REAL);
            CREATE TABLE IF NOT EXISTS attempts(
              id INTEGER PRIMARY KEY AUTOINCREMENT, unit_id TEXT, codes TEXT,
              action TEXT, created REAL);
            """
        )
        self.conn.commit()

    def seen(self, unit_id: str) -> bool:
        cur = self.conn.execute("SELECT 1 FROM units WHERE unit_id=?", (unit_id,))
        return cur.fetchone() is not None

    def add(self, unit: dict, verdict: dict | None, alpha_id: str | None) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO units VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (unit["unit_id"], unit["idea_id"], unit["region"], unit.get("shape"),
             unit.get("xop"), json.dumps(unit.get("params")), unit["expr"],
             unit.get("dataset"), json.dumps(unit.get("fields")), alpha_id,
             json.dumps((verdict or {}).get("metrics")),
             json.dumps((verdict or {}).get("fail_codes")), unit.get("attempt", 1),
             unit.get("parent"), time.time()))
        self.conn.commit()

    def attempt(self, unit_id: str, codes: list, action: str) -> None:
        self.conn.execute("INSERT INTO attempts(unit_id,codes,action,created) VALUES(?,?,?,?)",
                          (unit_id, json.dumps(codes), action, time.time()))
        self.conn.commit()

    def history(self, idea_id: str) -> list[dict]:
        cur = self.conn.execute(
            "SELECT verdict, attempt FROM units WHERE idea_id=? ORDER BY created", (idea_id,))
        out = []
        for v, a in cur.fetchall():
            try:
                codes = json.loads(v or "[]")
            except Exception:
                codes = []
            out.append({"codes": codes, "attempt": a})
        return out

    def count(self) -> int:
        return self.conn.execute("SELECT COUNT(*) FROM units").fetchone()[0]


def _build_units(market: str, idea, matches: list[dict]) -> list[dict]:
    units = []
    idx = 0
    for match in matches[:2]:
        fields = [f["id"] for f in match["fields"]]
        for shape in idea.shapes:
            params = {"shape": shape, "n": config.WINDOWS_N[idx % len(config.WINDOWS_N)],
                      "g": config.GROUPS[idx % len(config.GROUPS)], "rel": "div"}

            expr = composer.compose(shape, fields[0], fields[1], params)
            settings = composer.choose_settings(market, config.UNIVERSES[market][0], idx)
            units.append({
                "unit_id": composer.unit_key(market, idea.idea_id, params, expr),
                "idea_id": idea.idea_id, "idea_kind": idea.kind, "region": market,
                "shape": shape, "params": params, "expr": expr,
                "dataset": match["dataset"], "fields": fields, "settings": settings,
                "xop": gates.operators.xop_of(expr), "attempt": 1,
            })
            idx += 1
    return units


def gate_filter(units: list[dict], fdb: FieldDB, market: str,
                used_fields: set, used_datasets: set) -> tuple[list[dict], list[dict]]:
    ok, rejected = [], []
    for u in units:
        o = gates.operators.check(u["expr"])
        if not o[0]:
            rejected.append({**u, "gate": o[1]})
            continue
        d = gates.depth.check(u["expr"])
        if not d[0]:
            rejected.append({**u, "gate": d[1]})
            continue
        a = gates.atom.atom_pass(u["expr"], market, fdb)
        if not a[0]:
            rejected.append({**u, "gate": a[1]})
            continue
        ds = a[1]["datasets"][0] if a[1].get("datasets") else u["dataset"]
        u["dataset"] = ds
        s = gates.dataset.dataset_pass(ds, market, used_datasets)
        if not s[0]:
            rejected.append({**u, "gate": s[1]})
            continue
        ok.append(u)
    return ok, rejected


def run_batch(brain: Brain, state: State, fdb: FieldDB, market: str, ideas: list,
              used_fields: set, used_datasets: set, limit: int = 4,
              live: bool = True) -> dict:
    sims = passed = 0
    for idea in ideas:
        if sims >= limit:
            break
        matches = fdb.match_roles(market, idea.roles, used_fields, used_datasets)
        if not matches:
            continue
        units = _build_units(market, idea, matches)
        good, rejected = gate_filter(units, fdb, market, used_fields, used_datasets)
        if rejected:
            knowledge.feed({"shape": rejected[0].get("shape"), "fail_codes": ["GATE_FAIL"],
                            "idea_kind": idea.kind})
        if not good:
            continue
        batch = good[:2]
        diversity_ok, dv = gates.diversity.check(batch, used_fields)
        if not diversity_ok and len(batch) > 1:
            batch = batch[:1]
        for unit in batch:
            if sims >= limit:
                break
            if state.seen(unit["unit_id"]):
                continue
            sims += 1
            if not live:
                state.add(unit, {"status": "DRY", "metrics": {}}, None)
                continue
            res = sim.run(brain, unit)
            if res.get("status") != "done":
                state.add(unit, {"status": "FATAL", "fail_codes": [str(res.get("http"))]}, None)
                continue
            v = judge.verdict(res.get("alpha") or {}, market,
                              extra={"shape": unit["shape"], "idea_kind": idea.kind})
            v["settings"] = unit["settings"]
            state.add(unit, v, res["alpha_id"])
            knowledge.feed(v)
            if v["status"] == "PASS_READY":
                passed += 1
                queue.enqueue(res["alpha_id"], unit, v.get("metrics") or {})
            else:
                act = repair.next_action(unit, v, state.history(idea.idea_id))
                state.attempt(unit["unit_id"], v.get("fail_codes") or [], act["kind"])
                _self_heal(brain, state, fdb, market, idea, unit, act, used_fields,
                           used_datasets, live)
            print("  " + unit["unit_id"][:34] + " " + report.detail(v), flush=True)
            used_fields.update(unit["fields"])
    return {"sims": sims, "passed": passed}


def _self_heal(brain, state, fdb, market, idea, unit, act, used_fields, used_datasets, live):
    if act["kind"] not in ("RESHAPE", "REGROUP", "RETUNE_DECAY_UP", "SWITCH_RELATION"):
        return
    params = dict(unit["params"])
    params.update(act.get("params") or {})
    fields = unit["fields"]
    expr = composer.compose(params.get("shape", unit["shape"]), fields[0], fields[1], params)
    settings = dict(unit["settings"])
    if act["kind"] == "RETUNE_DECAY_UP":
        settings = repair.apply_decay_step(settings, 1)
    nxt = {**unit, "params": params, "expr": expr, "settings": settings,
           "unit_id": composer.unit_key(market, idea.idea_id, params, expr),
           "attempt": unit.get("attempt", 1) + 1, "parent": unit["unit_id"]}
    ok, _ = gate_filter([nxt], fdb, market, used_fields, used_datasets)
    if not ok or state.seen(nxt["unit_id"]):
        return
    if not live:
        return
    res = sim.run(brain, nxt)
    if res.get("status") != "done":
        return
    v = judge.verdict(res.get("alpha") or {}, market,
                      extra={"shape": nxt["shape"], "idea_kind": idea.kind})
    v["settings"] = nxt["settings"]
    state.add(nxt, v, res["alpha_id"])
    knowledge.feed(v)
    if v["status"] == "PASS_READY":
        queue.enqueue(res["alpha_id"], nxt, v.get("metrics") or {})
    print("  ↳heal " + nxt["unit_id"][:30] + " " + report.detail(v), flush=True)


def drain_queue(brain: Brain) -> dict:
    out = {"submitted": 0, "rejected": 0, "queued": 0}
    quota = ledger.daily_count(config.today_east())
    room = config.DAILY_REGULAR_QUOTA - quota["regular"]
    if room <= 0:
        return out
    for item in queue.peek(day_target=str(config.today_bj()))[:room]:
        aid = item["alpha_id"]
        ok, pre = submit.precheck(brain, aid)
        if not ok:
            if pre.get("reason") == "CORR_HARD_BAND":
                out["queued"] += 1
                continue
            if pre.get("reason") == "CHECK_UNAVAILABLE":
                out["queued"] += 1
                continue
            queue.mark(aid, "rejected", pre.get("reason", ""))
            out["rejected"] += 1
            continue
        res = submit.submit(brain, aid)
        if res["result"] == "REJECTED":
            queue.mark(aid, "rejected", ",".join(res.get("fails") or []))
            out["rejected"] += 1
            continue
        if submit.confirm(brain, aid):
            alpha = brain.get_json(f"/alphas/{aid}") or {}
            is_ = alpha.get("is") or {}
            queue.mark(aid, "submitted")
            ledger.append({
                "id": aid, "expr": (item.get("unit_id") or ""), "S": is_.get("sharpe"),
                "F": is_.get("fitness"), "T": is_.get("turnover"),
                "R": is_.get("returns"), "DD": is_.get("drawdown"),
                "dateSubmitted": alpha.get("dateSubmitted"), "region": item.get("market"),
            })
            out["submitted"] += 1
        else:
            out["queued"] += 1
    return out


def main(rounds: int = 3, limit: int = 6, live: bool = True, market: str | None = None) -> int:
    brain = Brain()
    try:
        brain.login()
    except AuthError as exc:
        print("AUTH_ABORT", exc)
        return 2
    if not brain.authenticated:
        print("LOGIN_FAIL")
        return 2
    fdb = FieldDB()
    raw = baseline.fetch_alphas(brain)
    records = raw.get("records") or []
    print("ALPHAS_RAW", {"seen": raw.get("alphas_seen"), "parsed": len(records),
                         "complete": raw.get("complete")}, flush=True)
    state = State()
    total = {"sims": 0, "passed": 0, "submitted": 0}
    if market:
        markets = [market]
    elif config.USA_FALLBACK_ONLY:
        markets = list(config.MARKET_PRIORITY)
    else:
        markets = list(config.MARKET_PRIORITY_FULL)
    for rnd in range(1, rounds + 1):
        if submit.clock_gate():
            had = queue.stats().get("ready", 0)
            if had:
                d = drain_queue(brain)
                total["submitted"] += d["submitted"]
                report.line(rnd, "-", "DRAIN", total["sims"], total["passed"],
                            total["submitted"], ledger.daily_count(config.today_east()),
                            extra=f"rej={d['rejected']} hold={d['queued']}")
        for mkt in markets:
            fdb.load(mkt, config.UNIVERSES[mkt][0], brain)
            parsed = baseline.parse_region(fdb, mkt, records)
            used_fields = parsed["used_fields"]
            used_datasets = parsed["used_datasets"]
            print(f"BASE {mkt} used_fields={len(used_fields)} used_ds={len(used_datasets)} "
                  f"unmapped={parsed['unmapped_fields']}", flush=True)
            ideas = idea_lib.candidates(mkt, used_datasets)
            if not ideas:
                continue
            r = run_batch(brain, state, fdb, mkt, ideas, used_fields,
                          used_datasets, limit=limit, live=live)
            total["sims"] += r["sims"]
            total["passed"] += r["passed"]
            report.line(rnd, mkt, "BATCH", total["sims"], total["passed"],
                        total["submitted"], ledger.daily_count(config.today_east()),
                        extra=f"units={state.count()}")
            if total["sims"] >= config.SIM_DAILY:
                break
        time.sleep(config.ROUND_INTERVAL)
    print("TOTAL", total, "UNITS", state.count(), "QUEUE", queue.stats())
    return 0


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--rounds", type=int, default=3)
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--market", default=None)
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    raise SystemExit(main(rounds=args.rounds, limit=args.limit,
                          live=not args.dry, market=args.market))