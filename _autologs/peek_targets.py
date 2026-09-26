# -*- coding: utf-8 -*-
"""peek_targets.py —— 确认候选的 regular 表达式可取（自写 UTF-8）"""
import io, json, os, csv

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined'
L = []

# 从投递日志里挑出的"离墙最近的高质量"目标
want = ['w162_06', 'w162_06__g_ind', 'w162_06__g_sec', 'w164_04',
        '1YwRK1wW_v2__r_bvol', '9qX3M2mq_v2__r_bvol', '9qX3M2mq_v2__r_sec', '9qX3M2mq_v2__IND']
bycid = {}
for x in sorted(os.listdir(MINED)):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MINED, x), encoding='utf-8'))
    except Exception:
        continue
    c = d.get('_cid')
    if c:
        bycid[c] = x

for cid in want:
    f = bycid.get(cid)
    if not f:
        L.append('%-24s : (mined 中无此 _cid)' % cid); continue
    d = json.load(io.open(os.path.join(MINED, f), encoding='utf-8'))
    reg = d.get('regular') or {}
    expr = reg.get('code') if isinstance(reg, dict) else reg
    if not expr:
        expr = d.get('regularCode') or ''
    st = d.get('settings') or {}
    L.append('%-24s file=%s' % (cid, f))
    L.append('    expr: %s' % (str(expr)[:400]))
    L.append('    settings: universe=%s decay=%s neut=%s trunc=%s delay=%s'
             % (st.get('universe'), st.get('decay'), st.get('neutralization'),
                st.get('truncation'), st.get('delay')))
    i = d.get('is') or {}
    L.append('    S=%.2f F=%.2f TO=%.4f tS=%.2f'
             % (i.get('sharpe') or 0, i.get('fitness') or 0, i.get('turnover') or 0,
                (d.get('test') or {}).get('sharpe') or 0))
    L.append('')

io.open(ROOT + '_autologs/_peek_targets.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
