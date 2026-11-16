# -*- coding: utf-8 -*-
"""
w200 日内主导组合批生成器（2026-09-19 凌晨）
背景诊断（见 .workbuddy/memory/2026-09-18.md 23:38 节）：
- 共享腿（引擎+标准PV）权重占比 ≥35% 的组合，真实 corr 必然 0.8+
- leg_lab 的 wp=2.0 会把组合推向 PV 主导 → 撞自己人
- 本批设计：日内/隔夜几何主导（池子 86 条无一此几何）+ 引擎腿 0.5 + 零标准PV腿
用法：python src/mine/mine_w200_intraday.py  → 落盘 _autologs/search_combos_w200.json
"""
import os, sys, json, csv, time, itertools, pathlib as pl
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
    # 日内/隔夜族（主腿）
    'P_on5':  G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
    'P_int20': G_EXPR('-ts_rank(close/open - 1, 20)'),
    'P_vd':   G_EXPR('(close - vwap)/vwap'),
    # 引擎腿（降权 0.5，唯一共享源）
    'L_cfo':  G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
    # 独有锚（0.75 辅助权）
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
MAINS = ['P_on5', 'P_int20', 'P_vd']
ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
ENGINE = 'L_cfo'

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

# ---------- 池子：只认台账；拉取失败必须报警（leg_lab 静默丢成员的教训） ----------
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
    print('⚠️ 以上成员不在池内，pred 会漏掉与它们的碰撞（rY07MXgd 教训）')

# ---------- 腿 PnL 装载 ----------
load = {}
for l in MAINS + ANCHORS + [ENGINE]:
    aid = cid2id(l)
    if not aid:
        print(f'⚠️ 腿 {l} 无 id'); continue
    p = get_pnl(aid)
    if not p:
        print(f'⚠️ 腿 {l} 无 PnL'); continue
    load[l] = p
legs = [l for l in MAINS + ANCHORS + [ENGINE] if l in load]
print(f'腿库 {len(legs)}: {" ".join(legs)}')

# 日期对齐（池 ∩ 腿）
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
G = Lraw @ Lraw.T / T
idx = {l: i for i, l in enumerate(legs)}

# ---------- 枚举组合 ----------
MIN_S = 2.2
cands = []
n_eval = 0
for k in range(1, len(MAINS) + 1):
    for mains in itertools.combinations(MAINS, k):
        # 主腿权重：首腿 2.0 或 1.5，次腿 1.5 或 1.0，三腿 1.0
        wschemes = []
        if k == 1:
            wschemes = [(2.0,), (1.5,)]
        elif k == 2:
            wschemes = [(2.0, 1.5), (2.0, 1.0), (1.5, 1.0)]
        else:
            wschemes = [(2.0, 1.5, 1.0), (2.0, 1.0, 1.0), (1.5, 1.0, 1.0)]
        for mw in wschemes:
            for na in range(0, 3):
                for extras in itertools.combinations(ANCHORS, na):
                    for eng in (True, False):
                        w = np.zeros(len(legs))
                        for l, wt in zip(mains, mw):
                            w[idx[l]] = wt
                        for x in extras:
                            w[idx[x]] = 0.75
                        if eng:
                            w[idx[ENGINE]] = 0.5
                        var = float(w @ G @ w)
                        if var <= 0:
                            continue
                        n_eval += 1
                        c = w @ Lraw
                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                        if S < MIN_S:
                            continue
                        cvec = (Mmat @ w) / (var ** .5)
                        mx = float(cvec.max())
                        tot = float(np.abs(w).sum())
                        shared = (0.5 if eng else 0.0) / tot
                        cands.append((S, mx, mains, mw, extras, eng, shared,
                                      pids[int(cvec.argmax())], w.copy()))

cands.sort(key=lambda t: (-t[0], t[1]))
print(f'评估 {n_eval}，S≥{MIN_S} 的 {len(cands)} 条')

# ---------- 选样：按主腿签名配额（每签名 ≤4 条），兄弟组合交给真实判决分高下 ----------
TAKE = 24
PER_SIG = 4
keep = []
sig_cnt = {}
for item in cands:
    sig = (tuple(item[2]), item[5])  # mains + engine 开关
    if sig_cnt.get(sig, 0) >= PER_SIG:
        continue
    keep.append(item)
    sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
    if len(keep) >= TAKE:
        break
print(f'配额选样：{len(cands)} → {len(keep)} 条（签名 {len(sig_cnt)} 个）')

COMB = {}
for i, (S, mx, mains, mw, extras, eng, shared, hit, w) in enumerate(keep):
    parts = []
    for l, wt in zip(mains, mw):
        parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
    for x in extras:
        parts.append(f'0.75*{EXPR[x]}')
    if eng:
        parts.append(f'0.5*{EXPR[ENGINE]}')
    expr = ' + '.join(parts)
    cid = f'w200_{i:02d}'
    COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                 'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                 'engine': eng, 'shared_frac': round(shared, 3)}
    print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} shared={shared:.2f} 撞{hit} | {expr[:130]}')

OUTP = '_autologs/search_combos_w200.json'
json.dump(COMB, open(OUTP, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'已落盘 {OUTP}（{len(COMB)} 条）')
