# -*- coding: utf-8 -*-
"""w204 前置：换几何锚 + 新主腿单腿模拟（建 PnL 库），key 直接用腿名以便 cid2id 解析"""
import json

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

LEGS = {
    # 独有锚的换几何版（与 zq8Xeo2R / 3qXd5vg0 的 subindustry 锚去相关）
    'A_xr_I':   GI('fnd6_xrent/assets'),
    'A_xr_C':   GC('fnd6_xrent/assets'),
    'A_xr_V':   GV('fnd6_xrent/assets'),
    'A_intc_I': GI('fnd6_intc/assets'),
    'A_intc_C': GC('fnd6_intc/assets'),
    'A_debt_I': GI('debt_st/assets'),
    'A_acc_I':  GI('fn_accrued_liab_curr_a/assets'),
    'A_int_I':  GI('-annual_intangible_assets_net_carrying_value/assets'),
    'A_lnoq_I': GI('fnd6_newqv1300_lnoq/assets'),
    'A_g12_I':  GI('fnd6_newqv1300_glcea12/assets'),
    # 主腿补充：更短窗口 + vwap 偏离 + 换几何日内
    'P_int5':   G('-ts_rank(close/open - 1, 5)'),
    'P_int15':  G('-ts_rank(close/open - 1, 15)'),
    'P_int30':  G('-ts_rank(close/open - 1, 30)'),
    'P_int10I': GI('-ts_rank(close/open - 1, 10)'),
    'P_int10C': GC('-ts_rank(close/open - 1, 10)'),
    'P_int10V': GV('-ts_rank(close/open - 1, 10)'),
}
COMB = {}
for i, (k, e) in enumerate(sorted(LEGS.items())):
    COMB[k] = {'expr': e, 'S': 0, 'maxcorr': 0, 'nearest': '', 'mains': [k], 'anchors': [], 'engine': False, 'shared_frac': 0}
json.dump(COMB, open('_autologs/search_combos_w204leg.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('legs to sim:', len(COMB))
