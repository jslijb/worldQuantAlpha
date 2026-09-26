# -*- coding: utf-8 -*-
"""blob_analysis.py —— 已提交池的"同质团"体检
① 池内两两 corr 矩阵 → 每条的最大/平均相关
② 按 corr>=0.70 贪心聚类 → 团大小、团内 S 分布
③ 表达式腿频次 → 共享腿排行（墙的成因）
④ 有效独立注数（n_eff ≈ n / (1+(n-1)*mean_corr)）
输出：_autologs/_blob.txt
"""
import io, os, csv, json, statistics as st, collections

ROOT = 'D:/Python/worldquant/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
PC = ROOT + 'data/alpha_quality_analysis/pnl/'

L = []

# ---- 读台账 ----
rows = []
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f)
    hdr = next(rd)
    for r in rd:
        if r and r[0].strip():
            rows.append(r)

L.append('台账数据行 %d' % len(rows))
L.append('表头 %s' % hdr[:12])

# 列位置：id, code, S, F, TO, ret, dd, corr_at_submit, dateSubmitted, decay, neut, batch
seen = {}
dups = []
for r in rows:
    aid = r[0].strip()
    if aid in seen:
        dups.append(aid)
        continue
    seen[aid] = r
L.append('唯一 id %d，重复 %d 条：%s' % (len(seen), len(dups), dups))

ids = list(seen.keys())

def fnum(v):
    try:
        return float(v)
    except Exception:
        return None

# ---- 读 PnL ----
P = {}
missing = []
for aid in ids:
    fp = PC + aid + '.json'
    if not os.path.exists(fp):
        missing.append(aid)
        continue
    try:
        d = json.load(io.open(fp, encoding='utf-8'))
        P[aid] = {k: float(v) for k, v in d.items()}
    except Exception:
        missing.append(aid)
L.append('读到 PnL %d 条，缺 %d 条 %s' % (len(P), len(missing), missing[:10]))

pids = [a for a in ids if a in P]

def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300:
        return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5
    sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy:
        return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)

n = len(pids)
M = {}
for i in range(n):
    for j in range(i + 1, n):
        v = corr(P[pids[i]], P[pids[j]])
        if v is not None:
            M[(pids[i], pids[j])] = v

S = {a: fnum(seen[a][2]) for a in pids}
F = {a: fnum(seen[a][3]) for a in pids}
TO = {a: fnum(seen[a][4]) for a in pids}

# ---- ① 每条的最大/平均相关 ----
L.append('')
L.append('== ① 池内相关统计（%d 对）==' % len(M))
vals = sorted(M.values())
if vals:
    L.append('  最小 %.4f  中位 %.4f  最大 %.4f' % (vals[0], vals[len(vals)//2], vals[-1]))

mx = {}
for a in pids:
    vv = [v for (x, y), v in M.items() if x == a or y == a]
    mx[a] = (max(vv) if vv else None, st.mean(vv) if vv else None)
allmean = st.mean([mx[a][1] for a in pids if mx[a][1] is not None])
L.append('  池平均 pairwise corr = %.4f' % allmean)
L.append('  有效独立注数 n_eff ≈ %.1f（名义 %d 条）' % (n / (1 + (n - 1) * allmean), n))

L.append('')
L.append('== ② 最"孤立"的 15 条（max corr 最低）==')
iso = sorted([a for a in pids if mx[a][0] is not None], key=lambda a: mx[a][0])[:15]
for a in iso:
    L.append('  %-10s S=%5s F=%5s TO=%6s  maxcorr=%.4f  mean=%.4f' % (
        a, S[a], F[a], TO[a], mx[a][0], mx[a][1]))

L.append('')
L.append('== ② b 池内 S 前 15 名（墙的高度）==')
top = sorted(pids, key=lambda a: -(S[a] or 0))[:15]
for a in top:
    L.append('  %-10s S=%5s F=%5s TO=%6s  maxcorr=%.4f' % (a, S[a], F[a], TO[a], mx[a][0]))

# ---- ② 贪心聚类 corr>=0.70 ----
L.append('')
L.append('== ③ corr>=0.70 贪心聚类（团 = 互相锁死的组）==')
adj = collections.defaultdict(set)
for (a, b), v in M.items():
    if v >= 0.70:
        adj[a].add(b); adj[b].add(a)
seen_c = set()
clusters = []
for a in sorted(pids, key=lambda x: -len(adj[x])):
    if a in seen_c:
        continue
    stack = [a]; comp = set()
    while stack:
        u = stack.pop()
        if u in comp:
            continue
        comp.add(u); seen_c.add(u)
        for w in adj[u]:
            if w not in comp:
                stack.append(w)
    clusters.append(comp)
clusters.sort(key=len, reverse=True)
for k, c in enumerate(clusters[:12], 1):
    ss = sorted([S[x] for x in c if S[x]], reverse=True)
    L.append('  团%-2d 大小=%-3d 团内 S 头部=%s' % (
        k, len(c), ['%.2f' % v for v in ss[:6]]))
singles = [c for c in clusters if len(c) == 1]
L.append('  → 团总数 %d，其中单点团 %d 条；最大团 %d 条' % (
    len(clusters), len(singles), len(clusters[0]) if clusters else 0))

# ---- ④ 腿频次 ----
L.append('')
L.append('== ④ 表达式腿频次（出现 >=5 次的）==')
import re
legcnt = collections.Counter()
for r in rows:
    code = r[1] if len(r) > 1 else ''
    code = code.strip('"')
    for m in re.finditer(r'group_rank\((.+?),\s*(?:subindustry|industry|sector|bucket\([^)]*\))\)', code):
        leg = m.group(1).strip()
        legcnt[leg] += 1
for leg, c in legcnt.most_common(20):
    if c >= 5:
        L.append('  %-3d  %s' % (c, leg[:110]))

# ---- ⑤ 换手/质量分布 ----
L.append('')
L.append('== ⑤ 台账质量分布 ==')
for name, dic in (('Sharpe', S), ('Fitness', F), ('Turnover', TO)):
    vv = sorted([v for v in dic.values() if v is not None])
    if vv:
        L.append('  %-8s n=%-3d min=%.3f p25=%.3f 中位=%.3f p75=%.3f max=%.3f 均值=%.3f' % (
            name, len(vv), vv[0], vv[len(vv)//4], vv[len(vv)//2], vv[3*len(vv)//4], vv[-1], st.mean(vv)))

L.append('')
L.append('== ⑥ 高换手名单（TO>0.30，含表达式前 90 字符）==')
hi = sorted([a for a in pids if TO[a] and TO[a] > 0.30], key=lambda a: -TO[a])
for a in hi:
    L.append('  %-10s S=%-5s F=%-5s TO=%.3f  %s' % (a, S[a], F[a], TO[a], seen[a][1].strip('"')[:90]))

io.open(ROOT + '_autologs/_blob.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
