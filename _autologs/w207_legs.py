# -*- coding: utf-8 -*-
"""w207 前置：评级值轴探针——裁决「vec_avg 评级轴 SF<=0.88」与「评级偏离度轴可用」的矛盾"""
import json

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'

LEGS = {
    # 裸评级值（验证旧判死）
    'R_raw_b':   G('vec_avg(anl4_basicdetailrec_ratingvalue)'),
    'R_raw_e':   G('vec_avg(anl4_eaz2lrec_ratingvalue)'),
    # 评级值历史偏离（Research16 偏离度思路）
    'R_dev_b20':  G('ts_av_diff(vec_avg(anl4_basicdetailrec_ratingvalue), 20)'),
    'R_dev_e20':  G('ts_av_diff(vec_avg(anl4_eaz2lrec_ratingvalue), 20)'),
    'R_dev_e60':  GI('ts_av_diff(vec_avg(anl4_eaz2lrec_ratingvalue), 60)'),
    # 评级变化率
    'R_chg_e':    GC('ts_delta(vec_avg(anl4_eaz2lrec_ratingvalue), 20)'),
}
COMB = {}
for i, (k, e) in enumerate(sorted(LEGS.items())):
    COMB[k] = {'expr': e, 'S': 0, 'maxcorr': 0, 'nearest': '', 'mains': [k], 'anchors': [], 'engine': False, 'shared_frac': 0}
json.dump(COMB, open('_autologs/search_combos_w207leg.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('legs to sim:', len(COMB))
