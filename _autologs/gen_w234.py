# -*- coding: utf-8 -*-
"""w234 —— n160 骨架定向微调（三条路都在 0.2 以内）

平台实测（0920 判决）：
  n160_qMxMV8NA_SEC  corr=0.7002 撞pwRwWoJ3(3.33) 需3.66 自己S2.55  → 压 corr 0.0002 即直通
  n160_d5b5voEJ_SEC  corr=0.7024 撞9qjqm3Q9(2.92) 需3.21 自己S2.55  → 压 corr 0.0024 即直通
  n160_qMxMV8NA_MAR  corr=0.8274 撞levpXXGl(2.31) 需2.54 自己S2.35  → 提 S 0.19 即过豁免线

微调手段（全部来自已实证的降换手工具）：
  hump 包裹 / ts_decay_linear 包裹 / 权重调整 / decay 调整 / 二次 group_neutralize / 加腿 / 窗口拉长
"""
import json, io

OUT = '_autologs/leg_combos_w234.json'

A = ('1.5*group_rank(fnd6_pstkl/cap, subindustry) + '
     'group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + '
     'group_rank(fnd6_xrent/assets, subindustry) + '
     '0.75*group_rank(-ts_delta(close, 20), subindustry) + '
     '0.75*group_rank(-ts_rank(returns, 20), subindustry) + '
     '0.75*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)')

B = ('1.5*group_rank(fn_accrued_liab_curr_a/assets, subindustry) + '
     'group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry) + '
     'group_rank(fnd6_xrent/assets, subindustry) + '
     '1.5*group_rank(-ts_delta(close, 20), subindustry) + '
     '1.5*group_rank(volume/ts_mean(volume, 60), subindustry) + '
     '1.5*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)')

A_w15 = A.replace('0.75*group_rank', '1.5*group_rank')
A_win30 = (A.replace('-ts_delta(close, 20)', '-ts_delta(close, 30)')
            .replace('-ts_rank(returns, 20)', '-ts_rank(returns, 30)'))
A_plus = A + ' + group_rank(fnd6_newa1v1300_aol2/cap, subindustry)'
B_plus = B + ' + group_rank(fnd6_newa1v1300_aol2/cap, subindustry)'

combos = {}
SEC = {'neutralization': 'SECTOR', 'decay': 10, 'truncation': 0.08}
MAR = {'neutralization': 'MARKET', 'decay': 10, 'truncation': 0.08}

# —— 路线一：压 corr（基座 A，SECTOR，差 0.0002）
combos['A_hump'] = dict(SEC, expr=f'hump({A})', _note='SECTOR hump包裹')
combos['A_decl'] = dict(SEC, expr=f'ts_decay_linear({A}, 5)', _note='SECTOR ts_decay_linear5')
combos['A_w15'] = dict(SEC, expr=A_w15, _note='SECTOR 慢腿权重0.75→1.5')
combos['A_plus'] = dict(SEC, expr=A_plus, _note='SECTOR 加aol2/cap腿')
combos['A_win30'] = dict(SEC, expr=A_win30, _note='SECTOR 慢腿窗口20→30')
combos['A_gn'] = dict(SEC, expr=f'group_neutralize({A}, sector)', _note='SECTOR 二次sector中性化')
combos['A_d5'] = dict(SEC, expr=A, decay=5, truncation=0.08, neutralization='SECTOR', _note='SECTOR decay5')
combos['A_d20'] = dict(SEC, expr=A, decay=20, truncation=0.08, neutralization='SECTOR', _note='SECTOR decay20')

# —— 路线二：提 S（基座 A，MARKET，差 0.19，撞低墙 levpXXGl 2.31）
combos['Am_w15'] = dict(MAR, expr=A_w15, _note='MARKET 慢腿权重1.5 提S')
combos['Am_hump'] = dict(MAR, expr=f'hump({A})', _note='MARKET hump')
combos['Am_plus'] = dict(MAR, expr=A_plus, _note='MARKET 加腿提S')
combos['Am_w2'] = dict(MAR, expr=A.replace('0.75*group_rank(-ts_delta(close, 20)', '2.0*group_rank(-ts_delta(close, 20)')
                       .replace('0.75*group_rank(-ts_rank(returns, 20)', '2.0*group_rank(-ts_rank(returns, 20)')
                       .replace('0.75*group_rank(-ts_mean(abs(returns)/volume, 20)', '1.5*group_rank(-ts_mean(abs(returns)/volume, 20)'),
                       _note='MARKET 慢腿权重2.0 激进提S')

# —— 路线三：压 corr（基座 B，SECTOR，差 0.0024）
combos['B_hump'] = dict(SEC, expr=f'hump({B})', _note='SECTOR hump包裹')
combos['B_decl'] = dict(SEC, expr=f'ts_decay_linear({B}, 5)', _note='SECTOR ts_decay_linear5')
combos['B_plus'] = dict(SEC, expr=B_plus, _note='SECTOR 加aol2/cap腿')
combos['B_d5'] = dict(SEC, expr=B, decay=5, truncation=0.08, neutralization='SECTOR', _note='SECTOR decay5')
combos['B_d20'] = dict(SEC, expr=B, decay=20, truncation=0.08, neutralization='SECTOR', _note='SECTOR decay20')
combos['B_gn'] = dict(SEC, expr=f'group_neutralize({B}, sector)', _note='SECTOR 二次sector中性化')

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('w234 combos:', len(combos))
for k, v in combos.items():
    print(' ', k, v['_note'])
