# -*- coding: utf-8 -*-
"""w231 —— 抬夏普清 N1avK6zw(2.42) 那条线

硬数据（0920 w225 判决）：
  levR2PqN(w225_b) S=2.57 corr=0.7675 vs N1avK6zw(S=2.42) → 需≥2.66，差 0.09
  blbWPG8K(w225_d) S=2.25 corr=0.7548 vs N1avK6zw(S=2.42) → 需≥2.66
  LLNlX5nv(w225_j) S=2.51 corr=0.7365 vs 58Q7kl1z(S=2.14) → 需≥2.35 【已放行入池】
骨架 = 1.5*INV + 1.5*ACCR + 0.5*XR + 0.4*CFOEV（SUBINDUSTRY）
夏普驱动器 = INV(-ts_rank(close/open-1,10))，w228 已验证加到 2.5~3.0 权仍稳。
目标：同骨架把 S 从 2.57 抬到 2.7+，清掉 2.66 的线。
"""
import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'
ILLIQ = '-ts_mean(abs(returns)/volume, 20)'
ACCR = '-(fnd6_newa2v1300_ni - cashflow_op)/assets'
ALC = 'fn_accrued_liab_curr_a/assets'
CORRV = '-ts_corr(close, volume, 20)'
PRC20 = '-ts_av_diff(close, 20)'
EBITEV = 'ts_av_diff(ebit/enterprise_value, 30)'
XR = 'fnd6_xrent/assets'
CFOEV = 'ts_av_diff(cashflow_op/enterprise_value,45)'
GL = 'fnd6_newqv1300_glcea12/assets'
REVT = 'fnd6_mfma2_revt/assets'

c = {}
# --- A 组：直接抬 INV 权（w225_b 加码）---
c['w231_a'] = G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_b'] = G(INV, 2.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_c'] = G(INV, 3.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_d'] = G(INV, 2.0) + ' + ' + G(ACCR, 2.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
# --- B 组：加第二条价格腿 ---
c['w231_e'] = G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(ILLIQ, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_f'] = G(INV, 2.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(ILLIQ, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_g'] = G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(CORRV, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_h'] = G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(PRC20, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
# --- C 组：w225_j（ebit/EV）加码 ---
c['w231_i'] = G(INV, 2.0) + ' + ' + G(EBITEV, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_j'] = G(INV, 2.5) + ' + ' + G(EBITEV, 1.5) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
c['w231_k'] = G(INV, 2.0) + ' + ' + G(EBITEV, 1.5) + ' + ' + G(ILLIQ, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(CFOEV, 0.4)
# --- D 组：institutional 锚（避开 cfoev）---
c['w231_l'] = G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(XR, 0.5)
c['w231_m'] = G(INV, 2.0) + ' + ' + G(ALC, 1.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(XR, 0.5)

json.dump(c, open('_autologs/leg_combos_w231.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('w231', len(c))
