# -*- coding: utf-8 -*-
"""pool_diag.py —— 用缓存的日 PnL 做全池相关性诊断（免费、不发提交）

产出：
  1) 每个已提交 alpha 的 max corr + 最近邻（找出池子里"最与众不同"的成员）
  2) kqoq0zed / 热对手的最近邻明细
  3) 指定候选之间的互相关矩阵
"""
import os as _os, pathlib as _pl, sys, json, csv, itertools

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

CACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

S_, NAME_ = {}, {}
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if len(row) >= 4 and len(row[0]) == 8:
        try:
            S_.setdefault(row[0], float(row[2]))
        except Exception:
            pass
    if len(row) >= 12 and len(row[0]) == 8:
        NAME_.setdefault(row[0], row[11])


def load(aid):
    p = _pl.Path(CACHE) / f'{aid}.json'
    if not p.exists():
        return None
    try:
        return json.load(open(p, encoding='utf-8'))
    except Exception:
        return None


def corr(a, b):
    keys = sorted(set(a) & set(b))
    if len(keys) < 120:
        return None
    xs = [a[k] for k in keys]; ys = [b[k] for k in keys]
    n = len(xs); mx = sum(xs) / n; my = sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    if vx == 0 or vy == 0:
        return None
    return cov / (vx * vy)


pnl = {}
for f in _pl.Path(CACHE).glob('*.json'):
    d = load(f.stem)
    if d:
        pnl[f.stem] = d
print(f'缓存到 {len(pnl)} 条日 PnL\n')

ids = list(pnl)
mode = sys.argv[1] if len(sys.argv) > 1 else 'pool'
args = sys.argv[2:]

if mode == 'pool':
    rows = []
    for a in ids:
        best = None
        for b in ids:
            if a == b:
                continue
            c = corr(pnl[a], pnl[b])
            if c is None:
                continue
            if best is None or c > best[0]:
                best = (c, b)
        if best:
            rows.append((best[0], a, best[1], S_.get(a)))
    rows.sort()
    print(f'{"alpha":<10}{"maxCorr":>9}{"S":>7}  最近邻')
    print('---- 池里最"与众不同"的 12 个 ----')
    for c, a, b, s in rows[:12]:
        print(f'{a:<10}{c:>9.4f}{s if s else "?":>7}  {b} ({NAME_.get(a,"")})')
    print('\n---- 池里最"挤"的 12 个 ----')
    for c, a, b, s in rows[-12:]:
        print(f'{a:<10}{c:>9.4f}{s if s else "?":>7}  {b} ({NAME_.get(a,"")})')

elif mode == 'near':
    for a in args:
        if a not in pnl:
            print(f'{a} 无缓存'); continue
        res = []
        for b in ids:
            if b == a:
                continue
            c = corr(pnl[a], pnl[b])
            if c is not None:
                res.append((c, b, S_.get(b)))
        res.sort(reverse=True)
        print(f'===== {a} (S={S_.get(a)}) 最近邻 =====')
        for c, b, s in res[:12]:
            print(f'  {b:<10}{c:>9.4f}  S={s if s else "?"}  {NAME_.get(b,"")}')
        print()

elif mode == 'matrix':
    print('互相关矩阵：')
    print('        ' + ''.join(f'{a:>10}' for a in args))
    for a in args:
        if a not in pnl:
            print(f'{a} 无缓存'); continue
        line = f'{a:<8}'
        for b in args:
            if b not in pnl:
                line += f'{"?":>10}'
            else:
                c = corr(pnl[a], pnl[b])
                line += f'{(c if c is not None else float("nan")):>10.4f}'
        print(line)
