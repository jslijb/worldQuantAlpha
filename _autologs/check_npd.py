# -*- coding: utf-8 -*-
"""check_npd.py —— 验证 npdO71xw 的真实相关分布 + 盘点账号里 51 条 TOP1000"""
import os, io, json, statistics as st
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant'); os.chdir(ROOT)
OUT = io.open('_autologs/_check_npd.txt', 'w', encoding='utf-8')
L = []
def w(s=''):
    L.append(str(s)); OUT.write(str(s) + '\n')

PC = ROOT / 'data/alpha_quality_analysis/pnl'
POOL_S = ROOT / 'data/alpha_quality_analysis/pool_s.json'

pool = []
for ln in open(ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read().splitlines()[1:]:
    a = ln.split(',')[0].strip('"')
    if a and a not in pool:
        pool.append(a)
PS = json.load(open(POOL_S, encoding='utf-8'))

def pnl(aid):
    return {k: float(v) for k, v in json.load(open(PC / f'{aid}.json', encoding='utf-8')).items()}

def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300:
        return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5; sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy:
        return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)

# --- 1. npdO71xw 真实相关分布 ---
w('== npdO71xw 与 107 条池子的完整相关分布 ==')
x = pnl('npdO71xw')
w('  自身 PnL 天数: %d, 日期范围 %s ~ %s' % (len(x), min(x), max(x)))
vals = []
for q in pool:
    try:
        p = pnl(q)
    except Exception:
        continue
    v = corr(x, p)
    if v is not None:
        vals.append((v, q, PS.get(q)))
vals.sort(reverse=True)
w('  有效比较 %d 条' % len(vals))
w('  corr 分布: max=%.4f p90=%.4f 中位=%.4f min=%.4f' % (
    vals[0][0], sorted(v for v, _, _ in vals)[int(len(vals) * 0.9)], st.median([v for v, _, _ in vals]), vals[-1][0]))
w('  最相关的 12 条:')
for v, q, s in vals[:12]:
    w('    %-12s corr=%.4f  S=%s' % (q, v, s))
w('  超过 0.40 的有 %d 条；超过 0.50 的 %d 条；超过 0.66(收名单地板) 的 %d 条' % (
    len([1 for v, _, _ in vals if v > 0.40]), len([1 for v, _, _ in vals if v > 0.50]),
    len([1 for v, _, _ in vals if v >= 0.66])))

# --- 2. 账号全部 TOP1000 / TOP2000 / TOP500 / TOP200 ---
w('')
w('=' * 120)
w('== 账号全部非 TOP3000 条目（76 条）==')
data = json.load(io.open(ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
led = set(pool)
def g(d, *p, default=None):
    cur = d
    for k in p:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur
rows = []
for a in data:
    s = a.get('settings') or {}
    if s.get('universe') == 'TOP3000':
        continue
    ch = g(a, 'is', 'checks', default=[]) or []
    rows.append(dict(id=a.get('id'), uni=s.get('universe'), neu=s.get('neutralization'),
                     dly=s.get('delay'), dec=s.get('decay'), trunc=s.get('truncation'),
                     S=g(a, 'is', 'sharpe'), F=g(a, 'is', 'fitness'), TO=g(a, 'is', 'turnover'),
                     tS=g(a, 'test', 'sharpe'),
                     sf=(g(a, 'is', 'sharpe') or 0) + (g(a, 'is', 'fitness') or 0),
                     fails=[c.get('name') for c in ch if c and c.get('result') == 'FAIL'],
                     code=(g(a, 'regular', 'code') or '')[:120]))
rows.sort(key=lambda r: -(r['F'] or 0))
hdr = '%-11s %-8s %-13s %-4s %-4s %6s %6s %7s %6s %6s %s'
w(hdr % ('id', 'universe', 'neut', 'dly', 'dec', 'S', 'F', 'TO', 'tS', 'SF', 'FAIL'))
for r in rows:
    w(hdr % (r['id'], r['uni'], str(r['neu'])[:13], r['dly'], r['dec'],
             '%.2f' % r['S'], '%.2f' % r['F'], '%.3f' % r['TO'], '%.2f' % (r['tS'] or -1),
             '%.2f' % r['sf'], ','.join(r['fails'])[:24]))
w('')
w('TOP1000 条目表达式样本（前 12 条）:')
for r in [x for x in rows if x['uni'] == 'TOP1000'][:12]:
    w('  %-11s S=%.2f F=%.2f TO=%.3f tS=%.2f %s' % (r['id'], r['S'], r['F'], r['TO'], r['tS'] or -1, r['code']))
w('')
w('其余池 (TOP2000/TOP500/TOP200) 表达式样本:')
for r in [x for x in rows if x['uni'] != 'TOP1000'][:14]:
    w('  %-11s %-8s S=%.2f F=%.2f TO=%.3f tS=%.2f %s' % (r['id'], r['uni'], r['S'], r['F'], r['TO'], r['tS'] or -1, r['code']))
OUT.close(); print('ok')
