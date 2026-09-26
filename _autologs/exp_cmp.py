# -*- coding: utf-8 -*-
"""比对：x244 换挡候选 vs 池内撞车对手 的表达式是否同源"""
import io, json, os, difflib

ROOT = r'D:\Python\worldquant'
MD = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'mined')
L = []

byid = {}
bycid = {}
for fn in os.listdir(MD):
    if not fn.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    aid = str(d.get('id') or d.get('alpha_id') or '')
    cid = str(d.get('cid') or d.get('name') or fn[:-5])
    if aid:
        byid[aid] = (cid, d)
    bycid[cid] = (aid, d)


def expr(d):
    for k in ('regular', 'expression', 'expr'):
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ''


PAIRS = [
    ('akbWaOZ9', 'x244_x174w125dAMIINTrind_MAR', 'O0N5o3Nv', 'A_MAR'),
    ('wpZJoj8Q', 'x244_x174w125dAMIINTrsec_MAR', 'omL8Mazn', 'n160_N1a18988_SEC'),
    ('KPNw7Onz', 'x244_x174w125dAMIINTrind_SEC', 'O0N55k1Y', 'w229_c'),
    ('npdOa0lE', 'x244_w16202rind_SEC', '6Xr2eQaJ', 'w85_a'),
]

for caid, ccid, oaid, ocid in PAIRS:
    L.append('=' * 100)
    L.append('候选 %s (%s)   vs   对手 %s (%s)' % (caid, ccid, oaid, ocid))
    ce = expr(byid.get(caid, ('', {}))[1]) if caid in byid else ''
    oe = expr(byid.get(oaid, ('', {}))[1]) if oaid in byid else ''
    if not ce and ccid in bycid:
        ce = expr(bycid[ccid][1])
    L.append('-- 候选 expr (%d 字符):' % len(ce))
    L.append('   ' + ce)
    L.append('-- 对手 expr (%d 字符):' % len(oe))
    L.append('   ' + oe)
    if ce and oe:
        r = difflib.SequenceMatcher(None, ce, oe).ratio()
        L.append('-- 字符串相似度: %.4f  %s' % (r, '★ 高度同源' if r > 0.8 else ('同族' if r > 0.5 else '不同源')))
    L.append('')

# A_* 系列全找出来（中性化实验系列）
L.append('=' * 100)
L.append('--- mined 里所有 A_* / n160_* 中性化实验产物 ---')
for fn in sorted(os.listdir(MD)):
    if not fn.endswith('.json'):
        continue
    cid = fn[:-5]
    if not (cid.startswith('A_') or cid.startswith('n160')):
        continue
    try:
        d = json.load(io.open(os.path.join(MD, fn), encoding='utf-8'))
    except Exception:
        continue
    isd = d.get('is') or {}
    st = d.get('settings') or {}
    L.append('%-28s %-10s %-10s S=%-5s F=%-5s TO=%-7s %s'
             % (cid[:28], str(d.get('id')), str(st.get('neutralization')),
                isd.get('sharpe'), isd.get('fitness'), isd.get('turnover'),
                str(expr(d))[:60]))

io.open(os.path.join(ROOT, '_autologs', '_exp_cmp.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
