# -*- coding: utf-8 -*-
"""dump_sweet.py —— 打印甜点区候选的表达式/设置，为定向提 S 做准备"""
import json, io, os

MINED = 'data/alpha_quality_analysis/mined'
TARGETS = ['x162_w164_00_MAR', 'x162_w164_04_MAR', 'w189_01__g_bdv',
           'w39_i', 'w41_c', 'w41_b', 'w215_w54x', 'w222_i']
L = []
for cid in TARGETS:
    p = f'{MINED}/{cid}.json'
    if not os.path.exists(p):
        L.append('%-24s (无产出)' % cid); continue
    d = json.load(io.open(p, encoding='utf-8'))
    s = d.get('settings') or {}
    reg = d.get('regular') or {}
    i = d.get('is') or {}
    L.append('=== %s  S=%.2f F=%.2f TO=%.2f%% tS=%.2f neut=%s decay=%s trunc=%s opc=%s'
             % (cid, i.get('sharpe') or 0, i.get('fitness') or 0, (i.get('turnover') or 0) * 100,
                ((d.get('test') or {}).get('sharpe') or 0), s.get('neutralization'),
                s.get('decay'), s.get('truncation'), reg.get('operatorCount')))
    L.append('    ' + (reg.get('code') or ''))
io.open('_autologs/_dump_sweet.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
