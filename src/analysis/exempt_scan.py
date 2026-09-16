# -*- coding: utf-8 -*-
"""exempt_scan.py —— 全量候选的【直通 + 豁免】双通道扫描（纯离线，用缓存的日 PnL）

规则（0916 定案）：
  直通：max corr < 0.70
  豁免：max corr ≥ 0.70 时，候选 S ≥ 1.10 × max(所有 corr≥0.70 对手的 S)
工具已标定：平台 selfCorr ≈ 本地 corr + 0.006 ~ +0.017（4 个样本）
  → 直接通道留缓冲：本地 ≤ 0.70 - buf 才算直通
  → 豁免通道留缓冲：本地 ≥ 0.70 - buf 的对手都算进"要压过"的集合

用法：
  python src/analysis/exempt_scan.py [--buf 0.015] [--top 40]
"""
import os as _os, pathlib as _pl, sys, json, csv
import numpy as np

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

CAND = 'data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv'
PCACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
OUT = 'data/alpha_quality_analysis/passable_candidates.csv'

BUF = 0.015
if '--buf' in sys.argv:
    BUF = float(sys.argv[sys.argv.index('--buf') + 1])
TOPN = 40
if '--top' in sys.argv:
    TOPN = int(sys.argv[sys.argv.index('--top') + 1])

DIRECT = 0.70 - BUF      # 本地 ≤ 此值算直通
EXSET = 0.70 - BUF       # 本地 ≥ 此值的对手进豁免集

# --- 池子 = 台账（唯一事实源）---
LSH, LNAME = {}, {}
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if len(row) >= 4 and len(row[0]) == 8:
        # 台账列序：id,expr,S,F,T,R,DD,selfCorr,... → S 是 row[2]！row[3] 是 Fitness（曾误用）
        try:
            LSH.setdefault(row[0], float(row[2]))
        except Exception:
            pass
        if len(row) >= 12:
            LNAME.setdefault(row[0], row[11])


def load(aid):
    p = _pl.Path(PCACHE) / f'{aid}.json'
    if not p.exists():
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


pool = {}
for pid in LSH:
    v = load(pid)
    if v:
        pool[pid] = v
pids = list(pool)
print(f'池子 {len(pids)} 条（台账 {len(LSH)}）')

dates = None
for ps in pool.values():
    ds = set(ps)
    dates = ds if dates is None else (dates & ds)
dates = sorted(dates)
T = len(dates)
print(f'对齐日期 {T} 天')
Pm = np.vstack([[pool[q][d] for d in dates] for q in pids])
Pz = (Pm - Pm.mean(axis=1, keepdims=True)) / np.maximum(Pm.std(axis=1, ddof=1, keepdims=True), 1e-12)
psh = np.array([LSH.get(q, 0.0) for q in pids])

rows = list(csv.DictReader(open(CAND, encoding='utf-8-sig')))
res = []
skipped = 0
already = set(LSH)
for r in rows:
    aid = r['id']
    if aid in already:
        continue
    try:
        SF = float(r['SF']); ts = float(r['tS'] or 0); S = float(r['S'])
    except Exception:
        continue
    if SF < 4.0 or ts < 1.25 or (r.get('fails') or '').strip():
        skipped += 1; continue
    cp = load(aid)
    if not cp:
        continue
    try:
        c = np.array([cp[d] for d in dates], dtype=float)
    except KeyError:
        continue
    c = c - c.mean()
    sd = c.std(ddof=1)
    if sd == 0:
        continue
    cvec = (Pz @ c) / (T * sd)
    mx = float(cvec.max()); hit = pids[int(cvec.argmax())]
    over = cvec >= EXSET
    if over.any():
        need = 1.10 * float(psh[over].max())
        need_who = pids[int(np.where(over)[0][np.argmax(psh[over])])]
    else:
        need, need_who = None, ''
    if mx <= DIRECT:
        verdict = 'DIRECT'
    elif need is not None and S >= need:
        verdict = 'EXEMPT'
    else:
        verdict = 'NO'
    res.append({'cid': r['cid'], 'id': aid, 'SF': SF, 'S': S, 'F': r['F'], 'T': r['T'],
                'tS': ts, 'DD': r['DD'], 'decay': r['decay'], 'maxcorr': round(mx, 4),
                'nearest': hit, 'need_S': round(need, 3) if need else '', 'need_who': need_who,
                'margin': round(S - need, 3) if need else '', 'verdict': verdict,
                'expr': r['expr']})
res.sort(key=lambda x: (x['verdict'] != 'DIRECT', x['verdict'] != 'EXEMPT',
                        x['maxcorr']))
print(f'候选 {len(rows)} 条，质量门过滤掉 {skipped} 条，实际评估 {len(res)} 条\n')

with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(res[0].keys()), extrasaction='ignore')
    w.writeheader()
    for r in res:
        w.writerow(r)
print(f'落盘 {OUT}\n')

for v in ('DIRECT', 'EXEMPT'):
    sub = [r for r in res if r['verdict'] == v]
    print(f'===== {v}  {len(sub)} 条 =====')
    for r in sub[:TOPN]:
        extra = '' if v == 'DIRECT' else f" 需S≥{r['need_S']}(压{r['need_who']}) 余量{r['margin']}"
        print(f"  {r['cid']:<9} {r['id']} SF={r['SF']:.2f} S={r['S']} tS={r['tS']} DD={r['DD']} "
              f"T={r['T']} decay={r['decay']} maxcorr={r['maxcorr']:.4f} 撞{r['nearest']}{extra}")
    print()
