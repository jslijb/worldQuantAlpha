# -*- coding: utf-8 -*-
"""pnl_corr.py —— 本地算 self-correlation，免提交

原理：平台对每个 alpha 都开放 PnL 序列端点
      GET /alphas/{id}/recordsets/pnl  -> {schema, records:[[date, pnl], ...]}
      selfCorrelation 就是对已提交池里其它 alpha 的日 PnL 求 Pearson 相关。
      所以：只要拿到候选 alpha 的 PnL（模拟完就有），就能在本地算出它会撞谁、撞多少，
      **不需要提交、不污染池子、不排队**。

用法：
    python src/analysis/pnl_corr.py <alpha_id> [<alpha_id2> ...]
    python src/analysis/pnl_corr.py w154_b            # 支持 mined json 里的 cid 简写
选项：
    --top N      只打印相关最高的 N 个对手（默认 8）
    --refresh     忽略缓存重新拉取
产出：
    data/alpha_quality_analysis/pnl/{alpha_id}.json   缓存
"""
import os as _os, pathlib as _pl, sys, json, time

_p = _pl.Path(__file__).resolve()
ROOT = None
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        ROOT = _d; _os.chdir(_d); break
assert ROOT

import requests

LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
MINED = 'data/alpha_quality_analysis/mined'
CACHE = 'data/alpha_quality_analysis/pnl'
_os.makedirs(CACHE, exist_ok=True)

_ARGV = []
_i = 1
while _i < len(sys.argv):
    a = sys.argv[_i]
    if a == '--top':
        _i += 2; continue
    if a.startswith('--'):
        _i += 1; continue
    _ARGV.append(a); _i += 1
TOP = int(sys.argv[sys.argv.index('--top') + 1]) if '--top' in sys.argv else 8
REFRESH = '--refresh' in sys.argv


def sess():
    s = requests.Session()
    s.auth = tuple(json.load(open('brain_credentials.txt')))
    assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201, '认证失败'
    return s


S = sess()


def ledger_ids():
    import csv
    ids = []
    with open(LEDGER, newline='', encoding='utf-8') as f:
        for row in csv.reader(f):
            if len(row) >= 1 and len(row[0]) == 8 and row[0].isalnum():
                if row[0] not in ids:
                    ids.append(row[0])
    return ids


def cid2id(cid):
    """把 w154_b 这种批内编号映射成 alpha id"""
    if len(cid) == 8:
        return cid
    p = _pl.Path(MINED) / f'{cid}.json'
    if p.exists():
        d = json.load(open(p, encoding='utf-8'))
        if d.get('id'):
            return d['id']
    hits = list(_pl.Path(MINED).glob(f'*{cid}*.json'))
    for h in hits:
        d = json.load(open(h, encoding='utf-8'))
        if d.get('_cid') == cid and d.get('id'):
            return d['id']
    raise SystemExit(f'找不到 {cid} 对应的 alpha id')


def get_pnl(aid, refresh=False):
    cp = _pl.Path(CACHE) / f'{aid}.json'
    if cp.exists() and not refresh:
        try:
            return json.load(open(cp, encoding='utf-8'))
        except Exception:
            pass
    for att in range(6):
        try:
            r = S.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            time.sleep(5); continue
        if r.status_code == 429 or r.headers.get('Retry-After'):
            time.sleep(float(r.headers.get('Retry-After') or 5)); continue
        if r.status_code != 200:
            time.sleep(3); continue
        try:
            j = r.json()
        except Exception:
            time.sleep(2); continue
        recs = j.get('records') or []
        if not recs:
            time.sleep(2); continue
        # 平台给的是【累计 PnL】，必须先差分成【日 PnL】，否则任意两条都是 0.99 相关
        raw = [(str(x[0]), float(x[1])) for x in recs if len(x) >= 2 and x[1] is not None]
        raw.sort()
        ser = {}
        for k in range(1, len(raw)):
            ser[raw[k][0]] = raw[k][1] - raw[k - 1][1]
        json.dump(ser, open(cp, 'w', encoding='utf-8'))
        return ser
    return None


def corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 60:
        return None, len(keys)
    xs = [a[k] for k in keys]; ys = [b[k] for k in keys]
    n = len(xs)
    mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    if vx == 0 or vy == 0:
        return None, n
    return cov / (vx * vy), n


if not _ARGV:
    print(__doc__); sys.exit(0)

pool = ledger_ids()
print(f'已提交池 {len(pool)} 个 alpha；预取 PnL（有缓存则跳过）...', flush=True)
pool_pnl = {}
for i, aid in enumerate(pool):
    s = get_pnl(aid, refresh=REFRESH)
    if s:
        pool_pnl[aid] = s
    if (i + 1) % 10 == 0:
        print(f'  {i+1}/{len(pool)}', flush=True)
print(f'成功取到 {len(pool_pnl)}/{len(pool)} 条 PnL\n', flush=True)

ledger_sharpe = {}
import csv as _csv
with open(LEDGER, newline='', encoding='utf-8') as f:
    for row in _csv.reader(f):
        if len(row) >= 4 and len(row[0]) == 8:
            try:
                ledger_sharpe.setdefault(row[0], float(row[2]))
            except Exception:
                pass

for cid in _ARGV:
    aid = cid2id(cid)
    cur = get_pnl(aid, refresh=REFRESH)
    if not cur:
        print(f'{cid} ({aid}) 取不到 PnL'); continue
    res = []
    for pid, ps in pool_pnl.items():
        if pid == aid:
            continue
        c, n = corr(cur, ps)
        if c is not None:
            res.append((c, pid, ledger_sharpe.get(pid), n))
    res.sort(reverse=True)
    mx = res[0][0] if res else 0
    print(f'===== {cid} ({aid}) =====')
    print(f'  {"对手":<10} {"corr":>8} {"S":>6}  豁免线(1.1*S)')
    for c, pid, sh, n in res[:TOP]:
        flag = ' <== 撞' if c >= 0.7 else ''
        sl = f'{1.1*sh:.3f}' if sh else '?'
        print(f'  {pid:<10} {c:>8.4f} {sh if sh else "?":>6}  {sl}{flag}')
    print(f'  --- 本地 max corr = {mx:.4f}  → {"直通 OK" if mx < 0.7 else "需豁免 / 会被拒"}')
    over = [(c, pid, sh) for c, pid, sh, _ in res if c >= 0.7 and sh]
    if over:
        need = 1.1 * max(sh for _, _, sh in over)
        print(f'  豁免线 = 1.10 x max(对手 S) = {need:.3f}')
    print()
