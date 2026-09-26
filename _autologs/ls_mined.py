# -*- coding: utf-8 -*-
"""ls_mined.py —— 列最近写入的 mined json + 定位 w240 批次文件"""
import io, os, glob, time

L = []
d = 'data/alpha_quality_analysis/mined'
fs = glob.glob(os.path.join(d, '*.json'))
fs.sort(key=lambda f: -os.path.getmtime(f))
L.append('mined json 总数 %d' % len(fs))
L.append('== 最近写入 15 个 ==')
for f in fs[:15]:
    L.append('  %-24s %s' % (os.path.basename(f), time.strftime('%m-%d %H:%M', time.localtime(os.path.getmtime(f)))))

# 用 w240 里的 id 反查文件
TARGETS = ['ZYbWAGQ8', 'levR8Gz2', 'qMxm09pZ', 'VkaYaL7M', '9qjAVLRV', 'Grb3lkx0', 'YPbWbMkJ']
found = {}
for f in fs[:400]:
    try:
        t = io.open(f, encoding='utf-8', errors='ignore').read()
    except Exception:
        continue
    for tid in TARGETS:
        if tid in t:
            found.setdefault(tid, []).append(os.path.basename(f))

L.append('\n== w240 命中 id 落在哪个文件 ==')
for tid in TARGETS:
    L.append('  %-10s %s' % (tid, ', '.join(found.get(tid, ['<无>'])[:4])))

io.open('_autologs/_ls_mined.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
