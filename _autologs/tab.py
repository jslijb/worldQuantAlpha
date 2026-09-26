# -*- coding: utf-8 -*-
"""tab.py —— 按文件名正则汇总 mined/ 里的模拟结果（S/F/TO/tS/FAIL + 设置摘要）
用法：python _autologs/tab.py "u1000_|x250_"   [--sort F]
"""
import os, io, sys, json, re
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant'); os.chdir(ROOT)
pat = sys.argv[1] if len(sys.argv) > 1 else '.'
sortk = 'file'
if '--sort' in sys.argv: sortk = sys.argv[sys.argv.index('--sort')+1]
MD = ROOT/'data/alpha_quality_analysis/mined'
rows = []
for f in sorted(MD.glob('*.json')):
    if not re.search(pat, f.name): continue
    try: d = json.load(io.open(f, encoding='utf-8'))
    except Exception: continue
    if not isinstance(d, dict) or 'is' not in d: continue
    st = d.get('settings') or {}; b = d.get('is') or {}; te = d.get('test') or {}
    fa = ','.join(c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL')
    rows.append(dict(file=f.stem, aid=d.get('id',''), S=b.get('sharpe') or 0, F=b.get('fitness') or 0,
                     TO=b.get('turnover') or 0, tS=te.get('sharpe') or 0, FAIL=fa,
                     u=st.get('universe'), neu=st.get('neutralization'), dec=st.get('decay'),
                     tr=st.get('truncation'), dly=st.get('delay'), nan=st.get('nanHandling')))
if sortk == 'F': rows.sort(key=lambda r: -r['F'])
print('%-34s %-10s %6s %6s %7s %6s %-28s %s' % ('file','alpha','S','F','TO','tS','FAIL','set(u/neu/dec/tr/dly/nan)'))
for r in rows:
    print('%-34s %-10s %6.2f %6.2f %7.4f %6.2f %-28s %s/%s/%s/%s/%s/%s' % (
        r['file'], r['aid'], r['S'], r['F'], r['TO'], r['tS'], r['FAIL'],
        r['u'], r['neu'], r['dec'], r['tr'], r['dly'], r['nan']))
print('共 %d 条' % len(rows))
