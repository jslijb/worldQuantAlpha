# -*- coding: utf-8 -*-
"""w229 —— 压 corr 破 0.70 直通线（承接 w228）

硬数据（0920 exempt 全池扫描）：
  VkagZle0(w193_00) S=3.38 F=3.09 tS=3.14  corr=0.7027 vs 0mR2K6lr(3.45)  ← 只差 0.0027 到直通线
  j2ALzgRZ(w197_01) S=3.34 F=2.47 tS=2.93  corr=0.7030 vs pwRwWoJ3(3.33)  ← 差 0.0030
  1YXQJRoX(w182_01) S=3.51 F=3.18 tS=3.13  corr=0.7169
规律：w182_01 → w193_00 只把 1.5 权重从 CFOEV 挪到 REVT，corr 0.7169→0.7027。
⇒ 继续把权重从共享腿（CFOEV / XR）搬走，corr 应跌破 0.70 → 直通提交。
池子里没被当过锚的独有腿：fnd6_mfma2_revt / fnd6_newqv1300_glcea12 / fnd6_tfvce / fnd6_intc。
"""
import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


CFOEV = 'ts_av_diff(cashflow_op/enterprise_value,45)'
XR = 'fnd6_xrent/assets'
GL = 'fnd6_newqv1300_glcea12/assets'
REVT = 'fnd6_mfma2_revt/assets'
TFVCE = 'fnd6_tfvce/assets'
INTC = 'fnd6_intc/assets'
REV2 = '-ts_delta(close, 2)'
REV5 = '-ts_delta(close, 5)'
ILLIQ = '-ts_mean(abs(returns)/volume, 20)'
R5 = '-ts_rank(returns, 5)'
R20 = '-ts_rank(returns, 20)'
INV = '-ts_rank(close/open - 1, 10)'

c = {}
# --- A 组：CFOEV 归零/极低，独有财务腿顶替 ---
c['w229_a'] = G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(TFVCE, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_b'] = G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(INTC, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_c'] = G(CFOEV, 0.25) + ' + ' + G(GL, 1.25) + ' + ' + G(REVT, 1.5) + ' + ' + G(TFVCE, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_d'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(INTC, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_e'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(TFVCE, 1.0) + ' + ' + G(REV2, 3.0) + ' + ' + G(ILLIQ, 3.0) + ' + ' + G(R5, 3.0)

# --- B 组：X * 独有腿，去掉 XR ---
c['w229_f'] = G(CFOEV, 0.75) + ' + ' + G(GL, 1.5) + ' + ' + G(TFVCE, 1.5) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_g'] = G(CFOEV, 0.75) + ' + ' + G(REVT, 1.5) + ' + ' + G(INTC, 1.5) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_h'] = G(GL, 2.0) + ' + ' + G(REVT, 2.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5) + ' + ' + G(R20, 1.5)

# --- C 组：换反转窗口，避开 -ts_delta(close,10) 面 ---
c['w229_i'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(REV5, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_j'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.5) + ' + ' + G(REVT, 1.5) + ' + ' + G(REV5, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R20, 2.5)

# --- D 组：加 INV 做第 4 条价格腿（低权，避免撞自家 1YX6MA0M）---
c['w229_k'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.0) + ' + ' + G(REVT, 1.0) + ' + ' + G(INV, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5)
c['w229_l'] = G(CFOEV, 0.5) + ' + ' + G(GL, 1.0) + ' + ' + G(TFVCE, 1.0) + ' + ' + G(REV2, 2.5) + ' + ' + G(ILLIQ, 2.5) + ' + ' + G(R5, 2.5) + ' + ' + G(INV, 1.5)

json.dump(c, open('_autologs/leg_combos_w229.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('w229', len(c))
