# -*- coding: utf-8 -*-
"""judge_now.py —— 任意 alpha id 的过墙预判（本地权威版）

为什么需要它：
  find_passers / near_miss 都依赖 all_unsubmitted.json 快照 —— 刚模拟出来的
  新 alpha 不在快照里，于是"永远进不了判决"。
  本工具直接按 id 走：PnL（缓存优先，缺失则拉平台）+ 池对比 + 豁免线计算。

用法：
  python _autologs/judge_now.py e7bOqGbM QPba58lr
  python _autologs/judge_now.py --top 8 e7bOqGbM
输出：_autologs/_judge_now.txt （追加式）
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

TOPN = int(opt('--top', 6))
CORR_FLOOR = float(opt('--corr-floor', 0.66))
CORR_DIRECT = float(opt('--corr-direct', 0.685))
IDS = [x for x in A if not x.startswith('-') and len(x) == 8 and x.isalnum()]

PC = ROOT / 'data/alpha_quality_analysis/pnl'
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
POOL_S = ROOT / 'data/alpha_quality_analysis/pool_s.json'

OUT = io.open(ROOT / '_autologs' / '_judge_now.txt', 'a', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n'); OUT.flush()

sess = requests.Session()
sess.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
for _ in range(8):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        time.sleep(5)


def pnl(aid, use_cache=True):
    f = PC / f'{aid}.json'
    if use_cache and f.exists():
        try:
            return json.load(io.open(f, encoding='utf-8'))
        except Exception:
            pass
    for _ in range(12):
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl', timeout=90)
        except Exception:
            time.sleep(4); continue
        ra = r.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 20)); continue
        try:
            j = r.json()
        except Exception:
            return None
        rec = (j or {}).get('records')
        if not rec:
            return None
        d = {}
        for i in range(1, len(rec)):
            d[rec[i][0]] = rec[i][1] - rec[i - 1][1]
        if len(d) >= 300:
            try:
                json.dump(d, io.open(f, 'w', encoding='utf-8'), ensure_ascii=False)
            except Exception:
                pass
            return d
        return None
    return None


def info(aid):
    """拿 is/test 指标：优先 mined json，其次平台"""
    for g in ROOT.glob('data/alpha_quality_analysis/mined/*.json'):
        try:
            j = json.load(io.open(g, encoding='utf-8'))
        except Exception:
            continue
        if j.get('id') == aid:
            return j
    try:
        return sess.get(f'https://api.worldquantbrain.com/alphas/{aid}', timeout=60).json()
    except Exception:
        return {}


# 池
pool = []
for ln in io.open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    aid = ln.split(',')[0].strip().strip('"')
    if aid and aid not in pool:
        pool.append(aid)
PS = json.load(io.open(POOL_S, encoding='utf-8'))

Praw = {}
for aid in pool:
    f = PC / f'{aid}.json'
    if f.exists():
        try:
            Praw[aid] = json.load(io.open(f, encoding='utf-8'))
        except Exception:
            pass
dates = sorted({k for d in Praw.values() for k in d})
DI = {dt: i for i, dt in enumerate(dates)}
T = len(dates)
pk = sorted(Praw)
M = np.zeros((T, len(pk)))
for j, aid in enumerate(pk):
    for k, v in Praw[aid].items():
        M[DI[k], j] = v
M -= M.mean(axis=0, keepdims=True)
sd = M.std(axis=0); sd[sd == 0] = 1.0
Mn = M / sd
PSv = np.array([PS.get(a) or 0.0 for a in pk])

w('')
w('==== %s  池 %d 条（PnL %d）====' % (time.strftime('%m-%d %H:%M:%S'), len(pool), len(pk)))
for aid in IDS:
    d = pnl(aid)
    if not d:
        w('%-10s 取不到 PnL' % aid); continue
    y = np.zeros(T); hit = 0
    for k, v in d.items():
        i = DI.get(k)
        if i is not None:
            y[i] = v; hit += 1
    if hit < 300:
        w('%-10s 可比天数不足 (%d)' % (aid, hit)); continue
    yy = y - y.mean()
    sy = yy.std()
    cv = (Mn * (yy / sy)[:, None]).mean(axis=0)
    order = np.argsort(-cv)
    j0 = int(order[0]); cmax = float(cv[j0])
    rel = np.where(cv >= CORR_FLOOR)[0]
    inf = info(aid)
    b = inf.get('is') or {}; te = inf.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    TO = b.get('turnover') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    w('---- %s ----' % aid)
    w('   S=%.3f F=%.3f TO=%.4f tS=%s FAIL=%s' % (S, F, TO, te.get('sharpe'), fa))
    w('   最高相关 top%d：' % TOPN)
    for k in order[:TOPN]:
        w('      %-11s corr=%.4f  S=%.2f%s' % (pk[int(k)], cv[int(k)], PSv[int(k)],
                                               '   ★≥0.66' if cv[int(k)] >= CORR_FLOOR else ''))
    if cmax < CORR_DIRECT:
        w('   ⇒ **直通**（corr %.4f < 0.685）' % cmax)
    else:
        if len(rel):
            need = 1.10 * float(PSv[rel].max())
            rival = pk[int(rel[np.argmax(PSv[rel])])]
            gap = need - S
            w('   ⇒ 走豁免：need=1.10x%.2f=%.3f（对手 %s）；gap = %+.3f  %s'
              % (PSv[rel].max(), need, rival, gap, '★过' if gap <= 0 else '✗ 未过'))
        else:
            w('   ⇒ **直通**（无 corr≥0.66 对手）')
    w('   超 0.66=%d  超 0.685=%d  超 0.80=%d' %
      (int((cv >= 0.66).sum()), int((cv >= 0.685).sum()), int((cv >= 0.80).sum())))
OUT.close()
print('judge_now done', flush=True)
