# -*- coding: utf-8 -*-
"""corr_gate.py —— 组合增量门：候选 alpha 到底该不该交

取代 mech_gate.py 的字段判据
--------------------------
mech_gate.py 用「字段集合 Jaccard」判重，已被 replay 实测证伪：
    字段同源 20 条：两两 PnL corr 中位 0.2718，组合 Sharpe 4.176
    字段跨源 20 条：两两 PnL corr 中位 0.3309，组合 Sharpe 3.747
字段同源反而更分散。⇒ 判重必须直接看 PnL。

门槛从哪来
----------
等权加入第 N 条（权重 w=1/N）后组合 Sharpe 不降的充要条件（严格推导）：
    rho  <  b/a  +  (b^2-a^2)/(2a^2) * (w/(1-w)) * (sigma_b/sigma_a)
w 很小时退化为  rho* = b/a
实测校验：400 对真实 PnL，门槛预测 ΔS 符号一致率 100%（2026-11-15）。

用法
----
python _grid/corr_gate.py <alpha_id|cid> [more ids ...]      # 逐个判定
python _grid/corr_gate.py --file cands.txt                   # 一行一个
python _grid/corr_gate.py --cid w154_b                       # mined json 里的批内编号
选项
    --refresh     忽略 PnL 缓存重拉
    --no-add      只看 corr 判定，不算加入后的实际组合 Sharpe（快）

输出
----
每条给三件事：
    1) 与现有池的 maxCorr（本地算，实测与平台 is.selfCorrelation 差 0.007）
    2) 门槛 rho* = b/a
    3) 实际加入后的组合 Sharpe 变化 ΔS（真算，不用公式近似）
"""
import json, io, os, sys, math, glob
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CACHE = 'data/alpha_quality_analysis/pnl'
MINED = 'data/alpha_quality_analysis/mined'
SUB = '_logs/submitted_full.json'

ARGV = sys.argv[1:]
REFRESH = '--refresh' in ARGV
NOADD = '--no-add' in ARGV
IDS = []
i = 0
while i < len(ARGV):
    a = ARGV[i]
    if a == '--file':
        i += 1
        # ★ 11-16 17:35 修 BUG：原代码 IDS += [裸字符串]，但下面按 (kind, val) 解包
        #   ⇒ ValueError: too many values to unpack。文件里每行是 alpha id ⇒ 包成 ('ID', x)。
        IDS += [('ID', x.strip()) for x in io.open(ARGV[i], encoding='utf-8') if x.strip()]
    elif a == '--cid':
        i += 1
        IDS.append(('CID', ARGV[i]))
    elif a.startswith('--'):
        pass
    else:
        IDS.append(('ID', a))
    i += 1

if not IDS:
    print(__doc__); sys.exit(0)


def lag1(v):
    n = len(v)
    if n < 10:
        return 0.0
    m = sum(v) / n
    num = sum((v[i] - m) * (v[i - 1] - m) for i in range(1, n))
    den = sum((x - m) ** 2 for x in v)
    return num / den if den else 0.0


# ---------- 已提交池 ----------
subs = json.load(io.open(SUB, encoding='utf-8'))
meta = {x['id']: x for x in subs}

POOL = {}
for x in subs:
    p = os.path.join(CACHE, x['id'] + '.json')
    if os.path.exists(p):
        try:
            s = json.load(io.open(p, encoding='utf-8'))
            if len(s) >= 250:
                POOL[x['id']] = s
        except Exception:
            pass

pool_ids = sorted(POOL.keys())
pdf = pd.DataFrame({a: pd.Series(POOL[a], dtype='float64') for a in pool_ids})
cov = pdf.notna().sum(axis=1) / len(pool_ids)
good = [d for d in sorted(pdf.index) if cov[d] >= 0.8]
W0, W1 = good[0], good[-1]
WP = pdf.loc[W0:W1]


def sh(ser):
    ser = pd.Series(ser).dropna()
    if len(ser) < 60:
        return None
    m = ser.mean(); sd = ser.std(ddof=0)
    return (m / sd * math.sqrt(252)) if sd else None


A = sh(WP.mean(axis=1, skipna=True))
print('已提交池 %d 条，窗口 %s ~ %s' % (len(pool_ids), W0, W1))
print('池组合 Sharpe a = %.4f' % (A or 0))
print()


# ---------- 取候选 PnL ----------
def _sess():
    sys.path.insert(0, '.')
    from src.core.session import Brain
    return Brain().s


_S = None


def get_pnl(aid):
    global _S
    cp = os.path.join(CACHE, aid + '.json')
    if os.path.exists(cp) and not REFRESH:
        try:
            s = json.load(io.open(cp, encoding='utf-8'))
        except Exception:
            s = None
        if s and len(s) >= 60:
            v = [s[k] for k in sorted(s)]
            if lag1(v) > 0.99:
                # 累计值未差分，现场修
                ks = sorted(s)
                s = {ks[i]: v[i] - v[i - 1] for i in range(1, len(ks))}
                json.dump(s, io.open(cp, 'w', encoding='utf-8'))
                print('  [修] %s 缓存是累计值，已差分' % aid)
            return s
    if _S is None:
        _S = _sess()
    import time
    for _ in range(6):
        r = _S.get('https://api.worldquantbrain.com/alphas/%s/recordsets/pnl' % aid, timeout=40)
        if r.status_code == 429 or r.headers.get('Retry-After'):
            time.sleep(float(r.headers.get('Retry-After') or 5)); continue
        if r.status_code != 200:
            time.sleep(3); continue
        recs = (r.json() or {}).get('records') or []
        if not recs:
            time.sleep(2); continue
        raw = sorted((str(x[0]), float(x[1])) for x in recs if len(x) >= 2 and x[1] is not None)
        ser = {raw[k][0]: raw[k][1] - raw[k - 1][1] for k in range(1, len(raw))}
        json.dump(ser, io.open(cp, 'w', encoding='utf-8'))
        return ser
    return None


def resolve(kind, val):
    if kind == 'ID':
        return val
    p = os.path.join(MINED, val + '.json')
    if os.path.exists(p):
        d = json.load(io.open(p, encoding='utf-8'))
        if d.get('id'):
            return d['id']
    for h in glob.glob(os.path.join(MINED, '*%s*.json' % val)):
        d = json.load(io.open(h, encoding='utf-8'))
        if d.get('_cid') == val and d.get('id'):
            return d['id']
    return None


# ---------- 逐个判定 ----------
rows = []
for kind, val in IDS:
    aid = resolve(kind, val)
    if not aid:
        print('%-12s 找不到对应 alpha id' % val); continue
    ser = get_pnl(aid)
    if not ser:
        print('%-12s 取不到 PnL' % aid); continue
    snew = pd.Series(ser, dtype='float64')
    window = snew.loc[(snew.index >= W0) & (snew.index <= W1)]
    # b 必须与 a 同口径：都用窗口内日 PnL 算（此前误用全历史，会导致门槛判定错位）
    b = sh(window)
    b_full = sh(snew)
    if b is None:
        print('%-12s 窗口内 PnL 不足（%d 日）' % (aid, len(window))); continue

    # 候选可能已在池中：算 corr 与组合时都要排除它自己
    inpool = aid in POOL
    base_ids = [p for p in pool_ids if p != aid]
    WB = WP[base_ids]
    A_base = sh(WB.mean(axis=1, skipna=True)) if base_ids else None

    # 与池逐条 corr，取 max
    cs = {}
    for pid in base_ids:
        idx = window.index.intersection(WP[pid].dropna().index)
        if len(idx) < 120:
            continue
        x = window.loc[idx].values; y = WP[pid].loc[idx].values
        if x.std() == 0 or y.std() == 0:
            continue
        cs[pid] = float(np.corrcoef(x, y)[0, 1])
    if not cs:
        print('%-12s 与池无重叠区间' % aid); continue
    mxid = max(cs, key=cs.get)
    mx = cs[mxid]
    if not A_base:
        continue
    # 完整门槛：含 sigma 比修正（简化式 b/a 在 w 不小或 sigma 差异大时会偏）
    sig_a = float(WB.mean(axis=1, skipna=True).dropna().std(ddof=0))
    sig_b = float(window.std(ddof=0))
    t = (sig_b / sig_a) if sig_a else 1.0
    w = 1.0 / (len(base_ids) + 1) if base_ids else 0.5
    rho_star = b / A_base + ((b * b - A_base * A_base) / (2 * A_base * A_base)) * (w / (1 - w)) * t
    rho_star_simple = b / A_base
    verdict = 'PASS' if mx < rho_star else 'FAIL'
    b_min = mx * A_base
    # 若要让这条通过，S 需要提到多少（解 b：mx = b/a + (b^2-a^2)/(2a^2)*(w/(1-w))*t）
    # 闭式解一元二次：令 c1=(w/(1-w))*t/(2a^2), c2=-mx
    # b^2*c1 + b/a - a*c1 - mx = 0  => c1*b^2 + b/a - (mx + a*c1) = 0
    c1 = (w / (1 - w)) * t / (2 * A_base * A_base)
    disc = (1.0 / A_base) ** 2 + 4 * c1 * (mx + A_base * c1)
    b_need = ((-1.0 / A_base) + math.sqrt(disc)) / (2 * c1) if c1 > 0 and disc > 0 else b_min

    ds = None
    if not NOADD:
        merged = pd.concat([WB, window.rename('NEW')], axis=1)
        s_after = sh(merged.mean(axis=1, skipna=True))
        ds = (s_after - A_base) if (s_after is not None and A_base is not None) else None

    rows.append(dict(id=aid, b=b, b_full=b_full, mx=mx, who=mxid, rho_star=rho_star,
                     rho_star_simple=rho_star_simple, verdict=verdict, b_min=b_min,
                     b_need=b_need, ds=ds, inpool=inpool, a_base=A_base, t=t))

rows.sort(key=lambda r: (0 if r['verdict'] == 'PASS' else 1,
                         -(r['ds'] if r['ds'] is not None else -9)))

print('%-10s %7s %9s %-10s %8s %8s %9s %6s' % (
    'alpha', 'S(自身)', 'maxCorr', '最像的', '门槛ρ*', '简化b/a', '实际ΔS', '判定'))
for r in rows:
    dstr = ('%+.5f' % r['ds']) if r['ds'] is not None else '    -'
    if r['ds'] is not None and abs(r['ds']) < 0.002:
        dstr += '*'
    print('%-10s %7.3f %9.4f %-10s %8.4f %8.4f %9s %6s' % (
        r['id'], r['b'], r['mx'], r['who'], r['rho_star'],
        r['rho_star_simple'], dstr, r['verdict']))

print('\n判据（完整式）：maxCorr < ρ* = b/a + (b²−a²)/(2a²)·(w/(1−w))·(σ_b/σ_a)')
print('  简化式 b/a 在同栏给出，两者接近时可只看简化式')
print('  带 * 的 ΔS 绝对值 <0.002，属浮点噪声量级（N 大时必然如此），只看 PASS/FAIL 不看数值')

npass = sum(1 for r in rows if r['verdict'] == 'PASS')
print('\n本次 %d 条中 PASS %d 条' % (len(rows), npass))

fail = [r for r in rows if r['verdict'] == 'FAIL']
if fail and len(fail) <= 12:
    print('\n失败项的两条补救路径（二选一）：')
    print('  %-10s %10s %14s %16s' % ('alpha', '当前S', '需要的S', '或把corr降到'))
    for r in fail:
        print('  %-10s %10.3f %14s %16s' % (
            r['id'], r['b'],
            ('%.3f' % r['b_need']) if r.get('b_need') else 'n/a',
            ('%.4f' % r['rho_star'])))

inp = [r for r in rows if r.get('inpool')]
if inp:
    print('  注：%d 条本来就在池里，ΔS 是「拿掉再放回」的对照，正常应≈0' % len(inp))
