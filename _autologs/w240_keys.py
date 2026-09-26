# -*- coding: utf-8 -*-
"""w240_keys.py —— 列 w240/w241 的 combo 键（自写 UTF-8）"""
import io, json

ROOT = 'D:/Python/worldquant/'
L = []
for tag in ('w238', 'w239', 'w240', 'w241'):
    f = ROOT + '_autologs/leg_combos_%s.json' % tag
    try:
        d = json.load(io.open(f, encoding='utf-8'))
    except Exception as e:
        L.append('%s: %s' % (tag, e)); continue
    L.append('=== %s  n=%d ===' % (tag, len(d)))
    L.append('  ' + ' | '.join(d.keys()))
    L.append('')
io.open(ROOT + '_autologs/_w240_keys.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
