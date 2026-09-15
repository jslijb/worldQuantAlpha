# -*- coding: utf-8 -*-
"""项目结构扫描：按顶层目录聚合文件数/体积，输出根目录清单与扩展名分布。只读，不改动任何文件。"""
import os, collections, sys

root = r'D:\Python\worldquant'
SKIP_DIRS = {'__pycache__', '.git', 'node_modules', '.workbuddy'}

agg = collections.defaultdict(lambda: [0, 0])   # 顶层目录 -> [文件数, 字节]
ext = collections.Counter()
root_files = []          # 根目录文件 (name, size, mtime)
root_dirs = []           # 根目录子目录
big = []                 # 全局大文件 top
newest = []              # 全局最近修改 top

for dp, dns, fns in os.walk(root):
    rel = os.path.relpath(dp, root)
    parts = [] if rel == '.' else rel.split(os.sep)
    dns[:] = [d for d in dns if d not in SKIP_DIRS]
    if any(p in SKIP_DIRS for p in parts):
        continue
    key = parts[0] if parts else '(根目录)'
    for f in fns:
        p = os.path.join(dp, f)
        try:
            st = os.stat(p); sz = st.st_size; mt = st.st_mtime
        except Exception:
            sz = 0; mt = 0
        agg[key][0] += 1
        agg[key][1] += sz
        ext[os.path.splitext(f)[1].lower()] += 1
        big.append((sz, os.path.relpath(p, root)))
        newest.append((mt, os.path.relpath(p, root)))
        if not parts:
            root_files.append((f, sz, mt))

for d in sorted(os.listdir(root)):
    dp = os.path.join(root, d)
    if os.path.isdir(dp):
        root_dirs.append(d)

out = []
out.append('=' * 70)
out.append('一、顶层目录聚合（文件数 / 体积）')
out.append('=' * 70)
for k, v in sorted(agg.items(), key=lambda x: -x[1][1]):
    out.append(f'  {k:38} {v[0]:6} 个   {v[1]/1024/1024:9.2f} MB')

out.append('')
out.append('=' * 70)
out.append(f'二、根目录文件清单（{len(root_files)} 个）')
out.append('=' * 70)
for f, sz, mt in sorted(root_files):
    import datetime
    t = datetime.datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M') if mt else '-'
    out.append(f'  {f:56} {sz/1024:8.1f} KB  {t}')

out.append('')
out.append('=' * 70)
out.append(f'三、根目录子目录（{len(root_dirs)} 个）')
out.append('=' * 70)
for d in root_dirs:
    out.append('  ' + d)

out.append('')
out.append('=' * 70)
out.append('四、扩展名分布')
out.append('=' * 70)
for k, v in ext.most_common():
    out.append(f'  {k or "(无扩展名)":20} {v}')

out.append('')
out.append('=' * 70)
out.append('五、体积最大的 30 个文件')
out.append('=' * 70)
for sz, rel in sorted(big, key=lambda x: -x[0])[:30]:
    out.append(f'  {sz/1024/1024:8.2f} MB  {rel}')

out.append('')
out.append('=' * 70)
out.append('六、最近修改的 30 个文件')
out.append('=' * 70)
import datetime
for mt, rel in sorted(newest, key=lambda x: -x[0])[:30]:
    t = datetime.datetime.fromtimestamp(mt).strftime('%Y-%m-%d %H:%M') if mt else '-'
    out.append(f'  {t}  {rel}')

txt = '\n'.join(out)
open(r'D:\Python\worldquant\_autologs\scan_project.txt', 'w', encoding='utf-8').write(txt)
print('done, lines=', len(out))
