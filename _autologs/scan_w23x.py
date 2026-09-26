# -*- coding: utf-8 -*-
"""scan_w23x.py —— 扫描 w232/w234/w235 产出，按 Fitness 排序，标注换手率档位与守门结果"""
import json, os

OUT = 'data/alpha_quality_analysis/mined'
TAGS = ('w232', 'w234', 'w235')

# 收集本批 cid
cids = []
for tag in TAGS:
    f = f'_autologs/leg_combos_{tag}.json'
    if not os.path.exists(f):
        continue
    for cid in json.load(open(f, encoding='utf-8')):
        cids.append((tag, cid))

rows = []
for tag, cid in cids:
    p = f'{OUT}/{cid}.json'
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding='utf-8'))
    b = d.get('is') or {}
    te = d.get('test') or {}
    S = b.get('sharpe') or 0
    F = b.get('fitness') or 0
    TO = b.get('turnover')
    tS = te.get('sharpe') or 0
    ret = b.get('returns') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    margin = (ret / TO * 10000 * 100) if (TO and ret) else 0  # bp per 1% TO -> approx bp
    ok = (S + F >= 4.0) and (tS >= 1.25) and (not fa)
    rows.append(dict(tag=tag, cid=cid, S=S, F=F, SF=S + F, TO=TO, tS=tS, ret=ret,
                     ne=d.get('_neut'), dec=d.get('_decay'), tr=d.get('_trunc'),
                     fa=fa, ok=ok, expr=(d.get('regular') or {}).get('code', '')))

rows.sort(key=lambda r: -r['F'])
L = []
L.append('== 达标（S+F>=4.0 & tS>=1.25 & 无FAIL）按 Fitness 排序 ==')
hits = [r for r in rows if r['ok']]
for r in hits:
    L.append('  %-22s %-6s S=%.2f F=%.2f SF=%.2f TO=%s tS=%.2f ret=%.4f [%s/%s/%s]'
             % (r['cid'], r['tag'], r['S'], r['F'], r['SF'],
                ('%.2f%%' % (r['TO'] * 100)) if r['TO'] else 'NA', r['tS'], r['ret'],
                r['ne'], r['dec'], r['tr']))
if not hits:
    L.append('  (无)')

L.append('')
L.append('== 未达标但 F>=2.0 或 SF>=3.8 的（观察换手率改善） ==')
near = [r for r in rows if not r['ok'] and (r['F'] >= 2.0 or r['SF'] >= 3.8)]
near.sort(key=lambda r: -r['F'])
for r in near[:30]:
    L.append('  %-22s %-6s S=%.2f F=%.2f SF=%.2f TO=%s tS=%.2f FAIL=%s'
             % (r['cid'], r['tag'], r['S'], r['F'], r['SF'],
                ('%.2f%%' % (r['TO'] * 100)) if r['TO'] else 'NA', r['tS'], r['fa']))
if not near:
    L.append('  (无)')

L.append('')
L.append('== 已产出总数 %d ==' % len(rows))
open('_autologs/_scan_w23x.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok', len(rows), len(hits))
