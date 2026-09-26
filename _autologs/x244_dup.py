# -*- coding: utf-8 -*-
"""① x244 的 18 个 id 有多少与 mined 里旧的 cid 撞（= 平台去重，白跑）
   ② dump 一个 json 的键名，修正表达式提取"""
import io, json, os

ROOT = r'D:\Python\worldquant'
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
L = []

# id -> [cid...]
idmap = {}
keyname = None
sample = None
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    p = os.path.join(MD, fn)
    try:
        d = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        continue
    if sample is None:
        sample = (fn, sorted(d.keys()))
    aid = str(d.get('id') or d.get('alpha_id') or '')
    if aid:
        idmap.setdefault(aid, []).append(fn[:-5])

L.append('json 顶层键样本 (%s): %s' % (sample[0], sample[1]))
L.append('')
L.append('--- x244 批次 id 去重检查 ---')
x244 = [(fn[:-5], str(json.load(io.open(os.path.join(MD, fn), encoding='utf-8')).get('id')))
        for fn in os.listdir(MD) if fn.startswith('x244_') and fn.endswith('.json')
        for _ in [0]]
dup, new = [], []
for cid, aid in sorted(x244):
    others = [c for c in idmap.get(aid, []) if c != cid]
    if others:
        dup.append((cid, aid, others))
    else:
        new.append((cid, aid))
L.append('x244 落盘 %d 条：与旧 cid 撞 id %d 条，全新 id %d 条' % (len(x244), len(dup), len(new)))
L.append('')
L.append('★ 撞 id（= 该 alpha 早已存在，换挡没产出新东西）：')
for cid, aid, others in dup:
    L.append('   %-38s %-10s  ← 已存在于: %s' % (cid, aid, ', '.join(others)))
L.append('')
L.append('全新 id：')
for cid, aid in new:
    L.append('   %-38s %s' % (cid, aid))

# 表达式提取修正：找含 '(' 且较长的字符串字段
L.append('')
L.append('--- 表达式字段名探测（A_MAR 样本）---')
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    if str(d.get('id')) == 'O0N5o3Nv':
        for k, v in d.items():
            if isinstance(v, str) and len(v) > 25:
                L.append('  [%s] %s' % (k, v[:300]))
            elif isinstance(v, dict):
                L.append('  {%s} keys=%s' % (k, list(v.keys())[:12]))
        break

io.open(os.path.join(ROOT, '_autologs', '_x244_dup.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
