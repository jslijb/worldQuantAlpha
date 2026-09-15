# -*- coding: utf-8 -*-
"""把 src/ 下脚本里的 alpha_quality_analysis 路径统一改为 data/data/alpha_quality_analysis"""
import re
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
pat = re.compile(r"(?<!data/)(?<!data\\)(['\"/\\])alpha_quality_analysis(?=['\"/\\.])")
n = 0
for p in sorted((ROOT / 'src').rglob('*.py')):
    t = p.read_text(encoding='utf-8')
    t2 = pat.sub(lambda m: m.group(1) + 'data/data/alpha_quality_analysis', t)
    if t2 != t:
        p.write_text(t2, encoding='utf-8')
        n += 1
        print('  updated', p.relative_to(ROOT))
print('改动文件数:', n)
# 复查
print()
print('=== 复查 src 下的路径引用 ===')
for p in sorted((ROOT / 'src').rglob('*.py')):
    for i, line in enumerate(p.read_text(encoding='utf-8').split('\n'), 1):
        if 'data/alpha_quality_analysis' in line and 'data/data/alpha_quality_analysis' not in line and 'data\\alpha_quality_analysis' not in line:
            print(f'  {p.relative_to(ROOT)}:{i}: {line.strip()[:110]}')
