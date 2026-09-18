# -*- coding: utf-8 -*-
"""w202 前置：条件门控日内腿单腿模拟（球队硬币帖招②：条件符号切换）"""
import json

G = lambda x: f'group_rank({x}, subindustry)'
CORE = '-ts_rank(close/open - 1, 20)'
VOLREG = 'ts_std_dev(returns, 60) > ts_mean(ts_std_dev(returns, 60), 120)'

LEGS = {
    # 波动率高状态才做日内反转，低状态空手
    'C_int_vg': G(f'if_else({VOLREG}, {CORE}, 0)'),
    # 跳空方向条件：低开才做日内反转
    'C_int_gap': G(f'if_else(open < ts_delay(close, 1), {CORE}, 0)'),
    # 反向对照：日内动量（正号）
    'C_int_mom': G('+ts_rank(close/open - 1, 20)'),
    # 波动率状态切换双向：高波做反转、低波做动量
    'C_int_2s': G(f'if_else({VOLREG}, {CORE}, ts_rank(close/open - 1, 20))'),
}
COMB = {}
for k, e in sorted(LEGS.items()):
    COMB[k] = {'expr': e, 'S': 0, 'maxcorr': 0, 'nearest': '', 'mains': [k],
               'anchors': [], 'engine': False, 'shared_frac': 0}
json.dump(COMB, open('_autologs/search_combos_w202leg.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('legs to sim:', len(COMB))
