# -*- coding: utf-8 -*-
"""筛 fnd6_matrix.json 里 aC<100 且未被 w123/124/125 用过的极冷字段"""
import json, glob, re

m = json.load(open('data/alpha_quality_analysis/fnd6_matrix.json', encoding='utf-8'))
found = {}
def walk(o):
    if isinstance(o, dict):
        fid = o.get('id') or o.get('field') or o.get('name')
        if isinstance(fid, str) and fid.startswith('fnd6'):
            ac = o.get('alphaCount', o.get('aC', 10**9))
            if isinstance(ac, (int, float)):
                found[fid] = int(ac)
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(m)
print('matrix 字段总数:', len(found))

# 已用字段（从 w123/124/125 产出表达式里提取）
used = set()
for f in glob.glob('data/alpha_quality_analysis/mined/w12[345]_*.json'):
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception: continue
    expr = (d.get('regular') or {}).get('code') or ''
    for tok in re.findall(r'fnd6_[a-z0-9_]+', expr):
        used.add(tok)
print('已用 fnd6 字段数:', len(used))

cold = [(ac, fid) for fid, ac in found.items() if ac < 100 and fid not in used]
cold.sort()
print('aC<100 且未用过:', len(cold))
for ac, fid in cold[:40]:
    print('%4d  %s' % (ac, fid))
