import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'          # 日内反转（1YX6MA0M 的强腿）
NEWS = 'news_short_interest'                   # 0mR2K6lr 的独有腿
ANL4 = 'anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets'  # j23Pl0e5 的独有腿
LIAB = 'liabilities_curr/assets'               # e79kPeEM/kqjpepz8 的腿
LIQ = '-ts_mean(abs(returns)/volume, 20)'      # pwRwWoJ3 的流动性腿
REV20 = '-ts_rank(returns, 20)'
CFOEV = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'
XR = G('fnd6_xrent/assets', 0.5)
INTC = G('fnd6_intc/assets', 0.5)

comb = {}
comb['w222_a'] = {'expr': G(INV, 1.0) + ' + ' + G(NEWS, 2.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_b'] = {'expr': G(INV, 1.5) + ' + ' + G(NEWS, 2.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_c'] = {'expr': G(INV, 1.5) + ' + ' + G(ANL4, 1.5) + ' + ' + INTC + ' + ' + CFOEV}
comb['w222_d'] = {'expr': G(INV, 1.0) + ' + ' + G(ANL4, 2.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_e'] = {'expr': G(INV, 1.5) + ' + ' + G(LIAB, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_f'] = {'expr': G(INV, 1.5) + ' + ' + G(LIQ, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_g'] = {'expr': G(INV, 1.5) + ' + ' + G(REV20, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_h'] = {'expr': G(INV, 1.0) + ' + ' + G(NEWS, 1.0) + ' + ' + G(ANL4, 1.0) + ' + ' + CFOEV}
comb['w222_i'] = {'expr': G(NEWS, 2.0) + ' + ' + G(ANL4, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w222_j'] = {'expr': G(INV, 1.5) + ' + ' + G(NEWS, 1.5) + ' + ' + XR + ' + ' + CFOEV + ' + 0.5*group_rank(volume/ts_mean(volume, 60), subindustry)'}

json.dump(comb, open('_autologs/leg_combos_w222.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
