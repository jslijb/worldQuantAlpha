# -*- coding: utf-8 -*-
"""验证 batch125 计划使用的字段在 fnd6_matrix.json 中存在及其 alphaCount"""
import json
m = json.load(open('data/alpha_quality_analysis/fnd6_matrix.json', encoding='utf-8'))
# 兼容结构
if isinstance(m, dict):
    fields = m.get('fields') or m
else:
    fields = m

want = ['fnd6_newqv1300_cicurrq', 'fnd6_dxd5', 'fnd6_aqi',
        'fnd6_newa2v1300_tstk', 'fnd6_newqv1300_loq',
        'fnd6_newqv1300_spceepsp12', 'fnd6_newa2v1300_xoptepsq', 'fnd6_newqv1300_prcepsq',
        'fnd6_newqv1300_spcep12',
        'fnd6_newqv1300_xrent', 'fnd6_xrent']
found = {}
def walk(o):
    if isinstance(o, dict):
        fid = o.get('id') or o.get('field') or o.get('name')
        if isinstance(fid, str) and ('fnd6' in fid or fid in want):
            found[fid] = o.get('alphaCount', o.get('aC', '?'))
        for v in o.values(): walk(v)
    elif isinstance(o, list):
        for v in o: walk(v)
walk(fields)
print('matrix 内字段总数(含嵌套去重前):', len(found))
for w in want:
    print('%-32s -> %s' % (w, 'aC=' + str(found[w]) if w in found else 'NOT FOUND'))
