# -*- coding: utf-8 -*-
"""final_status.py —— 收尾汇总：台账终值 / 美东当日入池清单 / 新批次产出（自写 UTF-8）"""
import io, csv, os, json, glob, datetime

ROOT = 'D:/Python/worldquant/'
L = []

raw = io.open(ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', 'rb').read().decode('utf-8-sig')
rows = [r for r in csv.reader(io.StringIO(raw)) if r and r[0].strip()]
hdr, data = rows[0], rows[1:]
ids = []
for r in data:
    if r[0].strip() and r[0].strip() != 'id':
        ids.append(r[0].strip())
uniq = list(dict.fromkeys(ids))
L.append('台账行数(不含表头): %d   唯一 id: %d   重复: %d' % (len(data), len(uniq), len(ids) - len(uniq)))
L.append('id 列索引: %d (%s)' % (hdr.index('id'), hdr[0]))

# 美东当日
today = [r for r in data if len(r) > 8 and r[8].startswith('2026-09-20')]
L.append('')
L.append('== 美东 2026-09-20 入池 %d 条 ==' % len(today))
L.append('  %-11s %6s %6s %8s %10s %s' % ('id', 'S', 'F', 'TO', 'selfCorr', 'batch'))
for r in sorted(today, key=lambda x: x[8]):
    L.append('  %-11s %6s %6s %8s %10s %s' % (r[0], r[2], r[3], r[4], r[7], (r[11] if len(r) > 11 else '')[:40]))

L.append('')
L.append('== 新批次产出计数 ==')
for tag in ('w239', 'w240', 'w241', 'w242', 'w243'):
    f = ROOT + '_autologs/leg_combos_%s.json' % tag
    if not os.path.exists(f):
        continue
    c = json.load(io.open(f, encoding='utf-8'))
    done = [k for k in c if os.path.exists(ROOT + 'data/alpha_quality_analysis/mined/%s.json' % k)]
    L.append('  %s: %d/%d' % (tag, len(done), len(c)))

L.append('')
L.append('== mined 最新 15 个产出 ==')
fs = sorted(((os.path.getmtime(os.path.join(ROOT + 'data/alpha_quality_analysis/mined', x)), x)
             for x in os.listdir(ROOT + 'data/alpha_quality_analysis/mined')), reverse=True)
for m, x in fs[:15]:
    L.append('  %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%H:%M:%S'), x))

io.open(ROOT + '_autologs/_final_status.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
