# -*- coding: utf-8 -*-
"""batch_status.py —— 汇总各批次进度 + 从运行日志里提取达标/★PASS 结果（自写 UTF-8）"""
import json, io, os, datetime

OUT = 'data/alpha_quality_analysis/mined'
TAGS = ('w236', 'w237', 'w238', 'w239', 'w240', 'w241', 'w242')
RUNS = {t: '_autologs/_%s_run%s.txt' % (t, '' if t in ('w233', 'w234', 'w235', 'w232') else '2')
        for t in TAGS}

L = []
for tag in TAGS:
    f = f'_autologs/leg_combos_{tag}.json'
    if not os.path.exists(f):
        L.append('%s: (无 combos)' % tag)
        continue
    c = json.load(io.open(f, encoding='utf-8'))
    done = sum(1 for cid in c if os.path.exists(f'{OUT}/{cid}.json'))
    L.append('%s: %d/%d 有产出' % (tag, done, len(c)))

L.append('')
L.append('== mined 最新 12 ==')
fs = [(os.path.getmtime(os.path.join(OUT, x)), x) for x in os.listdir(OUT)]
fs.sort(reverse=True)
for m, x in fs[:12]:
    L.append('  %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%m-%d %H:%M:%S'), x))

L.append('')
L.append('== 各批 run 日志尾部（★PASS / fail 行）==')
for tag in TAGS:
    for cand in (f'_autologs/_{tag}_run2.txt', f'_autologs/_{tag}_run.txt'):
        if not os.path.exists(cand):
            continue
        try:
            raw = io.open(cand, 'rb').read()
        except Exception:
            continue
        for enc in ('utf-8', 'utf-16', 'gbk'):
            try:
                t = raw.decode(enc)
                break
            except Exception:
                t = None
        if not t:
            continue
        lines = [x for x in t.splitlines() if 'SF=' in x]
        if lines:
            L.append('  --- %s (%d 条) ---' % (os.path.basename(cand), len(lines)))
            L += ['    ' + x for x in lines[-14:]]
        break

io.open('_autologs/_batch_status.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
