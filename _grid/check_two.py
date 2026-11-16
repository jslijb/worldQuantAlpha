# -*- coding: utf-8 -*-
"""check_two.py — 对指定 alpha id 拉平台 /check，打印 SELF/PROD corr 真值"""
import sys, os, json, time
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.core.session import Brain

API = 'https://api.worldquantbrain.com'
ids = sys.argv[1:]


def poll(aid, tries=6, gap=12):
    s = Brain().s
    for i in range(tries):
        try:
            r = s.get(f'{API}/alphas/{aid}/check', timeout=40)
        except Exception as e:
            print(f'  [{aid}] try{i} EXC {e}')
            time.sleep(gap); continue
        if r.status_code != 200:
            print(f'  [{aid}] try{i} HTTP {r.status_code} {r.text[:120]}')
            time.sleep(gap); continue
        txt = r.text.strip()
        if not txt:
            print(f'  [{aid}] try{i} 空body')
            time.sleep(gap); continue
        try:
            d = r.json()
        except Exception:
            print(f'  [{aid}] try{i} 非JSON: {txt[:120]}')
            time.sleep(gap); continue
        chk = d.get('is', {}).get('checks') or d.get('checks') or []
        if not isinstance(chk, list) or not chk:
            print(f'  [{aid}] try{i} 无checks字段, keys={list(d.keys())[:8]}')
            time.sleep(gap); continue
        got = {}
        done = 0
        for c in chk:
            n = c.get('name'); res = c.get('result'); val = c.get('value')
            if n in ('SELF_CORRELATION', 'PROD_CORRELATION', 'DATA_DIVERSITY', 'REGULAR_SUBMISSION', 'OLD_SIMULATION'):
                got[n] = (res, val)
                if res not in (None, 'PENDING'):
                    done += 1
        print(f'  [{aid}] try{i} 关键门: ' + ' | '.join(f'{k}={v[0]}({v[1]})' for k, v in got.items()))
        if done >= 2:
            fails = [c.get('name') for c in chk if c.get('result') == 'FAIL']
            print(f'  [{aid}] >>> 全量FAIL: {fails}')
            return d
        time.sleep(gap)
    return None


for aid in ids:
    print('=' * 90)
    print('check', aid)
    poll(aid)
