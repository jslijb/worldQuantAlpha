# -*- coding: utf-8 -*-
"""生成逐项清单：A类待删 + B类待归档。只读扫描，输出文本供人工核对。"""
import os, re

root = r'D:\Python\worldquant'
out = []

# ---------- A 类：逐项 ----------
out.append('=' * 72)
out.append('A 类：建议直接删除（逐项）')
out.append('=' * 72)

def walk_add(rel, label, f_filter=None):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        out.append(f'  [不存在] {rel}')
        return
    cnt = 0
    for dp, dns, fns in os.walk(p):
        for f in fns:
            if f_filter and not f_filter(f):
                continue
            full = os.path.join(dp, f)
            sz = os.path.getsize(full)
            out.append(f'  {sz/1024:9.1f} KB  {os.path.relpath(full, root)}')
            cnt += 1
    out.append(f'  -- {label}：{cnt} 个文件')

walk_add('__pycache__', 'Python 字节码缓存')
walk_add('.pytest_cache', 'pytest 缓存')
walk_add('.codegraph', '代码图谱索引（daemon 已死）')
out.append('')
out.append(f'  {os.path.getsize(os.path.join(root,"alpha_list_pending_simulated.csv"))/1024:9.1f} KB  alpha_list_pending_simulated.csv')
out.append(f'  {os.path.getsize(os.path.join(root,"data/alpha_quality_analysis","batch25.log"))/1024:9.1f} KB  alpha_quality_analysis/batch25.log')
for f in ['.corr_block_cache_0912.txt', '.corr_block_cache_0913.txt']:
    p = os.path.join(root, 'data/alpha_quality_analysis', f)
    if os.path.exists(p):
        out.append(f'  {os.path.getsize(p)/1024:9.1f} KB  alpha_quality_analysis/{f}')
walk_add('docs/pdf_pages', 'PDF 分页图')
walk_add('docs/pdf_text', 'PDF 文本提取')
walk_add('docs/ocr_output', 'OCR 输出')
import glob
figs = sorted(glob.glob(os.path.join(root, 'data/alpha_quality_analysis', 'fig_*.png')))
out.append('')
for f in figs:
    out.append(f'  {os.path.getsize(f)/1024:9.1f} KB  alpha_quality_analysis/{os.path.basename(f)}')
q = os.path.join(root, 'data/alpha_quality_analysis', 'QUALITY_REPORT.html')
if os.path.exists(q):
    out.append(f'  {os.path.getsize(q)/1024:9.1f} KB  alpha_quality_analysis/QUALITY_REPORT.html  (md 版保留)')

# ---------- B 类：待归档 ----------
out.append('')
out.append('=' * 72)
out.append('B 类：建议归档到 archive/（不删）')
out.append('=' * 72)

RULES = [
    ('archive/mining/',  r'^mine_batch\d+[a-z]?\.py$'),
    ('archive/submit/',  r'^(submit_(?!v2\.py).*\.py|daily_.*\.py|final_.*\.py|find_and_submit_.*\.py)$'),
    ('archive/hunt/',    r'^(alpha_hunter|world4|mine_submit|mine_probe|analyze_real|build_report)\.py$'),
    ('archive/tests/',   r'^(\w*_test\.py|debug\d*\.py|debug_.*\.py|quick_one\.py|simple_ratios\.py|test_utils\.py)$'),
    ('archive/checks/',  r'^(check_.*|corr_.*|poll_.*|recheck_.*|precheck_.*|scout_.*|.*probe.*|verify.*)\.py$'),
    ('archive/tools/',   r'^(fetch_.*|extract_.*|ocr_.*|render_.*|summarize_.*|calc_.*|.*_fields\.py|filter_.*|scan_.*|list_.*|query_.*|search_.*|explore_.*|alpha_quality_analysis)\.py$'),
]
KEEP = {'submit_v2.py', 'probe_corr_service.py', 'mine_batch120.py', 'mine_batch121.py',
        'auto_submit_loop.py', 'utils.py', 'AlphaSimulator.py'}

def bucket_files(files, base):
    groups = {k: [] for k, _ in RULES}
    groups['archive/misc/'] = []
    for f in files:
        if f in KEEP:
            continue
        for label, pat in RULES:
            if re.match(pat, f):
                groups[label].append(f)
                break
        else:
            groups['archive/misc/'].append(f)
    return groups

def emit(title, files, base):
    out.append('')
    out.append(f'--- {title}（{len(files)} 个 .py）---')
    for label, lst in bucket_files(files, base).items():
        if lst:
            out.append(f'  【{label}】{len(lst)} 个')
            for f in sorted(lst)[:400]:
                out.append(f'      {f}')

root_py = [f for f in os.listdir(root) if f.endswith('.py')]
emit('根目录', root_py, root)

docs_py = []
for dp, dns, fns in os.walk(os.path.join(root, 'docs')):
    dns[:] = [d for d in dns if d != '__pycache__']
    docs_py += [os.path.relpath(os.path.join(dp, f), os.path.join(root, 'docs'))
                for f in fns if f.endswith('.py')]
out.append('')
out.append(f'--- docs/（{len(docs_py)} 个 .py，全部归档）---')
import collections
fam = collections.Counter()
for f in docs_py:
    b = os.path.basename(f)
    if b.startswith('hunt'):
        fam['archive/hunt/'] += 1
    elif b.startswith('submit_'):
        fam['archive/submit/'] += 1
    elif b.startswith(('check_', 'verify', 'query_', 'list_')):
        fam['archive/checks/'] += 1
    elif b.startswith(('explore_', 'search_', 'filter_', 'scan_', 'probe_')):
        fam['archive/tools/'] += 1
    else:
        fam['archive/misc/'] += 1
for k, v in fam.items():
    out.append(f'  【{k}】{v} 个')

# docs 文本类
out.append('')
out.append('--- docs/ 文本与日志 ---')
logs = []
for dp, dns, fns in os.walk(os.path.join(root, 'docs')):
    for f in fns:
        if f.endswith(('.txt',)):
            logs.append(os.path.relpath(os.path.join(dp, f), root))
out.append(f'  .txt 共 {len(logs)} 个 -> archive/logs/')
for f in sorted(logs)[:15]:
    out.append(f'      {f}')
if len(logs) > 15:
    out.append(f'      ...（其余 {len(logs)-15} 个同类）')

open(os.path.join(root, '_autologs', 'delete_archive_list.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('lines:', len(out))
