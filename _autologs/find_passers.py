# -*- coding: utf-8 -*-
"""find_passers.py —— 精确算出**当前池下所有能过墙的候选**（直通 + 豁免两条路）

为什么需要它（0921 定论）：
  · 平台接受条件 = 无 FAIL 且 (corr_max < 0.685 或 S >= 1.10 x max(对手S))。
  · 豁免线取决于**对手的 S**，不是固定的 3.5 —— 只撞"弱靶"的候选 need 可能只有 2.4，非常好过。
  · 之前只算了 corr_max，没算 need ⇒ 漏掉了一整类"豁免放行"的候选。

数据源：全部走本地缓存（池 PnL + 候选 PnL），不发网络请求（池 S 除外，可 --no-fetch）。

用法：
  python _autologs/find_passers.py                 # 全量（用缓存里的候选）
  python _autologs/find_passers.py --min-f 1.3     # 只看 F>=1.3 的
"""
import os as _os, io, sys, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import numpy as np
import requests

A = sys.argv[1:]
def opt(n, d):
    for a in A:
        if a == n:
            return A[A.index(a) + 1]
        if a.startswith(n + '='):
            return a.split('=', 1)[1]
    return d

MIN_F = float(opt('--min-f', 0.0))
CORR_FLOOR = float(opt('--corr-floor', 0.66))
CORR_DIRECT = float(opt('--corr-direct', 0.685))
EXEMPT = float(opt('--exempt', 1.10))
NO_FETCH = '--no-fetch' in A

PC = ROOT / 'data/alpha_quality_analysis/pnl'
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
API = ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
POOL_S = ROOT / 'data/alpha_quality_analysis/pool_s.json'

OUT = io.open(ROOT / '_autologs' / '_find_passers.txt', 'w', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n'); OUT.flush()


def g(d, *p):
    c = d
    for k in p:
        if not isinstance(c, dict):
            return None
        c = c.get(k)
        if c is None:
            return None
    return c


pool = []
for ln in io.open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    aid = ln.split(',')[0].strip('"')
    if aid and aid not in pool:
        pool.append(aid)

PS = json.load(io.open(POOL_S, encoding='utf-8'))
missing = [a for a in pool if a not in PS]
if missing and not NO_FETCH:
    sess = requests.Session()
    sess.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
    for _a in range(6):
        try:
            if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                break
        except Exception:
            time.sleep(3)
    for a in missing:
        try:
            j = sess.get(f'https://api.worldquantbrain.com/alphas/{a}', timeout=30).json()
            s = g(j, 'is', 'sharpe')
            if s is not None:
                PS[a] = s
        except Exception:
            pass
        time.sleep(0.2)
    json.dump(PS, io.open(POOL_S, 'w', encoding='utf-8'))
w('池子 %d 条，S 已知 %d 条，最高 S=%.2f' % (len(pool), len([a for a in pool if PS.get(a)]),
                                        max([PS[a] for a in pool if PS.get(a)] or [0])))

Praw = {}
for aid in pool:
    f = PC / f'{aid}.json'
    if f.exists():
        try:
            Praw[aid] = json.load(io.open(f, encoding='utf-8'))
        except Exception:
            pass
w('池子 PnL 取到 %d' % len(Praw))

dates = sorted({k for d in Praw.values() for k in d})
DI = {dt: i for i, dt in enumerate(dates)}
T = len(dates)
M = np.zeros((T, len(Praw)))
pk = sorted(Praw)
for j, aid in enumerate(pk):
    col = np.zeros(T)
    for k, v in Praw[aid].items():
        col[DI[k]] = v
    M[:, j] = col
M -= M.mean(axis=0, keepdims=True)
sd = M.std(axis=0); sd[sd == 0] = 1.0
Mn = M / sd
Sv = np.array([PS.get(a) or 0.0 for a in pk])

data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
sub = set(pool)
rows = []
nocache = 0
for a in data:
    aid = a.get('id')
    if aid in sub:
        continue
    st_ = a.get('settings') or {}
    checks = g(a, 'is', 'checks') or []
    fails = [c.get('name') for c in checks if c and c.get('result') == 'FAIL']
    if fails:
        continue
    F = g(a, 'is', 'fitness')
    if (F or 0) < MIN_F:
        continue
    f = PC / f'{aid}.json'
    if not f.exists():
        nocache += 1; continue
    try:
        d = json.load(io.open(f, encoding='utf-8'))
    except Exception:
        nocache += 1; continue
    y = np.zeros(T); hit = 0
    for k, v in d.items():
        i = DI.get(k)
        if i is not None:
            y[i] = v; hit += 1
    if hit < 300:
        continue
    y -= y.mean()
    sy = y.std()
    if sy == 0:
        continue
    cv = (Mn * (y / sy)[:, None]).mean(axis=0)
    j = int(np.argmax(cv))
    cmax = float(cv[j])
    rel = cv >= CORR_FLOOR
    S = g(a, 'is', 'sharpe') or 0
    if cmax < CORR_FLOOR:
        verdict = '★ 直通(空)'
        need = 0.0; rival = ''
    elif cmax < CORR_DIRECT:
        verdict = '★ 直通'
        need = 0.0; rival = pk[j]
    else:
        idx = np.where(rel)[0]
        k = idx[int(np.argmax(Sv[idx]))]
        need = EXEMPT * Sv[k]
        rival = pk[k]
        verdict = '★ 豁免放行' if S >= need else '✗ 不够'
    rows.append(dict(id=aid, uni=st_.get('universe'), neu=st_.get('neutralization'),
                     delay=st_.get('delay'), dec=st_.get('decay'),
                     S=S, F=F, TO=g(a, 'is', 'turnover'), tS=g(a, 'test', 'sharpe'),
                     margin=g(a, 'is', 'margin'), cmax=cmax, need=need, rival=rival,
                     verdict=verdict, nriv=int(rel.sum())))

w('无 FAIL 且 PnL 在缓存的候选 %d 条（另有 %d 条无缓存未判）' % (len(rows), nocache))
pas = [r for r in rows if r['verdict'].startswith('★')]
pas.sort(key=lambda x: -(x['F'] or 0))
w('')
w('=' * 132)
w('★ 当前池下**能过墙**的候选共 %d 条（直通 %d / 豁免 %d）'
  % (len(pas), len([r for r in pas if '豁免' not in r['verdict']]),
     len([r for r in pas if '豁免' in r['verdict']])))
w('=' * 132)
hdr = '%-11s %-8s %-12s %3s %3s %6s %6s %7s %6s %6s | %8s %8s %-11s %s'
w(hdr % ('id', 'universe', 'neut', 'dly', 'dec', 'S', 'F', 'TO', 'tS', 'margin', 'corr_max', 'need', '强对手', '判定'))
w('-' * 132)
for r in pas:
    w(hdr % (str(r['id'])[:11], str(r['uni'])[:8], str(r['neu'])[:12], r['delay'], r['dec'],
             '%.2f' % r['S'], '%.2f' % (r['F'] or 0), '%.3f' % (r['TO'] or 0),
             '%.2f' % (r['tS'] if r['tS'] is not None else -1),
             '%.1f' % ((r['margin'] or 0) * 1e4), '%.4f' % r['cmax'],
             ('%.2f' % r['need']) if r['need'] else '-', str(r['rival'])[:11], r['verdict']))

w('')
w('== 按 F 分档看能过墙的条数 ==')
for lo in (0, 1.0, 1.2, 1.5, 1.8, 2.0, 2.5, 3.0):
    n = len([r for r in pas if (r['F'] or 0) >= lo])
    w('  F>=%.1f : %d 条' % (lo, n))
w('')
w('== 按 universe 看 ==')
for u in ('TOP3000', 'TOP2000', 'TOP1000', 'TOP500', 'TOP200'):
    w('  %-9s %d' % (u, len([r for r in pas if r['uni'] == u])))
OUT.close(); print('done')
