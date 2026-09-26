# -*- coding: utf-8 -*-
"""near_miss.py —— 近失分析器：把被墙候选按「离豁免线还差多少」排序

为什么需要它：
  find_passers.py 只输出「已经能过」的 59 条，看不到「差一点就能过」的。
  而豁免线 = 1.10 x max(corr>=0.66 对手的 S)，**gap = need - S** 直接告诉我们
  这条候选还差多少夏普就能过墙 —— 这就是最值得做手术的目标清单。

数据：全部走本地缓存（池 PnL + 候选 PnL），不发网络请求。
用法：
  python _autologs/near_miss.py                       # 全库，按 gap 升序取前 30
  python _autologs/near_miss.py --min-f 1.5 --top 40
  python _autologs/near_miss.py --ids YP58Mr5l,A10ev37X
输出：_autologs/_near_miss.txt
"""
import os as _os, io, sys, json
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import numpy as np

A = sys.argv[1:]
def opt(n, d):
    for a in A:
        if a == n:
            return A[A.index(a) + 1]
        if a.startswith(n + '='):
            return a.split('=', 1)[1]
    return d

MIN_F = float(opt('--min-f', 0.0))
TOP = int(opt('--top', 30))
IDS = [x.strip() for x in (opt('--ids', '') or '').split(',') if x.strip()]
CORR_FLOOR = float(opt('--corr-floor', 0.66))
CORR_DIRECT = float(opt('--corr-direct', 0.685))
FETCH = '--fetch' in A

PC = ROOT / 'data/alpha_quality_analysis/pnl'
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
API = ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
POOL_S = ROOT / 'data/alpha_quality_analysis/pool_s.json'

OUT = io.open(ROOT / '_autologs' / '_near_miss.txt', 'w', encoding='utf-8')
def w(s=''):
    OUT.write(str(s) + '\n')


def g(d, *p):
    c = d
    for k in p:
        if not isinstance(c, dict):
            return None
        c = c.get(k)
        if c is None:
            return None
    return c


# ---------- 池 ----------
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
w('池子 %d 条（PnL 可用 %d），最高 S=%.2f' % (len(pool), len(pk), PSv.max() if len(PSv) else 0))

# ---------- 候选 ----------
data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
sub = set(pool)
cands = []
for a in data:
    aid = a.get('id')
    if aid in sub:
        continue
    if IDS and aid not in IDS:
        continue
    fails = [c.get('name') for c in (g(a, 'is', 'checks') or []) if c and c.get('result') == 'FAIL']
    if fails:
        continue
    F = g(a, 'is', 'fitness') or 0
    if F < MIN_F:
        continue
    if not (PC / f'{aid}.json').exists() and not FETCH:
        continue
    cands.append(a)
w('纳入分析候选 %d 条（无 FAIL、F>=%.2f、%s）'
  % (len(cands), MIN_F, '有 PnL 缓存或按需拉取' if FETCH else '有 PnL 缓存'))

if FETCH:
    import requests
    sess = requests.Session()
    sess.auth = tuple(json.load(io.open(ROOT / 'brain_credentials.txt')))
    for _ in range(8):
        try:
            if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
                break
        except Exception:
            __import__('time').sleep(5)
    got = 0
    for a in cands:
        aid = a['id']
        if (PC / f'{aid}.json').exists():
            continue
        ok = False
        for att in range(10):
            try:
                r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl', timeout=90)
            except Exception:
                __import__('time').sleep(5); continue
            ra = r.headers.get('Retry-After')
            if ra:
                __import__('time').sleep(min(float(ra), 20)); continue
            try:
                j = r.json()
            except Exception:
                j = None
            rec = (j or {}).get('records')
            if rec:
                d = {}
                for i in range(1, len(rec)):
                    d[rec[i][0]] = rec[i][1] - rec[i - 1][1]
                if len(d) >= 300:
                    json.dump(d, io.open(PC / f'{aid}.json', 'w', encoding='utf-8'), ensure_ascii=False)
                    ok = True
                break
            break
        got += 1 if ok else 0
    w('   按需 PnL 拉取成功 %d 条' % got)

rows = []
for a in cands:
    aid = a['id']
    try:
        d = json.load(io.open(PC / f'{aid}.json', encoding='utf-8'))
    except Exception:
        continue
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
    rel = np.where(cv >= CORR_FLOOR)[0]
    S = g(a, 'is', 'sharpe') or 0.0
    st = a.get('settings') or {}
    if cmax < CORR_DIRECT:
        need = 0.0; gap = 0.0; rival = ''; kind = '直通'
    else:
        need = 1.10 * float(PSv[rel].max()) if len(rel) else 0.0
        rival = pk[int(rel[np.argmax(PSv[rel])])] if len(rel) else ''
        gap = need - S
        kind = '豁免'
    rows.append(dict(id=aid, u=st.get('universe'), dly=st.get('delay'), dec=st.get('decay'),
                     S=S, F=g(a, 'is', 'fitness'), TO=g(a, 'is', 'turnover'),
                     tS=g(a, 'test', 'sharpe'), cmax=cmax, need=need, gap=gap,
                     rival=rival, kind=kind, code=(g(a, 'regular', 'code') or '')[:100]))

ok = [r for r in rows if r['kind'] == '直通' or r['gap'] <= 0]
blocked = sorted([r for r in rows if not (r['kind'] == '直通' or r['gap'] <= 0)], key=lambda r: r['gap'])
w('')
w('== 能过 %d 条 / 被墙 %d 条 ==' % (len(ok), len(blocked)))
w('')
w('★ 离豁免线最近的 %d 条（gap = need - S，越小越好过）' % TOP)
w('%-10s %-8s %-4s %-4s %6s %6s %7s %6s | %8s %7s %7s %-10s %s'
  % ('id', 'universe', 'dly', 'dec', 'S', 'F', 'TO', 'tS', 'corr_max', 'need', 'gap', '强对手', '表达式'))
for r in blocked[:TOP]:
    w('%-10s %-8s %-4s %-4s %6.2f %6.2f %7.4f %6.2f | %8.4f %7.3f %7.3f %-10s %s'
      % (r['id'], r['u'], r['dly'], r['dec'], r['S'], r['F'] or 0, r['TO'] or 9, r['tS'] or 0,
         r['cmax'], r['need'], r['gap'], r['rival'], r['code']))
w('')
w('== gap 分档 ==')
for th in (0.05, 0.10, 0.20, 0.30, 0.50, 0.80, 1.20):
    w('   gap <= %.2f : %d 条' % (th, sum(1 for r in blocked if r['gap'] <= th)))
w('')
w('★ 手术靶：dly=1 且 tS>=1.25 且 TO<=0.15 且 gap<=0.45（有 TO 预算可换 S）')
w('%-10s %-8s %-4s %6s %6s %7s %6s | %8s %7s %7s %-10s %s'
  % ('id', 'universe', 'dec', 'S', 'F', 'TO', 'tS', 'corr_max', 'need', 'gap', '强对手', '表达式'))
surg = [r for r in blocked
        if r['dly'] == 1 and (r['tS'] or 0) >= 1.25 and (r['TO'] or 9) <= 0.15 and r['gap'] <= 0.45]
surg.sort(key=lambda r: r['gap'])
for r in surg[:20]:
    w('%-10s %-8s %-4s %6.2f %6.2f %7.4f %6.2f | %8.4f %7.3f %7.3f %-10s %s'
      % (r['id'], r['u'], r['dec'], r['S'], r['F'] or 0, r['TO'] or 9, r['tS'] or 0,
         r['cmax'], r['need'], r['gap'], r['rival'], r['code']))
w('   （共 %d 条符合条件）' % len(surg))

w('')
w('== 被墙候选里 F 最高的 15 条（看有没有"高 F 只差一点"的）==')
hi = sorted(blocked, key=lambda r: -(r['F'] or 0))[:15]
w('%-10s %-8s %-4s %6s %6s %7s | %8s %7s %7s %s'
  % ('id', 'universe', 'dly', 'S', 'F', 'tS', 'corr_max', 'need', 'gap', '强对手'))
for r in hi:
    w('%-10s %-8s %-4s %6.2f %6.2f %7.2f | %8.4f %7.3f %7.3f %s'
      % (r['id'], r['u'], r['dly'], r['S'], r['F'] or 0, r['tS'] or 0, r['cmax'], r['need'], r['gap'], r['rival']))

OUT.close()
print('done rows=%d blocked=%d' % (len(rows), len(blocked)))
