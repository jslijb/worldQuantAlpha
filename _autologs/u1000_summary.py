# -*- coding: utf-8 -*-
"""u1000_summary.py —— 换池批次（TOP1000/TOP500）质量汇总 + FAIL 体检"""
import os as _os, pathlib as _pl, json, glob, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

L = []
rows = []
for f in sorted(glob.glob('data/alpha_quality_analysis/mined/u1000_*.json')):
    d = json.load(io.open(f, encoding='utf-8'))
    b = d.get('is') or {}; te = d.get('test') or {}; st = d.get('settings') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    TO = b.get('turnover') or 0; tS = te.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    rows.append(dict(cid=d.get('_cid'), aid=d.get('id'), uni=d.get('_univ'), src=d.get('_src'),
                     S=S, F=F, TO=TO, tS=tS, fa=fa, mg=(b.get('margin') or 0) * 10000,
                     dec=st.get('decay'), neu=st.get('neutralization')))

rows.sort(key=lambda x: -(x['F'] or 0))
L.append('换池批次 u1000（TOP1000/TOP500）落盘 %d 条' % len(rows))
L.append('=' * 132)
L.append('%-26s %-10s %-9s %5s %6s %6s %6s %7s %6s | %s'
         % ('cid', 'aid', 'pool', 'dec', 'S', 'F', 'TO', 'tS', 'margin', 'FAIL'))
L.append('-' * 132)
for r in rows:
    L.append('%-26s %-10s %-9s %5s %6.3f %6.3f %6.4f %7.2f %6.1f | %s'
             % (r['cid'][:26], r['aid'], r['uni'], r['dec'], r['S'], r['F'], r['TO'],
                r['tS'], r['mg'], ','.join(r['fa']) if r['fa'] else '—'))

gate = [r for r in rows if not r['fa'] and r['S'] + r['F'] >= 4.0 and r['tS'] >= 1.25 and r['TO'] <= 0.20]
top1 = [r for r in rows if r['uni'] == 'TOP1000']
top5 = [r for r in rows if r['uni'] == 'TOP500']
L.append('')
L.append('=' * 132)
L.append('过质量闸门（无FAIL & S+F>=4.0 & tS>=1.25 & TO<=20%%）= %d 条' % len(gate))
for r in gate:
    L.append('   %-26s %-10s %-9s S=%.2f F=%.2f TO=%.4f tS=%.2f margin=%.1fbp'
             % (r['cid'], r['aid'], r['uni'], r['S'], r['F'], r['TO'], r['tS'], r['mg']))
L.append('')
L.append('分池统计：TOP1000 %d 条（过闸 %d / 带FAIL %d）；TOP500 %d 条（过闸 %d / 带FAIL %d）'
         % (len(top1), len([r for r in top1 if r in gate]), len([r for r in top1 if r['fa']]),
            len(top5), len([r for r in top5 if r in gate]), len([r for r in top5 if r['fa']])))
# 源 → 小池 的 Fitness 代价
L.append('')
L.append('Fitness 代价（源 TOP3000 → 小池版）：')
L.append('  %-26s %-9s %-8s %-8s %s' % ('cid', 'pool', 'srcF', 'newF', '跌幅'))
srcF = {}
import re
try:
    for ln in io.open('_autologs/_univ_run.txt', encoding='utf-8', errors='ignore'):
        m = re.match(r'^\s*src\s+(\w+)\s+S=([\d.]+)\s+F=([\d.]+)', ln)
        if m:
            srcF[m.group(1)] = float(m.group(3))
except Exception:
    pass
for r in sorted(rows, key=lambda x: -(x['F'] or 0))[:16]:
    s = srcF.get(r['src'])
    if s:
        L.append('  %-26s %-9s %-8.2f %-8.2f %+.2f' % (r['aid'], r['uni'], s, r['F'], r['F'] - s))

io.open('_autologs/_u1000_summary.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done %d' % len(rows))
