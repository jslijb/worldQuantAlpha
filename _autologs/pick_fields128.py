# -*- coding: utf-8 -*-
# 筛选 fnd6 未用、aC 30~150 的字段（batch127 实证：<30 无数据，87 的有数据）
import json, csv, re

# 已用字段 = 历史候选表达式里出现过的
used = set()
import glob, os
for f in glob.glob('data/alpha_quality_analysis/mined/*.json'):
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception: continue
    e = ((d.get('regular') or {}).get('code') or '') + ' ' + str(d.get('expr') or '')
    for m in re.findall(r'[a-z][a-z0-9_]{3,}', e.lower()):
        used.add(m)
# 台账里再扫一遍
try:
    for r in csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')):
        for m in re.findall(r'[a-z][a-z0-9_]{3,}', (r.get('expr') or '').lower()):
            used.add(m)
except Exception: pass

mat = json.load(open('data/alpha_quality_analysis/fnd6_matrix.json', encoding='utf-8'))
cands = []
for v in mat:
    aC = v.get('alphaCount') or 0
    fld = v.get('id')
    if 30 <= aC <= 400 and fld not in used:
        cands.append((aC, fld, (v.get('description') or '')[:40]))
cands.sort()
print(len(cands))
for aC, k, desc in cands:
    print(aC, k, desc)
