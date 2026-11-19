from __future__ import annotations

import time

from . import config, queue


def line(round_no: int, market: str, action: str, sims: int, passed: int,
         submitted: int, quota: dict, extra: str = "") -> str:
    s = queue.stats()
    q = f"{quota.get('regular', 0)}/{config.DAILY_REGULAR_QUOTA}"
    msg = (f"[{time.strftime('%H:%M:%S')}] R{round_no} | {market:<4} | {action:<12} | "
           f"sims={sims} pass={passed} submit={submitted} quota={q} "
           f"queue={s.get('ready', 0)}")
    if extra:
        msg += f" | {extra}"
    print(msg, flush=True)
    return msg


def detail(verdict: dict) -> str:
    m = verdict.get("metrics") or {}
    codes = ",".join(verdict.get("fail_codes") or []) or "PASS"
    return f"S={m.get('S')} F={m.get('F')} TO={m.get('TO')} {codes}"