# -*- coding: utf-8 -*-
"""w233 —— 低换手新骨架（排名导向：TO≤20% + F≥2.5 + S≥2.8）

设计依据（平台实测 + 文档甜点表）：
  1. 低换手族(TO<20%)的 margin 15~28bp，是高换手族(TO>40%)的 3 倍 → 排名与赚钱都在这边
  2. 财报字段一年只更新几次，天然低换手，且 alphaCount 122~400 属冷门（不拥挤）
  3. 慢速腿池来自平台高 F 样本共有腿：-ts_mean(abs(returns)/volume,20)、volume/ts_mean(volume,120)
  4. decay=10 / trunc=0.08 / nanHandling=ON / SUBINDUSTRY = 高F族的标准设置
"""
import json, io

OUT = '_autologs/leg_combos_w233.json'

# 冷门 fnd6 字段（来源 COLD_FIELD_WHITELIST.csv，剔除已占用的 xrent/xopr/debt_st/glcea12/txtub 系列）
FIELDS = [
    ('fnd6_newa1v1300_aol2', 1.19),
    ('fnd6_newqv1300_aol2q', 1.17),
    ('fnd6_newqv1300_dpactq', 0.96),
    ('fnd6_newa1v1300_ano', 0.92),
    ('fnd6_newa1v1300_dpact', 0.86),
    ('fnd6_txs', 0.84),
    ('fnd6_pstkl', 0.82),
    ('fnd6_mfmq_mibtq', 0.79),
    ('fnd6_lol2', 0.77),
    ('fnd6_newqv1300_invwipq', 0.72),
]

# 共享的慢速腿（低换手来源）
ENG1 = 'group_rank(ts_av_diff(cash/assets, 45), subindustry)'
ENG2 = 'group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), subindustry)'
SLOW1 = 'group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)'
SLOW2 = 'group_rank(volume/ts_mean(volume, 120), subindustry)'
SLOW3 = 'group_rank(-ts_delta(close, 20), subindustry)'

combos = {}
for f, s0 in FIELDS:
    main = f'1.5*group_rank({f}/assets, subindustry)'
    # 骨架 A：6 腿，主腿全权 + 双引擎 + 3 慢速腿
    combos[f'A_{f}'] = {
        'expr': ' + '.join([main, ENG1, ENG2, SLOW1, SLOW2, SLOW3]),
        'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08,
        '_note': f'新锚{s0} 6腿慢速版'}
    # 骨架 B：4 腿精瘦版（少引擎腿，牺牲部分质量换低相关）
    combos[f'B_{f}'] = {
        'expr': ' + '.join([main, ENG1, SLOW1, SLOW2]),
        'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08,
        '_note': f'新锚{s0} 4腿精瘦版'}
    # 骨架 C：8 腿，加高F财务锚（拥挤但对F有利）
    combos[f'C_{f}'] = {
        'expr': ' + '.join([main,
                            'group_rank(fn_accrued_liab_curr_a/assets, subindustry)',
                            'group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry)',
                            ENG1, ENG2, SLOW1, SLOW2]),
        'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08,
        '_note': f'新锚{s0} 7腿含高F锚'}

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('w233 combos:', len(combos))
