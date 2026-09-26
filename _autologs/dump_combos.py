# -*- coding: utf-8 -*-
"""dump w236~w240 combos 结构 + 与 O0N5o3Nv(A_MAR) 的腿重叠检查（自写 UTF-8）"""
import io, json, os

ROOT = 'D:/Python/worldquant/'
L = []

for tag in ('w236', 'w237', 'w238', 'w239', 'w240'):
    f = ROOT + '_autologs/leg_combos_%s.json' % tag
    if not os.path.exists(f):
        L.append('%s: 文件不存在' % tag); continue
    c = json.load(io.open(f, encoding='utf-8'))
    L.append('=== %s  n=%d  type=%s ===' % (tag, len(c), type(c).__name__))
    if isinstance(c, dict):
        ks = list(c.keys())
        L.append('  keys(前5): %s' % ks[:5])
        first = c[ks[0]]
        L.append('  样本 [%s] -> %s' % (ks[0], json.dumps(first, ensure_ascii=False)[:600]))
    else:
        L.append('  样本[0] -> %s' % json.dumps(c[0], ensure_ascii=False)[:600])
    L.append('')

L.append('=== A_MAR (O0N5o3Nv) 台账表达式 ===')
import csv
raw = io.open(ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', 'rb').read().decode('utf-8-sig')
for r in csv.reader(io.StringIO(raw)):
    if r and r[0].strip() == 'O0N5o3Nv':
        L.append('  ' + r[1])

io.open(ROOT + '_autologs/_combos_dump.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
