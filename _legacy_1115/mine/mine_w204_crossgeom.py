# -*- coding: utf-8 -*-
"""
w204 跨几何组合批（2026-09-19）
主腿 P_int10 系（含换几何版）+ 换几何锚（industry/市值桶/波动率桶）。
目标：与 zq8Xeo2R（P_int10+subindustry 锚）、3qXd5vg0（P_int20+subindustry 锚）去相关。
标定：shared<=0.10 偏移 -0.03~+0.05 → pred<=0.65 才有 real<=0.685 机会。
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

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

EXPR = {
    'P_int10':  G('-ts_rank(close/open - 1, 10)'),
    'P_int5':   G('-ts_rank(close/open - 1, 5)'),
    'P_int15':  G('-ts_rank(close/open - 1, 15)'),
    'P_int30':  G('-ts_rank(close/open - 1, 30)'),
    'P_int10I': GI('-ts_rank(close/open - 1, 10)'),
    'P_int10C': GC('-ts_rank(close/open - 1, 10)'),
    'P_int10V': GV('-ts_rank(close/open - 1, 10)'),
    'A_xr_I':   GI('fnd6_xrent/assets'),
    'A_xr_C':   GC('fnd6_xrent/assets'),
    'A_xr_V':   GV('fnd6_xrent/assets'),
    'A_intc_I': GI('fnd6_intc/assets'),
    'A_intc_C': GC('fnd6_intc/assets'),
    'A_debt_I': GI('debt_st/assets'),
    'A_acc_I':  GI('fn_accrued_liab_curr_a/assets'),
    'A_int_I':  GI('-annual_intangible_assets_net_carrying_value/assets'),
    'A_lnoq_I': GI('fnd6_newqv1300_lnoq/assets'),
    'A_g12_I':  GI('fnd6_newqv1300_glcea12/assets'),
}
MAINS = ['P_int10', 'P_int5', 'P_int15', 'P_int30', 'P_int10I', 'P_int10C', 'P_int10V']
ANCHORS = ['A_xr_I', 'A_xr_C', 'A_xr_V', 'A_intc_I', 'A_intc_C',
           'A_debt_I', 'A_acc_I', 'A_int_I', 'A_lnoq_I', 'A_g12_I']
MIN_S = 2.0
MAX_SHARED = 0.0    # 不带引擎腿/共享腿，全独有成分
MAX_PRED = 0.65
MAIN_W = [2.0, 1.5, 1.25]
ANCH_W = [1.0, 0.75, 0.5]
ALIAS = {'P_int10': 'w203leg_P_int10', 'P_int20': 'x180_leg_int'}

def cid2id(cid):
    for base in (f'{cid}',):
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
    print('WARN 以上成员不在池内，pred 会漏掉与它们的碰撞')

load = {}
for l in MAINS + ANCHORS:
    aid = cid2id(l)
    if not aid:
        print(f'WARN 腿 {l} 无 id'); continue
    p = get_pnl(aid)
    if not p:
        print(f'WARN 腿 {l} 无 PnL'); continue
    load[l] = p
legs = [l for l in MAINS + ANCHORS if l in load]
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

cands = []
n_eval = 0
for mains in MAINS:
    if mains not in load:
        continue
    for mw in MAIN_W:
        for na in range(2, 5):
            for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                for aw in ANCH_W:
                    w = np.zeros(len(legs))
                    w[idx[mains]] = mw
                    for x in extras:
                        w[idx[x]] = aw
                    tot = float(np.abs(w).sum())
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
                    cands.append((S, mx, mains, mw, extras, aw,
                                  pids[int(cvec.argmax())], w.copy()))

cands.sort(key=lambda t: (-t[0], t[1]))
print(f'评估 {n_eval}，S>={MIN_S} 且 shared=0 且 pred<={MAX_PRED} 的 {len(cands)} 条')

TAKE = 16
PER_SIG = 3
keep = []
sig_cnt = {}
for item in cands:
    sig = (item[2], tuple(item[4]))
    if sig_cnt.get(sig, 0) >= PER_SIG:
        continue
    keep.append(item)
    sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
    if len(keep) >= TAKE:
        break
print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

COMB = {}
for i, (S, mx, mains, mw, extras, aw, hit, w) in enumerate(keep):
    parts = []
    parts.append(f'{mw}*{EXPR[mains]}' if mw != 1 else EXPR[mains])
    for x in extras:
        parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
    expr = ' + '.join(parts)
    cid = f'w204_{i:02d}'
    COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                 'nearest': hit, 'mains': [mains], 'anchors': list(extras),
                 'engine': False, 'shared_frac': 0}
    print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} hit={hit} | {expr[:110]}')

OUTP = '_autologs/search_combos_w204.json'
json.dump(COMB, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已落盘 {OUTP}（{len(COMB)} 条）')
