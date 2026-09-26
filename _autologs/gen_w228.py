# -*- coding: utf-8 -*-
"""w228 —— 定向改造 1YXQJRoX(w182_01) 骨架

硬数据（0920 exempt 实跑）：
  1YXQJRoX  S=3.51 F=3.18 tS=3.13  corr=0.7169 vs 0mR2K6lr(S=3.45) → 需≥3.80
  同族 7 腿（w158/w188/w191/w193/w196）corr 0.83~0.99 vs pwRwWoJ3(S=3.33) → 需≥3.66，全死
两条破法：① corr 压到 0.70 以下 → 直通；② S 顶到 3.80+ → 豁免。
两边同时打：削共享腿权重（cfoev45/xrent），加独有腿权重（价格反转 + 独有财务腿）。

w182_01 原式 = 1.5*CFOEV + XR + GL + REVT + 2.0*REV2 + 2.0*ILLIQ + 2.0*R5
"""
import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


CFOEV = 'ts_av_diff(cashflow_op/enterprise_value,45)'
XR = 'fnd6_xrent/assets'
GL = 'fnd6_newqv1300_glcea12/assets'
REVT = 'fnd6_mfma2_revt/assets'
INTG = '-annual_intangible_assets_net_carrying_value/assets'
ACCR = '-(fnd6_newa2v1300_ni - cashflow_op)/assets'
ALC = 'fn_accrued_liab_curr_a/assets'
INTC = 'fnd6_intc/assets'
TFVCE = 'fnd6_tfvce/assets'
REV2 = '-ts_delta(close, 2)'
REV5 = '-ts_delta(close, 5)'
REV10 = '-ts_delta(close, 10)'
ILLIQ = '-ts_mean(abs(returns)/volume, 20)'
R5 = '-ts_rank(returns, 5)'
R20 = '-ts_rank(returns, 20)'
VOL60 = 'volume/ts_mean(volume, 60)'
VOL120 = 'volume/ts_mean(volume, 120)'

c = {}
# --- A 组：削 cfoev（共享最重的一腿），价格腿加码 ---
c['w228_a'] = G(CFOEV, 0.75) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w228_b'] = G(CFOEV, 0.5) + ' + ' + G(XR, 0.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w228_c'] = G(CFOEV, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 3.0)   # 去 XR
c['w228_d'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)   # 去 XR，财务独有腿加重
c['w228_e'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(INTC, 1.5) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)

# --- B 组：换反转窗口（远离小市值价值族的季节面）---
c['w228_f'] = G(CFOEV, 0.75) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV5, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w228_g'] = G(CFOEV, 0.75) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV10, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w228_h'] = G(CFOEV, 0.75) + ' + ' + G(XR, 1.0) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.0) + ' + ' + G(ILLIQ, 2.0) + ' + ' + G(R20, 2.5) + ' + ' + G(VOL60, 1.0)

# --- C 组：顶夏普（把价格/量腿堆满）---
c['w228_i'] = G(CFOEV, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(GL, 0.5) + ' + ' + G(REVT, 0.5) + ' + ' + G(REV2, 3.0) + ' + ' + G(ILLIQ, 3.0) + ' + ' + G(R5, 3.0)
c['w228_j'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 3.0) + ' + ' + G(ILLIQ, 3.0) + ' + ' + G(R5, 3.0) + ' + ' + G(VOL120, 1.0)
c['w228_k'] = G(CFOEV, 0.75) + ' + ' + G(GL, 1.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(REV2, 3.0) + ' + ' + G(ILLIQ, 3.0) + ' + ' + G(R5, 3.0)
c['w228_l'] = G(CFOEV, 0.75) + ' + ' + G(GL, 1.0) + ' + ' + G(ALC, 1.5) + ' + ' + G(REV2, 3.0) + ' + ' + G(ILLIQ, 3.0) + ' + ' + G(R5, 2.5)

# --- D 组：独有锚替换（GL 换成池子里没当锚用过的）---
c['w228_m'] = G(CFOEV, 0.75) + ' + ' + G(TFVCE, 1.5) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5) + ' + ' + G(INTG, 0.5)
c['w228_n'] = G(CFOEV, 0.75) + ' + ' + G(INTC, 1.5) + ' + ' + G(REVT, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5) + ' + ' + G(INTG, 0.5)

json.dump(c, open('_autologs/leg_combos_w228.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('w228', len(c))
