# -*- coding: utf-8 -*-
import json, io
L = []
d = json.load(io.open('data/alpha_quality_analysis/mined/kqjpepz8_v2.json', encoding='utf-8'))
L.append('top keys: ' + str(list(d.keys())))
r = d.get('regular') or {}
L.append('regular keys: ' + str(list(r.keys())))
L.append('code: ' + str(r.get('code'))[:400])
L.append('_decay=%s _neut=%s _trunc=%s' % (d.get('_decay'), d.get('_neut'), d.get('_trunc')))
io.open('_autologs/_probe_structure.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
