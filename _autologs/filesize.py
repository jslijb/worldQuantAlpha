# -*- coding: utf-8 -*-
import os, io, json, glob
os.chdir(r'D:\Python\worldquant')
L = []
for f in ['..workbuddy/memory/MEMORY.md'.replace('..', '.'), '.workbuddy/memory/MEMORY.md',
          '.workbuddy/memory/2026-09-20.md', '.workbuddy/memory/2026-09-21.md']:
    f = f if f.startswith('.') else f.replace('.workbuddy/memory/MEMORY.md', '.workbuddy/memory/MEMORY.md')
for f in ['.workbuddy/memory/MEMORY.md', '.workbuddy/memory/2026-09-20.md', '.workbuddy/memory/2026-09-21.md']:
    if os.path.exists(f):
        b = os.path.getsize(f)
        n = sum(1 for _ in io.open(f, encoding='utf-8'))
        L.append('%-40s %8d bytes  %5d lines' % (f, b, n))
    else:
        L.append('%-40s MISSING' % f)

# 平台拉取产物
for f in glob.glob('data/alpha_quality_analysis/raw_from_api/*.json'):
    L.append('%-40s %8d bytes' % (f, os.path.getsize(f)))
L.append('')
L.append('--- _pull_summary.txt ---')
if os.path.exists('_autologs/_pull_summary.txt'):
    L.append(io.open('_autologs/_pull_summary.txt', encoding='utf-8').read()[-1500:])

io.open('_autologs/_filesize.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
