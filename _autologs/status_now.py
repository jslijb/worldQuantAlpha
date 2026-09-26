# -*- coding: utf-8 -*-
"""status_now.py —— 当前全局状态：批次进度 + 实时判决日志尾部 + 提交裁决尾部"""
import json, io, os, datetime

OUT = 'data/alpha_quality_analysis/mined'
TAGS = ['w239', 'w240', 'w241', 'w242', 'w243']
L = []

L.append('== 批次进度 ==')
for tag in TAGS:
    f = '_autologs/leg_combos_%s.json' % tag
    if not os.path.exists(f):
        L.append('  %s: (无 combos)' % tag)
        continue
    c = json.load(io.open(f, encoding='utf-8'))
    done = sum(1 for cid in c if os.path.exists('%s/%s.json' % (OUT, cid)))
    L.append('  %s: %d/%d' % (tag, done, len(c)))

L.append('')
L.append('== _autologs 最新 30 个文件 ==')
fs = []
for x in os.listdir('_autologs'):
    p = os.path.join('_autologs', x)
    if os.path.isfile(p):
        fs.append((os.path.getmtime(p), x, os.path.getsize(p)))
fs.sort(reverse=True)
for m, x, s in fs[:30]:
    L.append('  %s  %8d  %s' % (datetime.datetime.fromtimestamp(m).strftime('%m-%d %H:%M:%S'), s, x))

def tail(path, keys=None, n=40):
    if not os.path.exists(path):
        L.append('  (缺文件 %s)' % path)
        return
    raw = io.open(path, 'rb').read()
    t = None
    for enc in ('utf-8', 'utf-16', 'gbk'):
        try:
            t = raw.decode(enc)
            break
        except Exception:
            pass
    if t is None:
        L.append('  (%s 编码不可读)' % path)
        return
    lines = t.splitlines()
    if keys:
        lines = [x for x in lines if any(k in x for k in keys)]
    L.append('  --- %s (共 %d 行, 取尾 %d) ---' % (os.path.basename(path), len(lines), n))
    for x in lines[-n:]:
        L.append('    ' + x)

L.append('')
L.append('== 实时判决/提交日志尾部 ==')
for cand in ['_autologs/_realtime.txt', '_autologs/_realtime2.txt',
             '_autologs/_judge_run.txt', '_autologs/_judge_run2.txt',
             '_autologs/_live.txt', '_autologs/_live2.txt']:
    if os.path.exists(cand):
        tail(cand, None, 40)

L.append('')
L.append('== mined 目录里最近 20 个新产出 ==')
fs2 = []
for x in os.listdir(OUT):
    p = os.path.join(OUT, x)
    fs2.append((os.path.getmtime(p), x))
fs2.sort(reverse=True)
for m, x in fs2[:20]:
    L.append('  %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%m-%d %H:%M:%S'), x))

io.open('_autologs/_status_now.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
