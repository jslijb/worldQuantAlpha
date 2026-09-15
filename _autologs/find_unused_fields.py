# -*- coding: utf-8 -*-
"""筛出：fnd6 MATRIX 字段中 alphaCount 低、且未被已提交池使用的候选锚"""
import json, os, glob, csv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 1. fnd6 MATRIX 字段清单
p = 'data/alpha_quality_analysis/fnd6_matrix.json'
data = json.load(open(p, encoding='utf-8'))
if isinstance(data, dict):
    rows = data.get('results') or list(data.values())
else:
    rows = data
print('fnd6_matrix 类型:', type(data), '条目:', len(rows))
sample = rows[0] if rows else {}
print('样本字段:', {k: sample.get(k) for k in list(sample.keys())[:12]})

# 2. 已提交池 + 候选池已用过的字段
used = set()
for f in glob.glob('data/alpha_quality_analysis/mined/*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    e = (d.get('regular') or {}).get('code') or ''
    for tok in e.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('+', ' ').replace('*', ' ').split():
        tok = tok.strip()
        if tok.startswith('fnd6_'):
            used.add(tok.split('/')[0])

# 3. 已提交台账里的字段（从增强视图）
if os.path.exists('data/alpha_quality_analysis/ledger_with_expr.csv'):
    for r in csv.DictReader(open('data/alpha_quality_analysis/ledger_with_expr.csv', encoding='utf-8-sig')):
        e = r.get('expr') or ''
        for tok in e.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('+', ' ').split():
            tok = tok.strip()
            if tok.startswith('fnd6_'):
                used.add(tok.split('/')[0])

out = []
out.append(f'候选池+已提交池已用过的 fnd6 字段: {len(used)} 个')
out.append('')

# 4. 找低 alphaCount 且未用过的
cand = []
for r in rows:
    fid = (r.get('id') or '').strip()
    if not fid:
        continue
    base = fid.split('/')[0]
    ac = r.get('alphaCount')
    cov = r.get('coverage')
    uc = r.get('userCount')
    cand.append((fid, base, ac, cov, uc, base in used))

unused = [c for c in cand if not c[5]]
unused.sort(key=lambda x: (x[2] if isinstance(x[2], int) else 99999))

out.append(f'fnd6 MATRIX 总字段: {len(cand)} | 未用过的: {len(unused)}')
out.append('')
out.append('=== 未用过 & alphaCount 最低的 45 个（优先做新锚）===')
out.append(f"{'字段':52} {'alphaCount':>10} {'cov':>7} {'users':>6}")
for fid, base, ac, cov, uc, _ in unused[:45]:
    out.append(f'{fid:52} {str(ac):>10} {str(cov)[:6]:>7} {str(uc):>6}')

out.append('')
out.append('=== 参考：已用过的字段（含频率）===')
import collections
uf = collections.Counter()
for f in glob.glob('data/alpha_quality_analysis/mined/*.json'):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    e = (d.get('regular') or {}).get('code') or ''
    for tok in set(e.replace('(', ' ').replace(')', ' ').replace(',', ' ').replace('+', ' ').replace('*', ' ').split()):
        tok = tok.strip()
        if tok.startswith('fnd6_'):
            uf[tok.split('/')[0]] += 1
for k, v in uf.most_common(30):
    out.append(f'  {k:50} {v:4} 条')

open('_autologs/fnd6_unused.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out[:70]))
