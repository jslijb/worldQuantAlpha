# -*- coding: utf-8 -*-
"""gen_w239.py —— 甜点区定向提 S 批（豁免线缺口 ≤0.30 的候选 × decay 阶梯）

依据（0920 新线索）：全库有一批候选"只撞弱靶"——收录到的最高 S 对手只有 2.31~2.59，
      豁免线只有 2.54~2.85，而候选自己 S 就差 0.07~0.30。这类不需要压 corr，
      **只要把 S 顶上去 0.1~0.3 就过**。decay 阶梯（d10→d4→d1 S 递增）是已验证杠杆。
"""
import json, io, os

MINED = 'data/alpha_quality_analysis/mined'
OUT = '_autologs/leg_combos_w239.json'

# (cid, 当前 decay, 缺口)
TARGETS = [
    ('x162_w164_00_MAR', 10, 0.07),
    ('x162_w164_04_MAR', 10, 0.09),
    ('w189_01__g_bdv',   10, 0.10),
    ('w39_i',            40, 0.22),
    ('w41_b',            50, 0.27),
    ('w41_c',            40, 0.25),
]
DECAYS = [1, 2, 4, 6, 20]

combos = {}
for cid, cur, gap in TARGETS:
    p = f'{MINED}/{cid}.json'
    if not os.path.exists(p):
        continue
    d = json.load(io.open(p, encoding='utf-8'))
    s = d.get('settings') or {}
    code = ((d.get('regular') or {}).get('code') or '').strip()
    if not code:
        continue
    for dc in DECAYS:
        if dc == cur:
            continue
        ncid = f'{cid}__d{dc}'
        if os.path.exists(f'{MINED}/{ncid}.json'):
            continue
        combos[ncid] = {'expr': code,
                        'neutralization': s.get('neutralization') or 'SUBINDUSTRY',
                        'decay': dc,
                        'truncation': s.get('truncation') or 0.08,
                        '_note': '提S decay%d->%d（缺口%.2f）' % (cur, dc, gap)}

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
io.open('_autologs/_gen_w239.txt', 'w', encoding='utf-8').write(
    '目标 %d 条 × decay%s → 组合 %d 条\n' % (len(TARGETS), DECAYS, len(combos)))
print('combos', len(combos))
