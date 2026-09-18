# -*- coding: utf-8 -*-
"""检查 w202 条件腿 standalone 结果"""
import os, json, glob
os.chdir(r'D:\Python\worldquant')
out = []
for f in sorted(glob.glob('data/alpha_quality_analysis/mined/C_int_*.json')):
    d = json.load(open(f, encoding='utf-8'))
    isd = d.get('is', {})
    fails = [c.get('name') for c in (isd.get('checks') or []) if isinstance(c, dict) and c.get('result') == 'FAIL']
    out.append('%-11s id=%s S=%s F=%s FAIL=%s' % (
        os.path.basename(f)[:-5], d.get('id'), isd.get('sharpe'), isd.get('fitness'), fails))
open('_autologs/r24.txt', 'w', encoding='utf-8').write('\n'.join(out))
