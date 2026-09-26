# -*- coding: utf-8 -*-
"""w235 —— j2Az8n0E 骨架降 corr 改造（平台判决 corr 0.7367，需 <0.70，差 0.037）

平台判决书实证（_autologs/_verdict_j2Az8n0E.txt）：
  SELF_CORRELATION FAIL value=0.7367 limit=0.7
  对手 MPaPe0oo 0.7367 / omL8Mazn 0.7365 / LLNXEe7L 0.7317 / kqVp6wnO 0.7184
  本地算 0.7314 → 平台 0.7367（偏移 +0.005）
  这条本身 S=2.60 F=2.44 tS=2.41 TO=11.27% margin=19.6bp —— 质量很好，只差 corr。

降 corr 手段（n160 实证最有效）：换中性化（同骨架 SUBINDUSTRY→SECTOR：corr 0.8274→0.7002，−0.127）
"""
import json, io

OUT = '_autologs/leg_combos_w235.json'

GV = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'   # 原分组：波动率分桶
GC = 'bucket(rank(cap), range="0.1, 1, 0.1")'                       # 备选：市值分桶（文档全过率 66.7%）


def full(g):
    return ('group_rank(fnd6_newa2v1300_tstk/assets, %s) + '
            'group_rank(fnd6_newqv1300_loq/assets, %s) + '
            'group_rank(fnd6_newqv1300_cicurrq/assets, %s) + '
            '0.5*group_rank(ts_av_diff(cash/assets, 45), %s) + '
            '0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), %s) + '
            '0.5*group_rank(-ts_delta(close, 2), %s) + '
            '0.5*group_rank(volume/ts_mean(volume, 60), %s) + '
            '0.5*group_rank(-ts_mean(abs(returns)/volume, 20), subindustry) + '
            '0.5*group_rank(-ts_rank(close/open - 1, 20), subindustry)') % ((g,) * 7)


def lean(g):
    """精简版：去掉 3 条 0.5 腿，把慢速腿提权（算子数 63→46，留出调参空间）"""
    return ('group_rank(fnd6_newa2v1300_tstk/assets, %s) + '
            'group_rank(fnd6_newqv1300_loq/assets, %s) + '
            'group_rank(fnd6_newqv1300_cicurrq/assets, %s) + '
            '0.75*group_rank(ts_av_diff(cash/assets, 45), %s) + '
            '0.75*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), %s) + '
            'group_rank(-ts_mean(abs(returns)/volume, 20), %s)') % ((g,) * 6)


combos = {}
for tag, nz in (('SEC', 'SECTOR'), ('MAR', 'MARKET'), ('IND', 'INDUSTRY'), ('NON', 'NONE')):
    combos['A_' + tag] = {'expr': full(GV), 'neutralization': nz, 'decay': 10, 'truncation': 0.08,
                          '_note': '原骨架换中性化 ' + nz}
    combos['L_' + tag] = {'expr': lean(GV), 'neutralization': nz, 'decay': 10, 'truncation': 0.08,
                          '_note': '精简版换中性化 ' + nz}
# 市值分桶（换分组维度）
combos['Acap_SEC'] = {'expr': full(GC), 'neutralization': 'SECTOR', 'decay': 10, 'truncation': 0.08,
                      '_note': '市值分桶+SECTOR'}
combos['Acap_SUB'] = {'expr': full(GC), 'neutralization': 'SUBINDUSTRY', 'decay': 10, 'truncation': 0.08,
                      '_note': '市值分桶+SUBIND'}
combos['Lcap_SEC'] = {'expr': lean(GC), 'neutralization': 'SECTOR', 'decay': 10, 'truncation': 0.08,
                      '_note': '精简+市值分桶+SECTOR'}
# decay 微调（平滑度改 PNL 时点）
combos['A_SEC_d6'] = {'expr': full(GV), 'neutralization': 'SECTOR', 'decay': 6, 'truncation': 0.08,
                      '_note': 'SECTOR decay6'}
combos['A_SUB_d15'] = {'expr': full(GV), 'neutralization': 'SUBINDUSTRY', 'decay': 15, 'truncation': 0.08,
                       '_note': 'SUBIND decay15'}

json.dump(combos, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('w235 combos:', len(combos))
