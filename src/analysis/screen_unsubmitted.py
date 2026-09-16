# -*- coding: utf-8 -*-
"""screen_unsubmitted.py —— 把历史积压的达标候选一次性用【本地 corr】筛一遍

背景：456 条候选 S+F≥4.0 却从未提交，历史瓶颈是相关性墙。
      0916 起本地 PnL corr 可用（误差 ±0.02，见 src/analysis/pnl_corr.py），
      于是不必再"提交一次试一次"，可以离线全量筛查。

用法：
  python src/analysis/screen_unsubmitted.py [--min-sf 4.0] [--min-ts 1.25] [--max-corr 0.70]
产出：
  data/alpha_quality_analysis/screened_candidates.csv  按 max corr 升序
  控制台打印通过者
"""
import os as _os, pathlib as _pl, sys, json, csv, time

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

import requests

SRC = 'data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv'
OUT = 'data/alpha_quality_analysis/screened_candidates.csv'
PCACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

def opt(name, dflt):
    if name in sys.argv:
        i = sys.argv.index(name)
        return float(sys.argv[i + 1])
    return dflt

MIN_SF = opt('--min-sf', 4.0)
MIN_TS = opt('--min-ts', 1.25)
MAX_CORR = opt('--max-corr', 0.70)

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201

_pnl_mem = {}


def get_pnl(aid):
    if aid in _pnl_mem:
        return _pnl_mem[aid]
    cp = _pl.Path(PCACHE) / f'{aid}.json'
    if cp.exists():
        try:
            v = json.load(open(cp, encoding='utf-8'))
            _pnl_mem[aid] = v
            return v
        except Exception:
            pass
    v = None
    for _ in range(4):
        try:
            r = s.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            time.sleep(4); continue
        if r.status_code != 200 or r.headers.get('Retry-After'):
            time.sleep(float(r.headers.get('Retry-After') or 3)); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(2); continue
        recs = sorted((str(x[0]), float(x[1])) for x in (j.get('records') or []) if len(x) >= 2 and x[1] is not None)
        if len(recs) < 60:
            time.sleep(2); continue
        v = {recs[k][0]: recs[k][1] - recs[k - 1][1] for k in range(1, len(recs))}
        try:
            json.dump(v, open(cp, 'w', encoding='utf-8'))
        except Exception:
            pass
        break
    _pnl_mem[aid] = v
    return v


def crr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 200:
        return None
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    n = len(x); mx = sum(x) / n; my = sum(y) / n
    cov = sum((p - mx) * (q - my) for p, q in zip(x, y))
    vx = sum((p - mx) ** 2 for p in x) ** .5; vy = sum((q - my) ** 2 for q in y) ** .5
    return None if vx == 0 or vy == 0 else cov / (vx * vy)


# 池子 = **只认台账**（缓存目录里混着未提交的单腿/实验 alpha，混进来会虚高 corr 误杀候选）
LSH = {}
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if len(row) >= 4 and len(row[0]) == 8:
        try:
            LSH.setdefault(row[0], float(row[2]))
        except Exception:
            pass
pool = {}
for pid in LSH:
    p = get_pnl(pid)
    if p:
        pool[pid] = p
print(f'池子 {len(pool)} 条（台账 {len(LSH)}）；候选 {sum(1 for _ in open(SRC, encoding="utf-8"))-1} 条', flush=True)

rows = []
with open(SRC, newline='', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        rows.append(r)

done = 0
for r in rows:
    aid = r['id']
    try:
        sf = float(r['SF']); ts = float(r['tS'] or 0)
    except Exception:
        continue
    if sf < MIN_SF or ts < MIN_TS or (r.get('fails') or '').strip():
        continue
    p = get_pnl(aid)
    if p is None:
        r['maxcorr'] = 'PNL_NA'; rows_done = None
        continue
    mx = 0.0; who = ''
    for pid, pp in pool.items():
        if pid == aid:
            continue
        c = crr(p, pp)
        if c is not None and c > mx:
            mx = c; who = pid
    r['maxcorr'] = round(mx, 4); r['nearest'] = who
    done += 1
    if done % 25 == 0:
        print(f'  已筛 {done} 条...', flush=True)

ok = [r for r in rows if isinstance(r.get('maxcorr'), float)]
ok.sort(key=lambda r: r['maxcorr'])
with open(OUT, 'w', newline='', encoding='utf-8-sig') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), extrasaction='ignore')
    w.writeheader()
    for r in ok:
        w.writerow(r)

print(f'\n筛完 {len(ok)} 条，落盘 {OUT}\n')
print('===== max corr < 0.70 的候选（可直通）=====')
n = 0
for r in ok:
    if r['maxcorr'] < MAX_CORR:
        n += 1
        print(f"  {r['cid']:<8} {r['id']} SF={float(r['SF']):.2f} S={r['S']} tS={r['tS']} "
              f"maxcorr={r['maxcorr']:.4f} 最近邻={r['nearest']}")
if n == 0:
    print('  （无）')
print(f'\n===== 最低 corr 的 25 条（含未过 0.70 的）=====')
for r in ok[:25]:
    print(f"  {r['cid']:<8} {r['id']} SF={float(r['SF']):.2f} maxcorr={r['maxcorr']:.4f} 最近邻={r['nearest']}")
