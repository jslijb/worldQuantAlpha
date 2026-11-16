# -*- coding: utf-8 -*-
"""replay_vf.py —— 反解「纳入门槛」，并算 VF 真正看的那个数

两个问题
--------
Q1. 组合already 4.x，新加一条还要不要？
    等权加入第 N 条（权重 w=1/N）后 Sharpe 变高的条件，可解析反解为对新条 corr 的上限 rho*。
    rho* 与 a（现有组合 Sharpe）、b（新条 Sharpe）、sigma 比有关；w 小时 rho* ≈ b/a。
    => 「纳入门槛 b > rho·a」这条经验公式，本脚本给出严格推导与数值校验。

Q2. VF 看的是「前 3 个月提交的 Alpha 的组合表现」，我们那个数是多少？
    按提交日期分桶，算每桶内部等权组合的 Sharpe，看趋势。

用法
----
python _grid/replay_vf.py
"""
import json, io, os, sys, math, collections
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CACHE = 'data/alpha_quality_analysis/pnl'
SUB = '_logs/submitted_full.json'
OUT = '_logs/replay'

def hr(t):
    print('\n' + '=' * 78); print(t); print('=' * 78)

subs = json.load(io.open(SUB, encoding='utf-8'))
meta = {x['id']: x for x in subs}
PNL = {}
for x in subs:
    p = os.path.join(CACHE, x['id'] + '.json')
    if os.path.exists(p):
        try:
            s = json.load(io.open(p, encoding='utf-8'))
            if len(s) >= 250:
                PNL[x['id']] = s
        except Exception:
            pass
ids = sorted(PNL.keys(), key=lambda a: (meta[a].get('dateSubmitted') or ''))
df = pd.DataFrame({a: pd.Series(PNL[a], dtype='float64') for a in ids})
cov = df.notna().sum(axis=1) / len(ids)
good = [d for d in sorted(df.index) if cov[d] >= 0.8]
w0, w1 = good[0], good[-1]
W = df.loc[w0:w1]
print('PnL %d 条，窗口 %s ~ %s' % (len(ids), w0, w1))


def sh(ser):
    ser = ser.dropna()
    if len(ser) < 60:
        return None
    m = ser.mean(); sd = ser.std(ddof=0)
    return (m / sd * math.sqrt(252)) if sd else None


# ================================================================
# Q1  纳入门槛 rho* 的严格推导与数值校验
# ================================================================
hr('Q1  纳入门槛：新条与现有组合的相关必须低于多少，组合 Sharpe 才不降')

print('''推导（等权，旧组合权重 1-w，新条权重 w=1/N）：
  设 k_a=mu_a/sigma_a, k_b=mu_b/sigma_b, t=sigma_b/sigma_a
  S_p > S_a  等价于
      rho  <  b/a  +  (b^2-a^2)/(2*a^2) * (w/(1-w)) * t
  w 很小时第二项趋 0，退化为   rho* = b/a
''')


def rho_star(a, b, w, t=1.0):
    if a <= 0:
        return None
    return b / a + (b * b - a * a) / (2 * a * a) * (w / (1 - w)) * t


print('  数值：现有组合 a=4.125（本账号 40 条等权实测），单条 b 不同取值')
print('  %8s %10s %12s %14s' % ('b', 'w=1/50', 'w=1/200', 'w->0 (b/a)'))
for b in [1.5, 2.0, 2.3, 2.7, 3.0, 3.5, 4.0]:
    print('  %8.2f %10.4f %12.4f %14.4f' % (
        b, rho_star(4.125, b, 1 / 50), rho_star(4.125, b, 1 / 200), b / 4.125))

print('\n  反过来：给定典型单条 b=2.3，现有组合 a 从 2.0 涨到 5.0，门槛怎么涨')
print('  %8s %10s' % ('a', 'rho* (w=1/100)'))
for a in [2.0, 2.5, 3.0, 3.5, 4.0, 4.125, 4.5, 5.0]:
    print('  %8.2f %10.4f' % (a, rho_star(a, 2.3, 1 / 100)))

# 数值校验：用真实 PnL 造一对，验证 rho* 是否真的在边界
print('\n  数值校验（用真实 PnL 验边界）：取池内两条，按 a/b/w 构造并检查实际 ΔS 符号')
cand = []
for i in range(len(ids)):
    for j in range(0, len(ids), 37):     # 稀疏取样
        if i == j:
            continue
        x = W[ids[i]].dropna(); y = W[ids[j]].dropna()
        idx = x.index.intersection(y.index)
        if len(idx) < 400:
            continue
        xv = x.loc[idx].values; yv = y.loc[idx].values
        sa = xv.mean() / xv.std(ddof=0) * math.sqrt(252)
        sb = yv.mean() / yv.std(ddof=0) * math.sqrt(252)
        rho = float(np.corrcoef(xv, yv)[0, 1])
        if sa < 0 or sb < 0:
            continue
        # 以 a=sa（单条当作"旧组合"），b=sb
        w = 0.10
        mu = (1 - w) * xv.mean() + w * yv.mean()
        sd = math.sqrt((1 - w) ** 2 * xv.var(ddof=0) + w ** 2 * yv.var(ddof=0)
                       + 2 * w * (1 - w) * rho * xv.std(ddof=0) * yv.std(ddof=0))
        sp = mu / sd * math.sqrt(252)
        rs = rho_star(sa, sb, w, t=yv.std(ddof=0) / xv.std(ddof=0))
        cand.append((sa, sb, rho, rs, sp - sa))
        if len(cand) >= 400:
            break
    if len(cand) >= 400:
        break

if cand:
    ok = sum(1 for sa, sb, rho, rs, ds in cand
             if rs is not None and ((rho < rs) == (ds > 0)))
    print('    样本 %d 对，门槛预测与实际 ΔS 符号一致 %d 对（%.1f%%）' % (len(cand), ok, 100.0 * ok / len(cand)))
    bad = [(sa, sb, rho, rs, ds) for sa, sb, rho, rs, ds in cand
           if rs is not None and ((rho < rs) != (ds > 0))]
    if bad:
        print('    不一致样例（预测 vs 实际）：')
        for sa, sb, rho, rs, ds in bad[:5]:
            print('      a=%.2f b=%.2f rho=%.4f rho*=%.4f 实际ΔS=%+.4f' % (sa, sb, rho, rs, ds))

# ================================================================
# Q2  VF 真正看的数：近 3 个月提交的组合表现
# ================================================================
hr('Q2  VF 的 (a)：近 3 个月提交 Alpha 的组合 Sharpe（按提交季度分桶）')

buckets = collections.defaultdict(list)
for a in ids:
    d = (meta[a].get('dateSubmitted') or '')[:10]
    if not d:
        continue
    buckets[d[:7]].append(a)

print('  %-9s %4s %9s %9s %9s %9s %9s' % ('月份', '条数', '单条S中位', '组合S', '两两corr中位', 'maxCorr中位', 'selfCorr中位'))
for m in sorted(buckets):
    g = buckets[m]
    if len(g) < 3:
        print('  %-9s %4d %9s %9s %9s %9s %9s' % (m, len(g), '-', '-', '-', '-', '-'))
        continue
    s_self = [float((meta[a].get('is') or {}).get('sharpe') or 'nan') for a in g]
    s_self = [x for x in s_self if x == x]
    sc = sh(W[g].mean(axis=1, skipna=True))
    cs = []
    for i in range(len(g)):
        for j in range(i + 1, len(g)):
            v = W[g[i]].corr(W[g[j]])
            if v == v:
                cs.append(v)
    # maxCorr 全池
    mc = []
    for a in g:
        row = W.corrwith(W[a])
        row = row.drop(a, errors='ignore').dropna()
        if len(row):
            mc.append(row.max())
    scr = [float((meta[a].get('is') or {}).get('selfCorrelation') or 'nan') for a in g]
    scr = [x for x in scr if x == x]
    print('  %-9s %4d %9.3f %9.3f %9.4f %9.4f %9.4f' % (
        m, len(g), np.median(s_self) if s_self else 0, sc or 0,
        np.median(cs) if cs else 0, np.median(mc) if mc else 0, np.median(scr) if scr else 0))

print('\n  --- 近 3 个月（2026-08-15 之后）作为一个整体 ---')
recent = [a for a in ids if (meta[a].get('dateSubmitted') or '')[:10] >= '2026-08-15']
if recent:
    sc = sh(W[recent].mean(axis=1, skipna=True))
    ss = [float((meta[a].get('is') or {}).get('sharpe') or 'nan') for a in recent]
    ss = [x for x in ss if x == x]
    scr = [float((meta[a].get('is') or {}).get('selfCorrelation') or 'nan') for a in recent]
    scr = [x for x in scr if x == x]
    print('    条数 %d   单条S中位 %.3f   组合S %.3f   selfCorr中位 %.4f' % (
        len(recent), np.median(ss), sc or 0, np.median(scr)))
    # 与全池比
    allsc = sh(W[ids].mean(axis=1, skipna=True))
    print('    全池 %d 条组合 S = %.3f  ⇒ 近 3 个月组合 %s 全池' % (
        len(ids), allsc or 0, '高于' if (sc or 0) > (allsc or 0) else '低于'))

# 累积组合曲线（按提交时间，等权，只算到该时点已提交的）
print('\n  --- 累积组合 Sharpe（按提交时间，每 20 条记一次）---')
cum = []
for k in range(20, len(ids) + 1, 20):
    g = ids[:k]
    s = sh(W[g].mean(axis=1, skipna=True))
    cum.append((k, (meta[ids[k - 1]].get('dateSubmitted') or '')[:10], s))
    print('    N=%-4d 截至 %s   组合S %.3f' % (k, cum[-1][1], s or 0))

json.dump(dict(rho_star_check=len(cand) if cand else 0, buckets={
    m: len(v) for m, v in buckets.items()}, recent_n=len(recent) if recent else 0,
    cum=[(k, d, s) for k, d, s in cum]),
    io.open(os.path.join(OUT, 'vf_numbers.json'), 'w', encoding='utf-8'), ensure_ascii=False)
print('\n完成')
