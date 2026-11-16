# -*- coding: utf-8 -*-
"""
w213 离线拼装（2026-09-20）：事件条件化 argmin 腿（帖 1 原意：回撤超阈值才发信号）。
框架同 mine_w210_assemble.py：主腿 + 独有锚 + 引擎（0.5/0.25/0），主腿占比≤0.45、shared≤0.12、pred≤0.63。
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
os.makedirs(PCACHE, exist_ok=True)

G_EXPR = lambda x: f'group_rank({x}, subindustry)'

EXPR = {
    'ev60a':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 60)'),
    'ev60b':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 0)'),
    'ev60nb':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0)'),
    'ev60db':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.15, ts_arg_min(returns, 60), 0)'),
    'ev120b':  G_EXPR('if_else(close/ts_delay(close, 120) - 1 < -0.15, ts_arg_min(returns, 120), 0)'),
    'ev20b':   G_EXPR('if_else(close/ts_delay(close, 20) - 1 < -0.07, ts_arg_min(returns, 20), 0)'),
    'evsum10': G_EXPR('if_else(ts_sum(returns, 10) < -0.10, -ts_arg_min(returns, 10), 0)'),
    'evh60a':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0)'),
    'evh60b':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, ts_arg_max(returns, 60), 0)'),
    'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
    'L_xr':        G_EXPR('fnd6_xrent/assets'),
    'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
    'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
    'M_intc':      G_EXPR('fnd6_intc/assets'),
    'M_g12':       G_EXPR('fnd6_newqv1300_glcea12/assets'),
    'M_debt':      G_EXPR('debt_st/assets'),
    'M_tstk':      G_EXPR('fnd6_tstkc/assets'),
    'M_accI':      G_EXPR('fn_accrued_liab_curr_a/assets'),
    'M_intI':      G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
    'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
}
MAINS = ['ev60a', 'ev60b', 'ev60nb', 'ev60db', 'ev120b', 'ev20b', 'evsum10', 'evh60a', 'evh60b']
ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
ENGINE = 'L_cfo'
MIN_S = float(os.environ.get('W213_MIN_S', '1.5'))
MAX_MAIN_FRAC = 0.45
MAX_SHARED = 0.12
MAX_PRED = 0.63
LEG_CID = {k: f'w213leg_{k}' for k in MAINS}
ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_xr': 'x180_leg_xr', 'L_int': 'x180_leg_int'}

def cid2id(cid):
    cands = [cid]
    if cid in LEG_CID:
        cands.append(LEG_CID[cid])
    if cid in ALIAS:
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
if missing:
    print('WARN 以上成员不在池内')

load = {}
noleg = []
for l in MAINS + ANCHORS + [ENGINE]:
    aid = cid2id(l)
    if not aid:
        noleg.append(l); continue
    p = get_pnl(aid)
    if not p:
        noleg.append(l); continue
    load[l] = p
print(f'腿库 {len(load)}/{len(MAINS+ANCHORS+[ENGINE])}；缺: {noleg}')

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

print('--- 单腿 vs 池子 max corr ---')
for m in MAINS:
    if m not in idx:
        continue
    cs = Mmat[:, idx[m]] / (Lraw[idx[m]].std(ddof=1) + 1e-12)
    print(f'  {m}: maxcorr={cs.max():.3f} hit={pids[int(cs.argmax())]}')

avail = [m for m in MAINS if m in load]
cands = []
n_eval = 0
for m in avail:
    for mw in (2.0, 1.5):
        for na in range(1, 4):
            for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                for aw in (0.75, 0.5):
                    for eng_w in (0.5, 0.25, 0.0):
                        w = np.zeros(len(names))
                        w[idx[m]] = mw
                        for x in extras:
                            w[idx[x]] = aw
                        if eng_w > 0:
                            w[idx[ENGINE]] = eng_w
                        tot = float(np.abs(w).sum())
                        main_frac = mw / tot
                        if main_frac > MAX_MAIN_FRAC:
                            continue
                        shared = eng_w / tot
                        if shared > MAX_SHARED:
                            continue
                        var = float(w @ Gm @ w)
                        if var <= 0:
                            continue
                        n_eval += 1
                        c = w @ Lraw
                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                        if S < MIN_S:
                            continue
                        cvec = (Mmat @ w) / (var ** .5)
                        mx = float(cvec.max())
                        if mx > MAX_PRED:
                            continue
                        cands.append((S, mx, m, mw, extras, aw, eng_w,
                                      main_frac, shared, pids[int(cvec.argmax())]))

cands.sort(key=lambda t: (-t[0], t[1]))
print(f'评估 {n_eval}，S>={MIN_S} 且 main_frac<={MAX_MAIN_FRAC} 且 pred<={MAX_PRED} 的 {len(cands)} 条')
for S, mx, m, mw, extras, aw, eng, mf, sh, hit in cands[:20]:
    print(f'  S={S:.2f} maxcorr={mx:.3f} main={m}({mw}) anchors={extras}(w{aw}) eng={eng} mainf={mf:.2f} hit={hit}')

OUTP = '_autologs/search_combos_w213.json'
COMB = {}
for i, (S, mx, m, mw, extras, aw, eng, mf, sh, hit) in enumerate(cands[:20]):
    parts = [f'{mw}*{EXPR[m]}'] + [f'{aw}*{EXPR[x]}' for x in extras]
    if eng > 0:
        parts.append(f'{eng}*{EXPR[ENGINE]}')
    COMB[f'w213_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3), 'maxcorr': round(mx, 4)}
json.dump(COMB, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已落盘 {OUTP}（{len(COMB)} 条）')
