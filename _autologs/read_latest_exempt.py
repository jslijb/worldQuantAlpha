# -*- coding: utf-8 -*-
"""read_latest_exempt.py —— 汇总最近 3 份判决日志"""
import io, os, glob

L = []
fs = sorted(glob.glob('_autologs/exempt_*.log'), key=os.path.getmtime)
L.append('共 %d 份日志，最近 3 份：' % len(fs))
for f in fs[-3:]:
    L.append('  %s  %s' % (os.path.basename(f), __import__('time').strftime('%m-%d %H:%M:%S', __import__('time').localtime(os.path.getmtime(f)))))

for f in fs[-2:]:
    L.append('\n' + '=' * 78)
    L.append('FILE %s' % os.path.basename(f))
    L.append('=' * 78)
    t = io.open(f, encoding='utf-8', errors='replace').read()
    for ln in t.splitlines():
        # 只留判定行与摘要行，去掉超长的"全名单"
        if '全名单[' in ln:
            ln = ln.split('| 全名单')[0]
        L.append(ln)

io.open('_autologs/_latest_exempt.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
