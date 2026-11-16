# -*- coding: utf-8 -*-
"""replay_ds.py —— 把「组合增量 DeltaS」与平台真值对账（只读，不提交）

为什么要这个脚本
----------------
11-15 反推出的挖掘法把「组合增量 ΔS>0」列为第 3 道门，但当时没对账。
平台不直接返回 ΔS，所以采用「锚点传递」：
    PnL 序列 ──算 Sharpe──> 与平台 is.sharpe 对账   ← 第 1 道锚
    PnL 序列 ──算 corr───> 与平台 is.selfCorrelation 对账 ← 第 2 道锚
    两道锚都过 ⇒ 同一套 PnL + 同一套算法算出的组合 Sharpe / ΔS 可当判据。

四段输出
--------
1. 单条 Sharpe 对账（本地 vs 平台 is.sharpe），含累计 PnL 一致性校验
2. 自相关对账（本地 max pairwise vs 平台 is.selfCorrelation）
3. 组合回放：按提交时间增量加仓，实测 ΔS 曲线；与等权闭式解对照
4. 同源 vs 跨源 对照实验：同簇 20 条 vs 跨簇 20 条，谁把组合 Sharpe 抬得高

用法
----
python _grid/replay_ds.py                # 全跑
python _grid/replay_ds.py --only 1       # 只跑第 1 段
python _grid/replay_ds.py --n 30         # 组合回放取样条数（默认 40）
"""
import json, io, os, sys, csv, math, random, statistics as st, collections

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

CACHE = 'data/alpha_quality_analysis/pnl'
SUB = '_logs/submitted_full.json'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
FIELDS = 'data/alpha_quality_analysis/all_fields_usa_top3000.json'
OUTDIR = '_logs/replay'
os.makedirs(OUTDIR, exist_ok=True)

ARGV = sys.argv[1:]
ONLY = ARGV[ARGV.index('--only') + 1] if '--only' in ARGV else 'all'
NREP = int(ARGV[ARGV.index('--n') + 1]) if '--n' in ARGV else 40
SEED = 20261115


def hr(t):
    print('\n' + '=' * 78)
    print(t)
    print('=' * 78)


def fnum(x):
    try:
        v = float(x)
        return v if v == v else None
    except Exception:
        return None


def pctl(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p / 100.0
    lo = int(k); hi = min(lo + 1, len(v) - 1)
    return v[lo] + (v[hi] - v[lo]) * (k - lo)


# ---------------- 载入 ----------------
subs = json.load(io.open(SUB, encoding='utf-8'))
print('已提交 alpha（API 拉取）%d 条' % len(subs))

PNL = {}
missing = []
for x in subs:
    aid = x['id']
    p = os.path.join(CACHE, aid + '.json')
    if not os.path.exists(p):
        missing.append(aid); continue
    try:
        s = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        missing.append(aid); continue
    if len(s) >= 250:
        PNL[aid] = {k: v for k, v in s.items() if v is not None}
print('PnL 可用 %d 条，缺 %d 条' % (len(PNL), len(missing)))


def sharpe(series):
    """日 PnL 序列 -> 年化 Sharpe（与平台 is.sharpe 同口径）"""
    v = list(series)
    if len(v) < 60:
        return None
    m = st.mean(v); sd = st.pstdev(v)
    if sd == 0:
        return None
    return m / sd * math.sqrt(252)


def pcorr(a, b, min_n=60):
    keys = set(a) & set(b)
    if len(keys) < min_n:
        return None, len(keys)
    keys = sorted(keys)
    xs = [a[k] for k in keys]; ys = [b[k] for k in keys]
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if vx == 0 or vy == 0:
        return None, n
    return cov / (vx * vy), n


# ================================================================
# 第 1 段：单条 Sharpe 对账 + 累计 PnL 一致性
# ================================================================
if ONLY in ('all', '1'):
    hr('第 1 段  单条 Sharpe 对账：本地 PnL -> Sharpe  vs  平台 is.sharpe')

    rows = []
    for x in subs:
        aid = x['id']
        if aid not in PNL:
            continue
        isd = x.get('is') or {}
        s_plat = fnum(isd.get('sharpe'))
        s_loc = sharpe(PNL[aid].values())
        pnl_plat = fnum(isd.get('pnl'))
        pnl_loc = sum(PNL[aid].values())
        if s_plat is None or s_loc is None:
            continue
        rows.append(dict(id=aid, plat=s_plat, loc=s_loc, err=s_loc - s_plat,
                         pnl_plat=pnl_plat, pnl_loc=pnl_loc, n=len(PNL[aid]),
                         d=(x.get('dateSubmitted') or '')[:10]))

    errs = [abs(r['err']) for r in rows]
    rel = [abs(r['err']) / abs(r['plat']) for r in rows if r['plat']]
    print('样本 %d 条' % len(rows))
    print('  |误差| 中位 %.5f   P90 %.5f   max %.5f' % (pctl(errs, 50), pctl(errs, 90), max(errs)))
    print('  相对误差 中位 %.4f%%   P90 %.4f%%   max %.4f%%' % (
        pctl(rel, 50) * 100, pctl(rel, 90) * 100, max(rel) * 100))
    for th in [0.001, 0.005, 0.01, 0.02, 0.05]:
        n = sum(1 for e in rel if e <= th)
        print('    相对误差 <=%.1f%% : %3d 条 (%.1f%%)' % (th * 100, n, 100.0 * n / len(rel)))

    bad = sorted(rows, key=lambda r: -abs(r['err']))[:8]
    print('\n  误差最大的 8 条：')
    print('  %-10s %-11s %8s %8s %8s %6s' % ('id', 'date', '平台S', '本地S', '误差', 'n日'))
    for r in bad:
        print('  %-10s %-11s %8.3f %8.3f %+8.4f %6d' % (r['id'], r['d'], r['plat'], r['loc'], r['err'], r['n']))

    # 累计 PnL 校验
    pr = [(r['pnl_loc'], r['pnl_plat']) for r in rows if r['pnl_plat']]
    if pr:
        dr = [abs(a - b) / abs(b) for a, b in pr if b]
        print('\n  累计 PnL 校验（sum(日PnL) vs is.pnl）：n=%d  相对误差中位 %.4f%%  max %.4f%%' % (
            len(dr), pctl(dr, 50) * 100, max(dr) * 100))

    json.dump(rows, io.open(os.path.join(OUTDIR, 'sharpe_recon.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)

# ================================================================
# 第 2 段：自相关对账
# ================================================================
if ONLY in ('all', '2'):
    hr('第 2 段  自相关对账：本地 max pairwise corr  vs  平台 is.selfCorrelation')

    # 候选抽样：全量算 pairwise 太慢（341^2/2 = 5.8 万对，每对 ~1200 日）
    # 实际可接受，直接全量
    ids = [x['id'] for x in subs if x['id'] in PNL]
    meta = {x['id']: x for x in subs}
    ids.sort(key=lambda a: (meta[a].get('dateSubmitted') or ''))
    print('参与对账 %d 条，按提交时间升序' % len(ids))

    PRE = {}   # id -> 该条提交前已存在的全部 id
    seen = []
    for aid in ids:
        PRE[aid] = list(seen)
        seen.append(aid)

    # 抽样 30 条做对账（时间上均匀铺开）
    step = max(1, len(ids) // 30)
    samp = ids[::step][:30]

    res = []
    for aid in samp:
        prev = PRE[aid]
        if len(prev) < 3:
            continue
        cur = PNL[aid]
        best = -9; who = None; npair = 0
        for pid in prev:
            c, n = pcorr(cur, PNL[pid])
            if c is None:
                continue
            npair += 1
            if c > best:
                best = c; who = pid
        if who is None:
            continue
        sp = fnum((meta[aid].get('is') or {}).get('selfCorrelation'))
        res.append(dict(id=aid, loc=best, plat=sp, err=(best - sp) if sp is not None else None,
                        who=who, prev=len(prev), npair=npair,
                        d=(meta[aid].get('dateSubmitted') or '')[:10]))

    print('\n  %-10s %-11s %3s %3s %8s %8s %8s' % ('id', 'date', '前池', '对数', '平台self', '本地max', '差'))
    for r in res:
        print('  %-10s %-11s %3d %3d %8s %8.4f %+8.4f' % (
            r['id'], r['d'], r['prev'], r['npair'],
            ('%.4f' % r['plat']) if r['plat'] is not None else '  n/a', r['loc'],
            r['err'] if r['err'] is not None else float('nan')))

    e = [r['err'] for r in res if r['err'] is not None]
    if e:
        ae = [abs(x) for x in e]
        print('\n  n=%d  |差|中位 %.4f  P90 %.4f  max %.4f' % (len(e), pctl(ae, 50), pctl(ae, 90), max(ae)))
        print('  差 <=0.05 : %d 条    <=0.10 : %d 条    >0.15 : %d 条' % (
            sum(1 for x in ae if x <= 0.05), sum(1 for x in ae if x <= 0.10), sum(1 for x in ae if x > 0.15)))
        # 系统性偏差
        print('  带符号均值 %+0.4f（正=本地偏高）' % (sum(e) / len(e)))
    json.dump(res, io.open(os.path.join(OUTDIR, 'selfcorr_recon.json'), 'w', encoding='utf-8'),
              ensure_ascii=False)

# ================================================================
# 第 3 段：组合回放 ΔS
# ================================================================
if ONLY in ('all', '3'):
    hr('第 3 段  组合回放：按提交时间增量加仓，实测 ΔS')
    meta = {x['id']: x for x in subs}
    ids = [x['id'] for x in subs if x['id'] in PNL]
    ids.sort(key=lambda a: (meta[a].get('dateSubmitted') or ''))
    ids = ids[::max(1, len(ids) // NREP)][:NREP]
    print('取样 %d 条（从 %d 条里等距取），按提交时间升序' % (len(ids), len(PNL)))

    def combo_sharpe(members, fixed=None):
        """等权日再平衡：当日有 PnL 的成员均值"""
        acc = collections.defaultdict(list)
        for aid in members:
            for d, v in PNL[aid].items():
                if fixed and not (fixed[0] <= d <= fixed[1]):
                    continue
                acc[d].append(v)
        ser = [sum(v) / len(v) for d, v in sorted(acc.items())]
        return sharpe(ser), len(ser)

    # 固定窗口（用取样集里最晚起点之后，保证成分齐整）
    starts = sorted(min(PNL[a]) for a in ids)
    ends = sorted(max(PNL[a]) for a in ids)
    w0 = starts[-1]; w1 = ends[0]
    print('固定窗口: %s ~ %s' % (w0, w1))

    print('\n  --- 版本 A：可变成分、全历史（模拟实盘）---')
    print('  %3s %-10s %8s %8s %8s' % ('N', '新增id', '组合S', 'ΔS', '该条自身S'))
    prev_s = None
    curveA = []
    for k in range(1, len(ids) + 1):
        s, n = combo_sharpe(ids[:k])
        ds = (s - prev_s) if (prev_s is not None and s is not None) else None
        self_s = sharpe(PNL[ids[k - 1]].values())
        curveA.append(dict(k=k, id=ids[k - 1], s=s, ds=ds, self_s=self_s, n=n))
        if k <= 12 or k % 5 == 0 or k == len(ids):
            print('  %3d %-10s %8.3f %8s %8.3f' % (
                k, ids[k - 1], s if s else 0,
                ('%+0.4f' % ds) if ds is not None else '     -', self_s or 0))
        prev_s = s

    print('\n  --- 版本 B：固定窗口、全成分 ---')
    print('  %3s %-10s %8s %8s' % ('N', '新增id', '组合S', 'ΔS'))
    prev_s = None
    curveB = []
    for k in range(1, len(ids) + 1):
        s, n = combo_sharpe(ids[:k], fixed=(w0, w1))
        ds = (s - prev_s) if (prev_s is not None and s is not None) else None
        curveB.append(dict(k=k, id=ids[k - 1], s=s, ds=ds, n=n))
        if k <= 12 or k % 5 == 0 or k == len(ids):
            print('  %3d %-10s %8.3f %8s' % (k, ids[k - 1], s if s else 0,
                                             ('%+0.4f' % ds) if ds is not None else '     -'))
        prev_s = s

    # 等权闭式解对照
    hr('第 3 段附  等权闭式解对照：S_p = S * sqrt(2/(1+rho))')
    print('  两条同 Sharpe=S、相关=rho 的腿等权合并：')
    print('  %6s %10s %10s' % ('rho', 'S_组合/S', '增量占比'))
    for rho in [0.0, 0.3, 0.5, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99, 1.0]:
        if rho >= 1:
            print('  %6.2f %10.3f %10s' % (rho, 1.0, '0.0%')); continue
        f = math.sqrt(2 / (1 + rho))
        print('  %6.2f %10.4f %9.1f%%' % (rho, f, (f - 1) * 100))

    dsA = [c['ds'] for c in curveA if c['ds'] is not None]
    dsB = [c['ds'] for c in curveB if c['ds'] is not None]
    print('\n  实测 ΔS 分布（版本A）：n=%d  中位 %+0.4f  均值 %+0.4f  负值占比 %.1f%%' % (
        len(dsA), pctl(dsA, 50), sum(dsA) / len(dsA), 100.0 * sum(1 for x in dsA if x < 0) / len(dsA)))
    print('  实测 ΔS 分布（版本B）：n=%d  中位 %+0.4f  均值 %+0.4f  负值占比 %.1f%%' % (
        len(dsB), pctl(dsB, 50), sum(dsB) / len(dsB), 100.0 * sum(1 for x in dsB if x < 0) / len(dsB)))
    print('  组合 S 起点/终点：A %.3f -> %.3f   B %.3f -> %.3f' % (
        curveA[0]['s'] or 0, curveA[-1]['s'] or 0, curveB[0]['s'] or 0, curveB[-1]['s'] or 0))

    json.dump(dict(curveA=curveA, curveB=curveB, w0=w0, w1=w1, ids=ids),
              io.open(os.path.join(OUTDIR, 'combo_curve.json'), 'w', encoding='utf-8'), ensure_ascii=False)

# ================================================================
# 第 4 段：同源 vs 跨源 对照实验
# ================================================================
if ONLY in ('all', '4'):
    hr('第 4 段  同源 vs 跨源：机制多样性到底值多少组合 Sharpe')
    meta = {x['id']: x for x in subs}

    # 用字段集合做簇（Jaccard>=0.5），复用 11-15 的口径
    F = json.load(io.open(FIELDS, encoding='utf-8'))
    toks = sorted([k for k in F if len(k) >= 3], key=len, reverse=True)
    import re
    pat = re.compile(r'(?<![A-Za-z0-9_])(' + '|'.join(re.escape(t) for t in toks) + r')(?![A-Za-z0-9_])')
    DROP = {'close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'cap', 'adv20',
            'sharesout', 'dividend', 'split', 'country', 'exchange', 'market', 'sector',
            'industry', 'subindustry', 'currency'}

    fps = {}
    for x in subs:
        code = (x.get('regular') or {}).get('code') or ''
        fs = set(m.group(1) for m in pat.finditer(code)) - DROP
        fps[x['id']] = fs

    ids = [x['id'] for x in subs if x['id'] in PNL]
    n = len(ids)
    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a

    for i in range(n):
        if not fps[ids[i]]:
            continue
        for j in range(i + 1, n):
            if not fps[ids[j]]:
                continue
            a, b = fps[ids[i]], fps[ids[j]]
            if len(a & b) / len(a | b) >= 0.5:
                ra, rb = find(i), find(j)
                if ra != rb:
                    parent[rb] = ra
    cl = collections.defaultdict(list)
    for i in range(n):
        cl[find(i)].append(ids[i])
    clusters = sorted(cl.values(), key=len, reverse=True)
    print('簇数 %d，最大簇 %d 条（占 %.1f%%）' % (len(clusters), len(clusters[0]),
                                              100.0 * len(clusters[0]) / len(ids)))

    def combo_sharpe(members, fixed=None):
        acc = collections.defaultdict(list)
        for aid in members:
            for d, v in PNL[aid].items():
                if fixed and not (fixed[0] <= d <= fixed[1]):
                    continue
                acc[d].append(v)
        ser = [sum(v) / len(v) for d, v in sorted(acc.items())]
        return sharpe(ser), len(ser)

    random.seed(SEED)
    K = 20

    # A 组：同源——最大簇里取 20 条（按提交时间）
    big = sorted(clusters[0], key=lambda a: (meta[a].get('dateSubmitted') or ''))
    grp_same = big[::max(1, len(big) // K)][:K]

    # B 组：跨源——每个簇取 1 条，取前 20 个簇（按簇大小降序），每簇取提交最早的一条
    grp_cross = []
    for c in clusters[:K]:
        cc = sorted(c, key=lambda a: (meta[a].get('dateSubmitted') or ''))
        grp_cross.append(cc[0])
    grp_cross = [x for x in grp_cross if x][:K]

    # C 组：随机 20 条（对照，反映「随便挑」
    grp_rand = random.sample(ids, min(K, len(ids)))

    for name, grp in [('同源（最大簇内 20 条）', grp_same),
                      ('跨源（20 个不同簇各 1 条）', grp_cross),
                      ('随机 20 条', grp_rand)]:
        starts = sorted(min(PNL[a]) for a in grp)
        ends = sorted(max(PNL[a]) for a in grp)
        w0, w1 = starts[-1], ends[0]
        s, nn = combo_sharpe(grp, fixed=(w0, w1))
        # 成员的平均单条 Sharpe
        ss = [sharpe(PNL[a].values()) for a in grp]
        ss = [x for x in ss if x]
        # 成员两两平均 corr
        cs = []
        for i in range(len(grp)):
            for j in range(i + 1, len(grp)):
                c, _ = pcorr(PNL[grp[i]], PNL[grp[j]])
                if c is not None:
                    cs.append(c)
        print('\n  %s' % name)
        print('    单条 S 中位 %.3f   两两 corr 中位 %.4f (n=%d)   组合 S %.3f   窗口 %s~%s (%d 日)' % (
            pctl(ss, 50) if ss else 0, pctl(cs, 50) if cs else 0, len(cs), s or 0, w0, w1, nn))
        if ss and s:
            print('    组合/单条 = %.3f  （等权理论值 sqrt(1/(mean_corr)) 近似）' % (s / pctl(ss, 50)))

    json.dump(dict(same=grp_same, cross=grp_cross, rand=grp_rand,
                   n_clusters=len(clusters), top_sizes=[len(c) for c in clusters[:15]]),
              io.open(os.path.join(OUTDIR, 'diversity_ab.json'), 'w', encoding='utf-8'), ensure_ascii=False)

print('\n完成。中间结果见 %s/' % OUTDIR)
