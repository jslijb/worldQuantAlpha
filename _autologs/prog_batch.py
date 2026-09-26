# -*- coding: utf-8 -*-
"""prog_batch.py —— 报告指定 combos 批次的完成进度（自写 UTF-8）"""
import json, os, io, sys

OUT = 'data/alpha_quality_analysis/mined'
lines = []
for tag in ('w232', 'w233', 'w234', 'w235', 'w236'):
    f = f'_autologs/leg_combos_{tag}.json'
    if not os.path.exists(f):
        lines.append(f'{tag}: (无 combos 文件)')
        continue
    c = json.load(open(f, encoding='utf-8'))
    tot = len(c)
    done, new = 0, []
    for cid in c:
        p = f'{OUT}/{cid}.json'
        if os.path.exists(p):
            done += 1
            new.append((os.path.getmtime(p), cid))
    new.sort(reverse=True)
    lines.append(f'{tag}: {done}/{tot} 有产出')
    for m, cid in new[:6]:
        import datetime
        lines.append('    %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%H:%M:%S'), cid))

lines.append('')
lines.append('== mined 目录里 mtime 最新的 15 个 ==')
fs = [(os.path.getmtime(os.path.join(OUT, x)), x) for x in os.listdir(OUT)]
fs.sort(reverse=True)
import datetime
for m, x in fs[:15]:
    lines.append('  %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%m-%d %H:%M:%S'), x))

open('_autologs/_prog_batch.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('ok')
