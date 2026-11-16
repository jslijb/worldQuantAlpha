# -*- coding: utf-8 -*-
"""
w208 未开采主腿批（2026-09-19）：w200 的 2016 组合里 P_on5/P_vd 主腿从未被模拟（配额被 P_int20 占满）。
新约束（本周实测标定）：主腿占比 <=0.45（占比高 → 偏移失控，w206 教训）、pred<=0.63。
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
    'P_on5':  G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
    'P_on20': G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 20)'),
    'P_vd':   G_EXPR('(close - vwap)/vwap'),
    'P_vd5':  G_EXPR('ts_mean((close - vwap)/vwap, 5)'),
    'P_int20': G_EXPR('-ts_rank(close/open - 1, 20)'),
    'L_cfo':  G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
    'L_xr':   G_EXPR('fnd6_xrent/assets'),
    'L_int':  G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
    'L_acc':  G_EXPR('fn_accrued_liab_curr_a/assets'),
    'M_intc': G_EXPR('fnd6_intc/assets'),
    'M_g12':  G_EXPR('fnd6_newqv1300_glcea12/assets'),
    'M_debt': G_EXPR('debt_st/assets'),
    'M_tstk': G_EXPR('fnd6_tstkc/assets'),
    'M_accI': G_EXPR('fn_accrued_liab_curr_a/assets'),
    'M_intI': G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
    'M_lnoq': G_EXPR('fnd6_newqv1300_lnoq/assets'),
}
MAINS = ['P_on5', 'P_on20', 'P_vd', 'P_vd5', 'P_int20']
ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
ENGINE = 'L_cfo'
MIN_S = 2.0
MAX_MAIN_FRAC = 0.45
MAX_SHARED = 0.12
MAX_PRED = 0.63
ALIAS = {'P_int20': 'x180_leg_int'}

def cid2id(cid):
    if cid in ALIAS:
        p = pl.Path(MINED) / f'{ALIAS[cid]}.json'
        if p.exists():
            d = json.load(open(p, encoding='utf-8'))
            if d.get('id'):
                return d['id']
    if len(cid) == 8 and cid.isalnum():
        return cid
    p = pl.Path(MINED) / f'{cid}.json'
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
for l in MAINS + ANCHORS + [ENGINE]:
    aid = cid2id(l)
    if not aid:
        print(f'WARN 腿 {l} 无 id'); continue
    p = get_pnl(aid)
    if not p:
        print(f'WARN 腿 {l} 无 PnL'); continue
    load[l] = p
legs = [l for l in MAINS + ANCHORS + [ENGINE] if l in load]
print(f'腿库 {len(legs)}: {" ".join(legs)}')

dates = None
for ps in list(pool.values()) + list(load.values()):
    ds = set(ps)
    dates = ds if dates is None else (dates & ds)
dates = sorted(dates)
T = len(dates)
print(f'对齐日期 {T} 天')
assert T >= 400

Lraw = np.vstack([[load[l][d] for d in dates] for l in legs])
pids = list(pool)
Pm = np.vstack([[pool[q][d] for d in dates] for q in pids])
Pm = Pm - Pm.mean(axis=1, keepdims=True)
Psd = Pm.std(axis=1, ddof=1, keepdims=True); Psd[Psd == 0] = 1
Pz = Pm / Psd
Mmat = Pz @ Lraw.T / T
Gm = Lraw @ Lraw.T / T
idx = {l: i for i, l in enumerate(legs)}

avail = [m for m in MAINS if m in load]
cands = []
n_eval = 0
for k in range(1, 3):
    for mains in itertools.combinations(avail, k):
        if k == 1:
            wschemes = [(2.0,), (1.5,)]
        else:
            wschemes = [(1.5, 1.0), (1.5, 1.5), (2.0, 1.0)]
        for mw in wschemes:
            for na in range(1, 4):
                for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                    for aw in (0.75, 0.5):
                        for eng in (True, False):
                            w = np.zeros(len(legs))
                            for l, wt in zip(mains, mw):
                                w[idx[l]] = wt
                            for x in extras:
                                w[idx[x]] = aw
                            ew = 0.5 if eng else 0.0
                            if eng:
                                w[idx[ENGINE]] = ew
                            tot = float(np.abs(w).sum())
                            main_frac = mw[0] / tot
                            if main_frac > MAX_MAIN_FRAC:
                                continue
                            shared = ew / tot
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
                            cands.append((S, mx, mains, mw, extras, aw, eng,
                                          main_frac, shared, pids[int(cvec.argmax())], w.copy()))

cands.sort(key=lambda t: (-t[0], t[1]))
print(f'评估 {n_eval}，S>={MIN_S} 且 main_frac<={MAX_MAIN_FRAC} 且 pred<={MAX_PRED} 的 {len(cands)} 条')

TAKE = 12
PER_SIG = 3
keep = []
sig_cnt = {}
for item in cands:
    sig = (tuple(item[2]), item[6])
    if sig_cnt.get(sig, 0) >= PER_SIG:
        continue
    keep.append(item)
    sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
    if len(keep) >= TAKE:
        break
print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

COMB = {}
for i, (S, mx, mains, mw, extras, aw, eng, mfrac, shared, hit, w) in enumerate(keep):
    parts = []
    for l, wt in zip(mains, mw):
        parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
    for x in extras:
        parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
    if eng:
        parts.append(f'0.5*{EXPR[ENGINE]}')
    expr = ' + '.join(parts)
    cid = f'w208_{i:02d}'
    COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                 'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                 'engine': eng, 'shared_frac': round(shared, 3), 'main_frac': round(mfrac, 3)}
    print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} mainf={mfrac:.2f} shared={shared:.2f} hit={hit} | {expr[:110]}')

OUTP = '_autologs/search_combos_w208.json'
json.dump(COMB, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已落盘 {OUTP}（{len(COMB)} 条）')
