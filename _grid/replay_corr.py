# -*- coding: utf-8 -*-
"""replay_corr.py —— 用 PnL 相关矩阵重做「信号源」判定 + 组合增量闭式解验证

为什么重做
----------
11-15 那版用「字段集合 Jaccard」当机制指纹，mech_gate.py 据此判重。
replay_ds.py 第 4 段实测把这个判据推翻了：
    字段同源 20 条：两两 PnL corr 中位 0.2718，组合 Sharpe 4.176
    字段跨源 20 条：两两 PnL corr 中位 0.3309，组合 Sharpe 3.747
字段同源的 PnL 反而更分散。⇒ 字段集合不是相关性的代理，必须直接用 PnL。

本脚本四件事
------------
1. 全量 341×341 PnL 相关矩阵（固定窗口，pairwise complete）
2. 按 PnL corr 聚类，重新数「真正的信号源」有几个
3. 选股策略 A/B/C/D 对比：按 maxCorr 最低 / 按 Sharpe 最高 / 按字段最新 / 随机
4. 组合增量闭式解 vs 实测逐步对照（验证 ΔS 的预测能力）

用法
----
python _grid/replay_corr.py
python _grid/replay_corr.py --top 60      # 每组建仓条数
"""
import json, io, os, sys, math, random, collections
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CACHE = 'data/alpha_quality_analysis/pnl'
SUB = '_logs/submitted_full.json'
OUT = '_logs/replay'
os.makedirs(OUT, exist_ok=True)

ARGV = sys.argv[1:]
K = int(ARGV[ARGV.index('--top') + 1]) if '--top' in ARGV else 20
SEED = 20261115

def hr(t):
    print('\n' + '=' * 78); print(t); print('=' * 78)

subs = json.load(io.open(SUB, encoding='utf-8'))
meta = {x['id']: x for x in subs}
PNL = {}
for x in subs:
    p = os.path.join(CACHE, x['id'] + '.json')
    if not os.path.exists(p):
        continue
    try:
        s = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        continue
    if len(s) >= 250:
        PNL[x['id']] = s

ids = sorted(PNL.keys(), key=lambda a: (meta[a].get('dateSubmitted') or ''))
print('PnL 可用 %d 条' % len(ids))

# ---------- 构建宽表 ----------
df = pd.DataFrame({a: pd.Series(PNL[a], dtype='float64') for a in ids})
# 固定窗口：取多数 alpha 共有的区间（2019-01-03 ~ 2023-12-29 是主区间）
all_dates = sorted(df.index)
# 找「至少 80% alpha 都有数据」的连续区间
cov = df.notna().sum(axis=1) / len(ids)
good = [d for d in all_dates if cov[d] >= 0.8]
w0, w1 = good[0], good[-1]
print('固定窗口 %s ~ %s（%d 日，覆盖率≥80%%）' % (w0, w1, len(good)))
W = df.loc[w0:w1]
print('窗口内有效值比例 %.1f%%' % (100.0 * W.notna().sum().sum() / (len(W) * len(ids))))

# ---------- 1. 相关矩阵 ----------
hr('第 1 段  341×341 PnL 相关矩阵')
C = W.corr(min_periods=120)
print('相关矩阵 %d×%d，NaN 占比 %.1f%%' % (C.shape[0], C.shape[1], 100.0 * C.isna().sum().sum() / (C.size)))

# 每条的 max corr（排除自身）
np.fill_diagonal(C.values, np.nan)
mx = C.max(axis=0)
mx_who = C.idxmax(axis=0)
_mv = mx.dropna().values
print('\n全池 maxCorr 分布（对 341 条彼此）：')
for q in [10, 25, 50, 75, 90, 95]:
    print('  P%-3d %.4f' % (q, np.percentile(_mv, q)))
print('  min %.4f  max %.4f  mean %.4f' % (_mv.min(), _mv.max(), _mv.mean()))

# 平台 selfCorrelation 对照（时点值，不是全池）
plat = pd.Series({a: (meta[a].get('is') or {}).get('selfCorrelation') for a in ids}, dtype='float64')
print('\n平台 is.selfCorrelation 中位 %.4f' % plat.median())
print('全池 maxCorr 中位 %.4f（必然 ≥ 平台时点值，因为池更大）' % mx.median())

# ---------- 2. 按 PnL corr 聚类 ----------
hr('第 2 段  真正的信号源：按 PnL corr 聚类')
for th in [0.5, 0.6, 0.7, 0.75, 0.8, 0.85, 0.9]:
    n = len(ids)
    parent = list(range(n))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    M = C.values
    for i in range(n):
        for j in range(i + 1, n):
            v = M[i, j]
            if v == v and v >= th:
                ra, rb = find(i), find(j)
                if ra != rb:
                    parent[rb] = ra
    cl = collections.Counter(find(i) for i in range(n))
    sz = sorted(cl.values(), reverse=True)
    print('  相关>=%.2f  源数=%-3d  最大源=%-3d (%4.1f%%)  单条源=%-3d' % (
        th, len(cl), sz[0], 100.0 * sz[0] / n, sum(1 for x in sz if x == 1)))

# 用 0.7 做后续
TH = 0.7
n = len(ids); parent = list(range(n))
def find(a):
    while parent[a] != a:
        parent[a] = parent[parent[a]]; a = parent[a]
    return a
M = C.values
for i in range(n):
    for j in range(i + 1, n):
        v = M[i, j]
        if v == v and v >= TH:
            ra, rb = find(i), find(j)
            if ra != rb:
                parent[rb] = ra
groups = collections.defaultdict(list)
for i in range(n):
    groups[find(i)].append(ids[i])
pnl_clusters = sorted(groups.values(), key=len, reverse=True)
print('\n采用阈值 %.2f：源数 %d，最大源 %d 条，其成员 maxCorr 中位 %.4f' % (
    TH, len(pnl_clusters), len(pnl_clusters[0]),
    mx[[a for a in pnl_clusters[0] if a in mx.index]].median()))

# ---------- 3. 选股策略对比 ----------
hr('第 3 段  选股策略对比：建仓 %d 条，谁把组合 Sharpe 堆得最高' % K)

def combo_sharpe(members):
    sub = W[members]
    ser = sub.mean(axis=1, skipna=True).dropna()
    if len(ser) < 60:
        return None, 0
    m = ser.mean(); sd = ser.std(ddof=0)
    return (m / sd * math.sqrt(252)) if sd else None, len(ser)

def stats(members):
    s, n = combo_sharpe(members)
    selfs = [((meta[a].get('is') or {}).get('sharpe')) for a in members]
    selfs = [float(x) for x in selfs if x is not None]
    cs = []
    for i in range(len(members)):
        for j in range(i + 1, len(members)):
            v = C.loc[members[i], members[j]]
            if v == v:
                cs.append(v)
    return dict(s=s, n=n, self_med=np.median(selfs) if selfs else None,
                corr_med=np.median(cs) if cs else None)

# A: maxCorr 最低的 K 条
A = list(mx.sort_values().index[:K])
# B: 单条 Sharpe 最高的 K 条
B = sorted(ids, key=lambda a: -float((meta[a].get('is') or {}).get('sharpe') or 0))[:K]
# C: 每个 PnL 源各取 1 条，取前 K 个源（源内取 Sharpe 最高的那条）
Cset = []
for g in pnl_clusters[:K]:
    gg = sorted(g, key=lambda a: -float((meta[a].get('is') or {}).get('sharpe') or 0))
    Cset.append(gg[0])
Cset = Cset[:K]
# D: 随机
random.seed(SEED)
D = random.sample(ids, K)
# E: 字段跨源（沿用旧判据，做对照）
import re
F = json.load(io.open('data/alpha_quality_analysis/all_fields_usa_top3000.json', encoding='utf-8'))
toks = sorted([k for k in F if len(k) >= 3], key=len, reverse=True)
pat = re.compile(r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(t) for t in toks) + r')(?![A-Za-z0-9_])')
DROP = {'close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'cap', 'adv20',
        'sharesout', 'dividend', 'split', 'country', 'exchange', 'market', 'sector',
        'industry', 'subindustry', 'currency'}
fps = {}
for a in ids:
    code = (meta[a].get('regular') or {}).get('code') or ''
    fps[a] = set(m.group(1) for m in pat.finditer(code)) - DROP
n2 = len(ids); par2 = list(range(n2))
def find2(a):
    while par2[a] != a:
        par2[a] = par2[par2[a]]; a = par2[a]
    return a
for i in range(n2):
    if not fps[ids[i]]:
        continue
    for j in range(i + 1, n2):
        if not fps[ids[j]]:
            continue
        x, y = fps[ids[i]], fps[ids[j]]
        if len(x & y) / len(x | y) >= 0.5:
            ra, rb = find2(i), find2(j)
            if ra != rb:
                par2[rb] = ra
g2 = collections.defaultdict(list)
for i in range(n2):
    g2[find2(i)].append(ids[i])
fcl = sorted(g2.values(), key=len, reverse=True)
E = []
for g in fcl[:K]:
    gg = sorted(g, key=lambda a: -float((meta[a].get('is') or {}).get('sharpe') or 0))
    E.append(gg[0])
E = E[:K]

print('\n%-6s %-30s %8s %8s %9s %10s' % ('策略', '说明', '组合S', '单条S中位', '两两corr中位', 'n日'))
rows = []
for name, tag, grp in [('A', 'maxCorr 最低 %d 条' % K, A),
                       ('B', '单条 Sharpe 最高 %d 条' % K, B),
                       ('C', 'PnL 源各取1条 (%d 源)' % len(Cset), Cset),
                       ('D', '随机 %d 条' % K, D),
                       ('E', '字段源各取1条 (%d 源)' % len(E), E)]:
    st_ = stats(grp)
    rows.append((name, tag, st_))
    print('%-6s %-30s %8.3f %8.3f %9.4f %10d' % (
        name, tag, st_['s'] or 0, st_['self_med'] or 0, st_['corr_med'] or 0, st_['n']))

# 追加：A 策略的 maxCorr 均值
print('\n各策略成员的全池 maxCorr 中位：')
for name, tag, grp in [('A', '', A), ('B', '', B), ('C', '', Cset), ('D', '', D), ('E', '', E)]:
    v = mx[[a for a in grp if a in mx.index]]
    print('  %s  %.4f' % (name, v.median()))

# ---------- 4. 闭式解验证 ----------
hr('第 4 段  组合增量闭式解 vs 实测（逐步建仓，40 步）')

sub_ids = ids[::max(1, len(ids) // 40)][:40]

def sh(ser):
    ser = ser.dropna()
    if len(ser) < 60:
        return None
    m = ser.mean(); sd = ser.std(ddof=0)
    return (m / sd * math.sqrt(252)) if sd else None

print('  %3s %-10s %8s %8s %8s %8s %8s' % ('N', '新增', '实测S', '预测S', '误差', 'rho', '新条S'))
prev = None
recs = []
for k in range(1, len(sub_ids) + 1):
    members = sub_ids[:k]
    new = sub_ids[k - 1]
    ser_new = W[members].mean(axis=1, skipna=True).dropna()
    s_now = sh(ser_new)
    if prev is None:
        pred = None; rho = None; b = sh(W[new])
    else:
        old_members = sub_ids[:k - 1]
        ser_old = W[old_members].mean(axis=1, skipna=True).dropna()
        a = sh(ser_old); b = sh(W[new])
        idx = ser_old.index.intersection(W[new].dropna().index)
        if len(idx) < 120 or a is None or b is None:
            pred = None; rho = None
        else:
            x = ser_old.loc[idx].values; y = W[new].loc[idx].values
            rho = float(np.corrcoef(x, y)[0, 1])
            w = 1.0 / k
            # 用日收益的年化口径推：σ = |μ|/S × √252 关系不便直接算，用统计量
            mu_a, sd_a = x.mean(), x.std(ddof=0)
            mu_b, sd_b = y.mean(), y.std(ddof=0)
            mu_p = (1 - w) * mu_a + w * mu_b
            var_p = (1 - w) ** 2 * sd_a ** 2 + w ** 2 * sd_b ** 2 + 2 * w * (1 - w) * rho * sd_a * sd_b
            pred = mu_p / math.sqrt(var_p) * math.sqrt(252) if var_p > 0 else None
    err = (s_now - pred) if (pred is not None and s_now is not None) else None
    recs.append(dict(k=k, id=new, s=s_now, pred=pred, err=err, rho=rho, self_s=b))
    if k <= 10 or k % 5 == 0:
        print('  %3d %-10s %8.3f %8s %8s %8s %8s' % (
            k, new, s_now or 0,
            ('%.3f' % pred) if pred is not None else '    -',
            ('%+.4f' % err) if err is not None else '    -',
            ('%.4f' % rho) if rho is not None else '    -',
            ('%.3f' % b) if b is not None else '    -'))
    prev = s_now

ev = [abs(r['err']) for r in recs if r['err'] is not None]
pv = [r['err'] for r in recs if r['err'] is not None]
if ev:
    print('\n  闭式解误差：n=%d  |误差| 中位 %.4f  P90 %.4f  max %.4f' % (
        len(ev), np.median(ev), np.percentile(ev, 90), max(ev)))
    print('  带符号均值 %+.4f（正=实测高于预测）' % (sum(pv) / len(pv)))
    print('  误差 <=0.02 : %d/%d   <=0.05 : %d/%d' % (
        sum(1 for x in ev if x <= 0.02), len(ev), sum(1 for x in ev if x <= 0.05), len(ev)))

# 保存
json.dump(dict(
    w0=w0, w1=w1,
    maxcorr={a: (float(mx[a]) if mx[a] == mx[a] else None) for a in ids},
    clusters={str(i): g for i, g in enumerate(pnl_clusters[:40])},
    strategies=dict(A=A, B=B, C=Cset, D=D, E=E),
    strategy_stats=[(n_, t, s_) for n_, t, s_ in rows],
    closed_form=recs,
), io.open(os.path.join(OUT, 'corr_analysis.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('\n结果已存 %s/corr_analysis.json' % OUT)
