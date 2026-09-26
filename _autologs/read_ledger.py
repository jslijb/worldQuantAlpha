# -*- coding: utf-8 -*-
"""读台账：先原样 dump 头部若干行，再看结构（自写 UTF-8）"""
import io, csv

ROOT = 'D:/Python/worldquant/'
p = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
raw = io.open(p, 'rb').read()
t = None
for enc in ('utf-8-sig', 'utf-8', 'gbk', 'utf-16'):
    try:
        t = raw.decode(enc); used = enc; break
    except Exception:
        t = None

L = ['文件: ' + p, '大小: %d bytes' % len(raw), '编码: %s' % (t and used)]
rows = list(csv.reader(io.StringIO(t)))
rows = [r for r in rows if any(x.strip() for x in r)]
L.append('有效行数: %d' % len(rows))
L.append('')
L.append('== 前 6 行原样 ==')
for i, r in enumerate(rows[:6]):
    L.append('  [%d] ncol=%d :: %s' % (i, len(r), ' | '.join(r)))
L.append('')
L.append('== 末 12 行原样 ==')
for r in rows[-12:]:
    L.append('  ncol=%d :: %s' % (len(r), ' | '.join(r)))

io.open(ROOT + '_autologs/_ledger_tail.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
