# -*- coding: utf-8 -*-
"""dump_set.py —— 打印指定 id 的 settings + 指标（优先读 mined/，再从 API 快照）"""
import os, io, sys, json
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant'); os.chdir(ROOT)
IDS = [x for x in sys.argv[1:] if x]
MD = ROOT/'data/alpha_quality_analysis/mined'
found = {}
for f in MD.glob('*.json'):
    try: d = json.load(io.open(f, encoding='utf-8'))
    except Exception: continue
    i = d.get('id')
    if i in IDS: found.setdefault(i, d)
D = json.load(io.open(ROOT/'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(D, dict): D = D.get('results', [])
for a in D:
    if a.get('id') in IDS: found.setdefault(a['id'], a)
for i in IDS:
    a = found.get(i)
    if not a: print(i, '未找到'); continue
    st = a.get('settings') or {}; b = a.get('is') or {}; te = a.get('test') or {}
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    code = (a.get('regular') or {}).get('code') or ''
    print('%-10s %s' % (i, json.dumps({k: st.get(k) for k in ['universe','neutralization','decay','truncation','delay','nanHandling','pasteurization','unitHandling','maxTrade','maxPosition']}, ensure_ascii=False)))
    print('   S=%.2f F=%.2f TO=%.4f tS=%.2f FAIL=%s len=%d' % (b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0, te.get('sharpe') or 0, fa, len(code)))
