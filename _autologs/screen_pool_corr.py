# -*- coding: utf-8 -*-
"""screen_pool_corr.py —— 对**全部**未提交候选算"对已入池 109 条的最大相关"，找真弹药

为什么需要它（0921，战略纠正）：
  我们此前只在"过我们自己闸门（S+F>=4.0 / F>=1.8 / tS>=1.25 / TO<=20%）"的 371 条里找候选。
  但平台的接受条件 = **无 FAIL + selfCorr 过墙**，Fitness 只是评分项之一，不是准入线
  （平台实测 FAIL 阈值 F>=1.0）。⇒ **被我们自己闸门砍掉的那 3200+ 条里，可能藏着
  corr 干净、无 FAIL、能入池的候选。**

  而且实测 IS Score ≈ 79 x 条数（8636/109、8348/105 两条独立读数都落在 79.2~79.5），
  ⇒ 每多入池一条 ≈ +72~79 IS 分。**"能不能入池"的紧约束是墙，不是 Fitness。**

本脚本：拉全量候选 PnL（带磁盘缓存 + 多线程）→ 用 numpy 向量化算对池 109 条的 corr → 按 corr_max 分档输出。

用法：
  python _autologs/screen_pool_corr.py --min-f 1.0 --max-to 0.70 --min-ts 0.0
  python _autologs/screen_pool_corr.py --limit 200          # 试跑
"""
import os as _os, io, sys, json, time, threading
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import numpy as np
import requests

OUT = io.open(ROOT / '_autologs' / '_screen_pool_corr.txt', 'w', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n'); OUT.flush()

A = sys.argv[1:]
def opt(n, d):
    for a in A:
        if a == n:
            return A[A.index(a) + 1]
        if a.startswith(n + '='):
            return a.split('=', 1)[1]
    return d

MIN_F = float(opt('--min-f', 1.0))
MAX_TO = float(opt('--max-to', 0.70))
MIN_TS = float(opt('--min-ts', 0.0))
MIN_S = float(opt('--min-s', 0.0))
LIMIT = int(opt('--limit', 0))
WORKERS = int(opt('--workers', 8))
ALLOW_FAIL = '--allow-fail' in A
CORR_DIRECT = float(opt('--corr-direct', 0.685))
CORR_FLOOR = float(opt('--corr-floor', 0.66))

PC = ROOT / 'data/alpha_quality_analysis/pnl'
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
API = ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'

_tl = threading.local()
def sess():
    if not hasattr(_tl, 's'):
        s = requests.Session()
        s.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
        for _a in range(6):
            try:
                if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                    break
            except Exception:
                time.sleep(3)
        _tl.s = s
    return _tl.s


def pnl(aid):
    f = PC / f'{aid}.json'
    if f.exists():
        try:
            return json.load(open(f, encoding='utf-8'))
        except Exception:
            pass
    s = sess()
    j = None; ra = None
    for att in range(4):
        try:
            r = s.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl', timeout=45)
            ra = r.headers.get('Retry-After')
            j = r.json()
            if j.get('records'):
                break
        except Exception:
            j = None
        # ⚠ 本机/平台坑：Retry-After 可能是 300~600，原样 sleep 会把批次挂死（0921 卡死 5 分钟）
        time.sleep(min(float(ra), 15) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        return None
    d = {}; prev = None
    for r in j['records']:
        cum = float(r[1])
        d[str(r[0])] = cum - (prev if prev is not None else cum)
        prev = cum
    json.dump(d, open(f, 'w', encoding='utf-8'))
    return d


def g(d, *p, default=None):
    cur = d
    for k in p:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


# ---------- 池子矩阵 ----------
pool = []
for ln in io.open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    aid = ln.split(',')[0].strip('"')
    if aid and aid not in pool:
        pool.append(aid)

Praw = {}
for aid in pool:
    d = pnl(aid)
    if d:
        Praw[aid] = d
w('池子 %d 条，取到 PnL %d 条' % (len(pool), len(Praw)))

dates = sorted({k for d in Praw.values() for k in d})
DI = {dt: i for i, dt in enumerate(dates)}
T = len(dates)
M = np.zeros((T, len(Praw)), dtype=np.float64)
pk = list(Praw)
for j, aid in enumerate(pk):
    col = np.zeros(T)
    for k, v in Praw[aid].items():
        col[DI[k]] = v
    M[:, j] = col
M -= M.mean(axis=0, keepdims=True)
sd = M.std(axis=0)
sd[sd == 0] = 1.0
Mn = M / sd
w('共同日期轴 %d 天' % T)

# ---------- 候选 ----------
data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
sub = set(pool)
cands = []
for a in data:
    st_ = a.get('settings') or {}
    checks = g(a, 'is', 'checks', default=[]) or []
    fails = [c.get('name') for c in checks if c and c.get('result') == 'FAIL']
    S = g(a, 'is', 'sharpe'); F = g(a, 'is', 'fitness')
    TO = g(a, 'is', 'turnover'); tS = g(a, 'test', 'sharpe')
    if a.get('id') in sub:
        continue
    if (F or 0) < MIN_F or (TO or 9) > MAX_TO or (tS if tS is not None else -9) < MIN_TS:
        continue
    if (S or 0) < MIN_S:
        continue
    if fails and not ALLOW_FAIL:
        continue
    cands.append(dict(id=a.get('id'), S=S, F=F, TO=TO, tS=tS, fails=fails,
                      R=g(a, 'is', 'returns'), margin=g(a, 'is', 'margin'),
                      uni=st_.get('universe'), neu=st_.get('neutralization'),
                      delay=st_.get('delay'), dec=st_.get('decay')))
cands.sort(key=lambda x: -(x['F'] or 0))
if LIMIT:
    cands = cands[:LIMIT]
w('候选 %d 条（min_f %.2f / max_to %.2f / min_ts %.2f / 无FAIL=%s）' % (len(cands), MIN_F, MAX_TO, MIN_TS, not ALLOW_FAIL))

# ---------- 并发取 PnL ----------
res = {}
lock = threading.Lock()
todo = [c for c in cands if not (PC / (c['id'] + '.json')).exists()]
w('PnL 已缓存 %d，需新拉 %d' % (len(cands) - len(todo), len(todo)))
done = [0]

def work(chunk):
    for c in chunk:
        if c['id'] in res:
            continue
        try:
            d = pnl(c['id'])
        except Exception:
            d = None
        with lock:
            res[c['id']] = d
            done[0] += 1
            if done[0] % 100 == 0:
                w('  ...已取 %d/%d' % (done[0], len(todo)))

CACHE_ONLY = '--cache-only' in A
if todo and not CACHE_ONLY:
    nch = max(1, min(WORKERS, len(todo)))
    chunks = [todo[i::nch] for i in range(nch)]
    ths = [threading.Thread(target=work, args=(ch,)) for ch in chunks]
    for t in ths: t.start()
    for t in ths: t.join()
elif todo:
    w('  --cache-only：本次不拉取，缺 %d 条按无 corr 处理' % len(todo))
# 缓存的直接读
for c in cands:
    if c['id'] not in res:
        try:
            res[c['id']] = json.load(open(PC / (c['id'] + '.json'), encoding='utf-8'))
        except Exception:
            res[c['id']] = None

# ---------- 相关 ----------
rows = []
for c in cands:
    d = res.get(c['id'])
    if not d:
        c['cmax'] = None; c['rival'] = ''
        rows.append(c); continue
    y = np.zeros(T); hit = 0
    for k, v in d.items():
        i = DI.get(k)
        if i is not None:
            y[i] = v; hit += 1
    if hit < 300:
        c['cmax'] = None; c['rival'] = 'short'
        rows.append(c); continue
    y -= y.mean()
    sy = y.std()
    if sy == 0:
        c['cmax'] = None; c['rival'] = 'flat'
        rows.append(c); continue
    cv = (Mn * (y / sy)[:, None]).mean(axis=0)
    j = int(np.argmax(cv))
    c['cmax'] = float(cv[j]); c['rival'] = pk[j]
    rows.append(c)

ok = [c for c in rows if c['cmax'] is not None]
clean = [c for c in ok if c['cmax'] < CORR_FLOOR]
direct = [c for c in ok if c['cmax'] < CORR_DIRECT]

w('')
w('=' * 128)
w('算到 corr 的 %d 条；corr_max < %.2f 的 **%d** 条；corr_max < %.3f（直通线）的 **%d** 条'
  % (len(ok), CORR_FLOOR, len(clean), CORR_DIRECT, len(direct)))
w('=' * 128)
hdr = '%-11s %-8s %-12s %-3s %-3s %6s %6s %7s %6s %6s | %8s %-11s'
w(hdr % ('id', 'universe', 'neut', 'dly', 'dec', 'S', 'F', 'TO', 'tS', 'margin', 'corr_max', '撞谁'))
w('-' * 128)
for c in clean:
    w(hdr % (str(c['id'])[:11], str(c['uni'])[:8], str(c['neu'])[:12], c['delay'], c['dec'],
             '%.2f' % (c['S'] or 0), '%.2f' % (c['F'] or 0), '%.3f' % (c['TO'] or 0),
             '%.2f' % (c['tS'] if c['tS'] is not None else -1),
             '%.1f' % ((c['margin'] or 0) * 1e4), '%.4f' % c['cmax'], str(c['rival'])[:11]))

w('')
w('== corr 分档统计 ==')
bins = [(0, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.66), (0.66, 0.685), (0.685, 0.75), (0.75, 0.85), (0.85, 1.01)]
for lo, hi in bins:
    n = len([c for c in ok if lo <= c['cmax'] < hi])
    w('  [%.2f, %.2f) = %d' % (lo, hi, n))
w('')
w('== 按 universe 看干净条数（corr_max<%.2f）==' % CORR_FLOOR)
for u in ('TOP3000', 'TOP2000', 'TOP1000', 'TOP500', 'TOP200'):
    sel = [c for c in clean if c['uni'] == u]
    w('  %-9s %d' % (u, len(sel)))
OUT.close()
print('done')
