# -*- coding: utf-8 -*-
"""脚本分类统计：按功能族归并根目录与 docs 下的 .py 文件。只读。"""
import os, re, collections

root = r'D:\Python\worldquant'

RULES = [
    ('挖矿批次 mine_batch*.py',        r'^mine_batch\d+[a-z]?\.py$'),
    ('早期挖矿 mine_*.py',             r'^mine_(submit|probe)\.py$|^alpha_hunter\.py$|^world4\.py$'),
    ('提交 submit_*.py',               r'^submit_.*\.py$'),
    ('提交 v系列 submit_v*.py',        r'^submit_v\d+\.py$'),
    ('提交 daily/final/find/fast',     r'^(daily_.*|final_.*|find_and_submit_.*|fast_test)\.py$'),
    ('检查/预检 check/probe/corr/poll', r'^(check_.*|.*probe.*|corr_.*|poll_.*|recheck_.*|precheck_.*|scout_.*|verify.*)\.py$'),
    ('测试/调试 *_test/debug*',        r'^(\w*_test\.py|debug\d*\.py|debug_.*\.py|balance_test\.py|combo_test\.py|hybrid_test\.py|norm_test\.py|scale_test\.py|quick_one\.py|simple_ratios\.py)$'),
    ('工具 fetch/extract/ocr/render/sum', r'^(fetch_.*|extract_.*|ocr_.*|render_.*|summarize_.*|calc_.*|.*_fields\.py|filter_.*|scan_.*|list_.*|query_.*|search_.*|explore_.*|verify_.*)\.py$'),
    ('公共库 utils/AlphaSimulator',    r'^(utils|AlphaSimulator|alpha_quality_analysis)\.py$'),
    ('SDD 文档脚本',                   r'^(spec|design|tasks|pitfalls|methodology)\.md$'),
]

def classify(names):
    hit = {}
    left = []
    for n in names:
        for label, pat in RULES:
            if re.match(pat, n):
                hit.setdefault(label, []).append(n)
                break
        else:
            left.append(n)
    return hit, left

# 根目录
root_py = [f for f in os.listdir(root) if f.endswith('.py')]
h, left = classify(root_py)
out = []
out.append('=' * 66)
out.append(f'根目录 .py 合计 {len(root_py)} 个')
out.append('=' * 66)
for k in sorted(h, key=lambda x: -len(h[x])):
    out.append(f'  {k:34} {len(h[k]):4} 个')
if left:
    out.append(f'  {"【未归类】":34} {len(left):4} 个  -> {sorted(left)}')

for sub in ['docs', 'data/alpha_quality_analysis']:
    p = os.path.join(root, sub)
    pys = []
    for dp, dns, fns in os.walk(p):
        dns[:] = [d for d in dns if d not in ('__pycache__',)]
        pys += [os.path.join(dp, f) for f in fns if f.endswith('.py')]
    rels = [os.path.relpath(x, p) for x in pys]
    hh, ll = classify(rels)
    out.append('')
    out.append('=' * 66)
    out.append(f'{sub}/ 下 .py 合计 {len(rels)} 个')
    out.append('=' * 66)
    for k in sorted(hh, key=lambda x: -len(hh[x])):
        out.append(f'  {k:34} {len(hh[k]):4} 个')
    if ll:
        out.append(f'  【未归类】{len(ll)} 个 -> {sorted(ll)[:25]}')

open(os.path.join(root, '_autologs', 'classify.txt'), 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
