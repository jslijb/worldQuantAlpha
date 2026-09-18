# -*- coding: utf-8 -*-
"""w201 前置：日内轴新腿单腿模拟（建 PnL 库），key 直接用腿名以便 cid2id 解析"""
import json

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

LEGS = {
    # P_int20 窗口变体
    'P_int10': G('-ts_rank(close/open - 1, 10)'),
    'P_int40': G('-ts_rank(close/open - 1, 40)'),
    'P_int60': G('-ts_rank(close/open - 1, 60)'),
    # P_on5 窗口变体
    'P_on10': G('-ts_mean(open/ts_delay(close,1) - 1, 10)'),
    'P_on20': G('-ts_mean(open/ts_delay(close,1) - 1, 20)'),
    # 换分组变体
    'P_int20I': GI('-ts_rank(close/open - 1, 20)'),
    'P_int20C': GC('-ts_rank(close/open - 1, 20)'),
    'P_int20V': GV('-ts_rank(close/open - 1, 20)'),
    'P_on5I':  GI('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
    # vwap 偏离均值化
    'P_vd5':  G('ts_mean((close - vwap)/vwap, 5)'),
}
COMB = {}
for i, (k, e) in enumerate(sorted(LEGS.items())):
    COMB[k] = {'expr': e, 'S': 0, 'maxcorr': 0, 'nearest': '', 'mains': [k], 'anchors': [], 'engine': False, 'shared_frac': 0}
json.dump(COMB, open('_autologs/search_combos_w201leg.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('legs to sim:', len(COMB))
