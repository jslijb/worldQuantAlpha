# -*- coding: utf-8 -*-
"""w226/w227 —— 提夏普专项：权重重平衡
李工 0920：'shape 率提升 10% 相似度超过 80% 也可以提交，你需要提升夏普率'
→ 豁免线 = 1.1 × max(对手 S)。夏普越高，能吃的对手越多。
"""
import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


# ---- 腿库 ----
INV = '-ts_rank(close/open - 1, 10)'            # 日内反转（今日最强单腿，2.5 权 → S3.26）
REV2 = '-ts_delta(close, 2)'                    # 2 日反转
ILLIQ = '-ts_mean(abs(returns)/volume, 20)'     # 非流动性/反转
R5 = '-ts_rank(returns, 5)'                     # 5 日反转
R20 = '-ts_rank(returns, 20)'                   # 20 日反转
XR = 'fnd6_xrent/assets'
GL = 'fnd6_newqv1300_glcea12/assets'
REVT = 'fnd6_mfma2_revt/assets'
INTG = '-annual_intangible_assets_net_carrying_value/assets'
CFOEV = 'ts_av_diff(cashflow_op/enterprise_value,45)'
ACCR = '-(fnd6_newa2v1300_ni - cashflow_op)/assets'
ALC = 'fn_accrued_liab_curr_a/assets'

# ============ w226：日内反转主导几何，抬权重找夏普峰 ============
c = {}
c['w226_a'] = G(INV, 3.0) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_b'] = G(INV, 3.5) + ' + ' + G(XR, 0.5) + ' + ' + G(GL, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_c'] = G(INV, 3.0) + ' + ' + G(REV2, 1.5) + ' + ' + G(GL, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_d'] = G(INV, 2.0) + ' + ' + G(REV2, 1.5) + ' + ' + G(ILLIQ, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_e'] = G(INV, 1.5) + ' + ' + G(REV2, 1.5) + ' + ' + G(ILLIQ, 1.5) + ' + ' + G(R5, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_f'] = G(INV, 2.0) + ' + ' + G(REV2, 1.5) + ' + ' + G(ILLIQ, 1.5) + ' + ' + G(GL, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_g'] = G(INV, 2.5) + ' + ' + G(REV2, 1.5) + ' + ' + G(REVT, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_h'] = G(INV, 2.0) + ' + ' + G(ILLIQ, 2.0) + ' + ' + G(GL, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_i'] = G(INV, 2.5) + ' + ' + G(R20, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_j'] = G(INV, 2.0) + ' + ' + G(REV2, 1.0) + ' + ' + G(ILLIQ, 1.0) + ' + ' + G(R5, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_k'] = G(INV, 3.5) + ' + ' + G(ILLIQ, 1.0) + ' + ' + G(GL, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w226_l'] = G(INV, 4.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
json.dump(c, open('_autologs/leg_combos_w226.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

# ============ w227：最强 7 腿骨架（w182_01 S3.51）权重重平衡 ============
d = {}
cfo = G(CFOEV, 1.5)
price3 = [REV2, ILLIQ, R5]
for tag, wp, wv in [('a', 2.0, 1.0), ('b', 2.5, 1.0), ('c', 3.0, 0.5), ('d', 1.5, 1.0)]:
    d[f'w227_{tag}'] = cfo + ' + ' + G(XR, wv) + ' + ' + G(GL, wv) + ' + ' + G(REVT, wv) + ' + ' + ' + '.join(G(l, wp) for l in price3)
# 换第 4 腿 / 换价格腿组合
d['w227_e'] = cfo + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.0) + ' + ' + G(ILLIQ, 2.0) + ' + ' + G(R20, 2.0)
d['w227_f'] = cfo + ' + ' + G(XR, 1.0) + ' + ' + G(INTG, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
d['w227_g'] = cfo + ' + ' + G(XR, 1.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.0) + ' + ' + G(R5, 2.0)
d['w227_h'] = cfo + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(ALC, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
d['w227_i'] = G(CFOEV, 2.0) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
d['w227_j'] = cfo + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(INV, 2.0) + ' + ' + G(REV2, 2.0) + ' + ' + G(ILLIQ, 2.0)
json.dump(d, open('_autologs/leg_combos_w227.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)

print('w226', len(c), 'w227', len(d))
