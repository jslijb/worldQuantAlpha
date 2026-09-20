# -*- coding: utf-8 -*-
"""
w213c 加挂拼装（2026-09-20）：w210 已验证达标结构（2.0 主腿 + 双基本面锚 + 0.5 引擎）不动，
第 5 条腿加挂事件条件化腿（0.5/0.75），目标：corr 0.6968~0.7359 → <0.685，SF 保 4.0+。
"""
import os, json, csv, time, itertools, pathlib as pl
import numpy as np

_p = pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        os.chdir(_d); break

import requests

MINED = 'data/alpha_quality_analysis/mined'
PCACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

G_EXPR = lambda x: f'group_rank({x}, subindustry)'

EXPR = {
    'argshort10': G_EXPR('-ts_arg_min(returns, 10)'),
    'ev60a':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 60)'),
    'ev60nb':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0)'),
    'evh60a':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0)'),
    'evh60b':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, ts_arg_max(returns, 60), 0)'),
    'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
    'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
    'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
    'M_intc':      G_EXPR('fnd6_intc/assets'),
    'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
}
# w210 达标结构的锚权重（实测）
STRUCTS = {
    'A_E5pYLQPL': {'L_int': 1.5, 'M_intc': 0.75},
    'B_0mX95n5p': {'L_acc': 0.75, 'L_int': 0.75, 'M_lnoq': 0.75},
    'C_YPbnYzol': {'L_int': 1.5, 'M_lnoq': 0.75},
}
EVENTS = ['ev60a', 'ev60nb', 'evh60a', 'evh60b']
EWS = (0.75, 0.5)
LEG_CID = {'ev60a': 'w213leg_ev60a', 'ev60nb': 'w213leg_ev60nb',
           'evh60a': 'w213leg_evh60a', 'evh60b': 'w213leg_evh60b',
           'argshort10': 'w210leg_argshort10'}
ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_int': 'x180_leg_int', 'L_acc': 'x180_leg_acc',
         'M_intc': None, 'M_lnoq': None}

def cid2id(cid):
    cands = [cid]
    if cid in LEG_CID:
        cands.append(LEG_CID[cid])
    if cid in ALIAS and ALIAS[cid]:
        cands.append(ALIAS[cid])
    for base in cands:
        p = pl.Path(MINED) / f'{base}.json'
        if p.exists():
            d = json.load(open(p, encoding='utf-8'))
            if d.get('id'):
                return d['id']
    for h in pl.Path(MINED).glob('*.json'):
        try:
            d = json.load(open(h, encoding='utf-8'))
        except Exception:
            continue
        if d.get('_cid') == cid and d.get('id'):
            return d['id']
    return None

_S = None
def sess():
    s = requests.Session()
    s.auth = tuple(json.load(open('brain_credentials.txt')))
    assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201
    return s

def get_pnl(aid):
    cp = pl.Path(PCACHE) / f'{aid}.json'
    if cp.exists():
        try:
            return json.load(open(cp, encoding='utf-8'))
        except Exception:
            pass
    global _S
    if _S is None:
        _S = sess()
    for _ in range(6):
        try:
            r = _S.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            time.sleep(5); continue
        if r.status_code != 200 or r.headers.get('Retry-After'):
            time.sleep(float(r.headers.get('Retry-After') or 4)); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(3); continue
        recs = sorted((str(x[0]), float(x[1])) for x in (j.get('records') or [])
                      if len(x) >= 2 and x[1] is not None)
        if len(recs) < 60:
            time.sleep(3); continue
        ser = {recs[k][0]: recs[k][1] - recs[k - 1][1] for k in range(1, len(recs))}
        json.dump(ser, open(cp, 'w', encoding='utf-8'))
        return ser
    return None

pool = {}
missing = []
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if row and len(row[0]) == 8 and row[0].isalnum() and row[0] not in pool:
        v = get_pnl(row[0])
        if v:
            pool[row[0]] = v
        else:
            missing.append(row[0])
print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')

need = ['argshort10'] + EVENTS + list(EXPR)[5:]
load = {}
noleg = []
for l in need:
    aid = cid2id(l)
    if not aid:
        noleg.append(l); continue
    p = get_pnl(aid)
    if not p:
        noleg.append(l); continue
    load[l] = p
print(f'腿库 {len(load)}/{len(need)}；缺: {noleg}')
assert not noleg, noleg

dates = None
for ps in list(pool.values()) + list(load.values()):
    ds = set(ps)
    dates = ds if dates is None else (dates & ds)
dates = sorted(dates)
T = len(dates)
print(f'对齐日期 {T} 天')
assert T >= 400

Lraw = np.vstack([[load[l][d] for d in dates] for l in load])
names = list(load)
pids = list(pool)
Pm = np.vstack([[pool[q][d] for d in dates] for q in pids])
Pm = Pm - Pm.mean(axis=1, keepdims=True)
Psd = Pm.std(axis=1, ddof=1, keepdims=True); Psd[Psd == 0] = 1
Pz = Pm / Psd
Mmat = Pz @ Lraw.T / T
Gm = Lraw @ Lraw.T / T
idx = {l: i for i, l in enumerate(names)}

rows = []
for sname, anchors in STRUCTS.items():
    for ev in EVENTS:
        if ev not in idx:
            continue
        for ew in EWS:
            w = np.zeros(len(names))
            w[idx['argshort10']] = 2.0
            for a, aw in anchors.items():
                w[idx[a]] += aw
            w[idx[ev]] = ew
            w[idx['L_cfo']] = 0.5
            tot = float(np.abs(w).sum())
            var = float(w @ Gm @ w)
            if var <= 0:
                continue
            c = w @ Lraw
            S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
            cvec = (Mmat @ w) / (var ** .5)
            mx = float(cvec.max())
            hit = pids[int(cvec.argmax())]
            rows.append((S, mx, sname, ev, ew, hit, tot))
            print(f'  {sname} +{ev}(w{ew}): S={S:.2f} pred={mx:.3f} hit={hit}')

rows.sort(key=lambda r: (-r[0], r[1]))
OUTP = '_autologs/search_combos_w213c.json'
COMB = {}
for i, (S, mx, sname, ev, ew, hit, tot) in enumerate(rows):
    parts = [f'2.0*{EXPR["argshort10"]}']
    for a, aw in STRUCTS[sname].items():
        parts.append(f'{aw}*{EXPR[a]}')
    parts.append(f'{ew}*{EXPR[ev]}')
    parts.append(f'0.5*{EXPR["L_cfo"]}')
    COMB[f'w213c_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3),
                              'maxcorr': round(mx, 4), 'struct': sname, 'ev': ev, 'ew': ew}
json.dump(COMB, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已落盘 {OUTP}（{len(COMB)} 条）')
