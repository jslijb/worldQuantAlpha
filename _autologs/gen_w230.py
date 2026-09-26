# -*- coding: utf-8 -*-
"""w230 —— 换中性化破墙：INDUSTRY 低墙区

硬数据（0920 exempt 全池扫描）三层墙（全部 SUBINDUSTRY 系）：
  0mR2K6lr 3.45 / pwRwWoJ3 3.33 / mLgd6nwX 3.17 → 需 S 3.80/3.66/3.49，够不着
但池子里 INDUSTRY 那一族的 S 天花板只有 e79kPeEM 3.02，
  而 e79kPeEM = liabilities_curr/assets + ts_av_diff(cfoev,60) + -ts_rank(close,5), INDUSTRY
⇒ 只要避开 cfoev60 和 -ts_rank(close,5)，
  INDUSTRY 族里剩下的最高只有 j23nOrVW 1.92 / 58QVJA9M 2.15 → 豁免线只需 S≈2.1~2.4
同时把今天验证过的最强夏普腿（-ts_rank(close/open-1,10)）以高权塞进去冲 S。
"""
import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='industry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'
ILLIQ = '-ts_mean(abs(returns)/volume, 20)'
LIAB = 'liabilities_curr/cap'
LIABC = 'liabilities_curr/assets'
ACCR = '-(fnd6_newa2v1300_ni - cashflow_op)/assets'
CORRV = '-ts_corr(close, volume, 20)'
PRC20 = '-ts_av_diff(close, 20)'
REVT = 'fnd6_mfma2_revt/assets'
XOPR = 'fnd6_xopr/assets'
XR = 'fnd6_xrent/assets'
TFVCE = 'fnd6_tfvce/assets'


def C(expr, neut='INDUSTRY', decay=10):
    return {'expr': expr, 'neutralization': neut, 'decay': decay}


c = {}
c['w230_a'] = C(G(INV, 2.0) + ' + ' + G(LIAB, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(XR, 0.5))
c['w230_b'] = C(G(INV, 2.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(ACCR, 1.0) + ' + ' + G(XR, 0.5))
c['w230_c'] = C(G(INV, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(REVT, 1.0) + ' + ' + G(XR, 0.5))
c['w230_d'] = C(G(INV, 2.0) + ' + ' + G(PRC20, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(XR, 0.5))
c['w230_e'] = C(G(INV, 2.0) + ' + ' + G(ACCR, 1.5) + ' + ' + G(PRC20, 1.5) + ' + ' + G(REVT, 1.0))
c['w230_f'] = C(G(INV, 2.5) + ' + ' + G(LIAB, 1.0) + ' + ' + G(ACCR, 1.0) + ' + ' + G(CORRV, 1.0) + ' + ' + G(XOPR, 0.5))
c['w230_g'] = C(G(INV, 2.0) + ' + ' + G(CORRV, 2.0) + ' + ' + G(ACCR, 1.0) + ' + ' + G(XR, 0.5) + ' + ' + G(LIAB, 0.5))
c['w230_h'] = C(G(INV, 3.0) + ' + ' + G(CORRV, 1.0) + ' + ' + G(ACCR, 1.0) + ' + ' + G(XR, 0.5))
c['w230_i'] = C(G(INV, 2.0) + ' + ' + G(ILLIQ, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(XR, 0.5))
c['w230_j'] = C(G(INV, 1.5) + ' + ' + G(ILLIQ, 1.5) + ' + ' + G(CORRV, 2.0) + ' + ' + G(XR, 0.5))
c['w230_k'] = C(G(INV, 2.0) + ' + ' + G(LIABC, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(TFVCE, 1.0))
c['w230_l'] = C(G(INV, 2.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(XR, 0.5), decay=6)
c['w230_m'] = C(G(INV, 2.0) + ' + ' + G(LIAB, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(XR, 0.5), decay=15)
# 对照组：同式 SUBINDUSTRY，用来量化"换中性化到底降多少 corr"
c['w230_n'] = C(G(INV, 2.0) + ' + ' + G(LIAB, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(XR, 0.5), neut='SUBINDUSTRY')
c['w230_o'] = C(G(INV, 2.5) + ' + ' + G(CORRV, 1.5) + ' + ' + G(ACCR, 1.0) + ' + ' + G(XR, 0.5), neut='SUBINDUSTRY')

json.dump(c, open('_autologs/leg_combos_w230.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('w230', len(c))
