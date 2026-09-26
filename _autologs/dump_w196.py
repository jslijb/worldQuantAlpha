# -*- coding: utf-8 -*-
import json, io, os
os.chdir('D:/Python/worldquant/')
L = []
for cid in ('w196_04',):
    p = 'data/alpha_quality_analysis/mined/%s.json' % cid
    d = json.load(io.open(p, encoding='utf-8'))
    i = d.get('is') or {}; t = d.get('test') or {}
    L.append('cid=%s aid=%s' % (d.get('_cid'), d.get('id')))
    L.append('  S=%s F=%s TO=%s R=%s DD=%s margin=%s' % (i.get('sharpe'), i.get('fitness'),
             i.get('turnover'), i.get('returns'), i.get('drawdown'), i.get('margin')))
    L.append('  tS=%s tF=%s' % (t.get('sharpe'), t.get('fitness')))
    L.append('  neut=%s decay=%s trunc=%s ops=%s' % (d.get('_neut'), d.get('_decay'),
             d.get('_trunc'), (d.get('regular') or {}).get('operatorCount')))
    L.append('  FAIL=%s' % [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL'])
    reg = d.get('regular') or {}
    L.append('  code: %s' % (reg.get('code') if isinstance(reg, dict) else reg))
io.open('_autologs/_w196_04.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
