# -*- coding: utf-8 -*-
"""① x244 候选 vs 撞车对手 的 regular.code 逐字对比
   ② A_*/n160_* 中性化系列有多少已入池（在台账里）"""
import io, json, os, difflib, re

ROOT = r'D:\Python\worldquant'
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
LED = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'SUBMITTED_LEDGER.csv')
L = []

recs = {}          # cid -> dict
byid = {}          # aid -> cid
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    cid = fn[:-5]
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    code = ((d.get('regular') or {}).get('code') or '')
    recs[cid] = dict(aid=str(d.get('id') or ''), code=code,
                     is_=d.get('is') or {}, st=d.get('settings') or {},
                     oc=((d.get('regular') or {}).get('operatorCount')))
    if recs[cid]['aid']:
        byid.setdefault(recs[cid]['aid'], []).append(cid)

# 台账
sub = {}
for i, ln in enumerate(io.open(LED, encoding='utf-8-sig')):
    p = ln.rstrip('\n').split(',')
    if i and p and p[0].strip():
        sub[p[0].strip()] = p

PAIRS = [('x244_x174w125dAMIINTrind_MAR', 'A_MAR'),
         ('x244_x174w125dAMIINTrsec_MAR', 'n160_N1a18988_SEC'),
         ('x244_x174w125dAMIINTrind_SEC', 'A_SEC__r_ind'),
         ('x244_x174w125dAMIINTrsec_SEC', 'A_IND__r_ind')]

for a, b in PAIRS:
    A, B = recs.get(a), recs.get(b)
    L.append('=' * 104)
    L.append('%s (%s)   vs   %s (%s)' % (a, A['aid'] if A else '?', b, B['aid'] if B else '?'))
    if not A or not B:
        L.append('  缺记录')
        continue
    L.append('  候选 code (%d字符, 算子%d): %s' % (len(A['code']), A['oc'] or 0, A['code']))
    L.append('  对手 code (%d字符, 算子%d): %s' % (len(B['code']), B['oc'] or 0, B['code']))
    r = difflib.SequenceMatcher(None, A['code'], B['code']).ratio()
    L.append('  相似度 %.4f  %s' % (r, '★ 同一条' if r > 0.95 else ('同源' if r > 0.6 else '不同源')))
    L.append('')

# A_/n160_ 系列入池率
fam = [c for c in recs if c.startswith('A_') or c.startswith('n160')]
inled = [c for c in fam if recs[c]['aid'] in sub]
L.append('=' * 104)
L.append('中性化实验系列：mined 里 %d 条，其中已提交入池 %d 条' % (len(fam), len(inled)))
L.append('')
L.append('已入池的（这些就是墙）：')
L.append('%-28s %-10s %-12s %-7s %-7s %-7s' % ('cid', 'aid', 'neu', 'S', 'F', 'TO'))
for c in sorted(inled, key=lambda x: -(recs[x]['is_'].get('fitness') or 0)):
    r = recs[c]
    L.append('%-28s %-10s %-12s %-7s %-7s %-7s' % (
        c[:28], r['aid'], r['st'].get('neutralization'),
        r['is_'].get('sharpe'), r['is_'].get('fitness'), r['is_'].get('turnover')))
L.append('')
L.append('未入池的 %d 条里，过闸(S+F>=4.0 / tS 见 is.checks) 的：' % (len(fam) - len(inled)))
for c in sorted([x for x in fam if x not in inled], key=lambda x: -((recs[x]['is_'].get('sharpe') or 0) + (recs[x]['is_'].get('fitness') or 0))):
    r = recs[c]
    S, F = r['is_'].get('sharpe') or 0, r['is_'].get('fitness') or 0
    if S + F >= 4.0:
        L.append('  %-28s %-10s %-12s S=%-6s F=%-6s TO=%-7s' % (
            c[:28], r['aid'], r['st'].get('neutralization'), S, F, r['is_'].get('turnover')))

io.open(os.path.join(ROOT, '_autologs', '_exp2.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
