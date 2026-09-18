# -*- coding: utf-8 -*-
"""检查 w201 单腿模拟结果：各腿 standalone Sharpe"""
import os, json, glob
os.chdir(r'D:\Python\worldquant')
out = []
for f in sorted(glob.glob('data/alpha_quality_analysis/mined/P_int*.json') +
                glob.glob('data/alpha_quality_analysis/mined/P_on*.json') +
                glob.glob('data/alpha_quality_analysis/mined/P_vd*.json')):
    d = json.load(open(f, encoding='utf-8'))
    isd = d.get('is', {})
    s = isd.get('sharpe')
    ft = isd.get('fitness')
    cid = os.path.basename(f)[:-5]
    if cid in ('P_on5', 'P_vd'):  # 老腿，跳过
        continue
    out.append('%-10s id=%s S=%s F=%s' % (cid, d.get('id'), s, ft))
open('_autologs/r21.txt', 'w', encoding='utf-8').write('\n'.join(out))
