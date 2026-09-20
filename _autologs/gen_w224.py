import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'
NEWS = 'news_short_interest'
ANL4 = 'anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets'
LIAB = 'liabilities_curr/assets'
FNAC = 'fn_accrued_liab_curr_a/assets'
TXT = 'fnd6_txtubxintis/assets'
XR = G('fnd6_xrent/assets', 0.5)
CFOEV = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'

comb = {}
comb['w224_a'] = {'expr': G(ANL4, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_b'] = {'expr': G(NEWS, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_c'] = {'expr': G(LIAB, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_d'] = {'expr': G(FNAC, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_e'] = {'expr': G(TXT, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_f'] = {'expr': G(ANL4, 2.0) + ' + ' + G(NEWS, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_g'] = {'expr': G(ANL4, 1.5) + ' + ' + G(LIAB, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_h'] = {'expr': G(NEWS, 1.5) + ' + ' + G(LIAB, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_i'] = {'expr': G(ANL4, 2.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_j'] = {'expr': G(NEWS, 2.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_k'] = {'expr': G(ANL4, 1.5) + ' + ' + G(TXT, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w224_l'] = {'expr': G(LIAB, 1.5) + ' + ' + G(FNAC, 1.5) + ' + ' + XR + ' + ' + CFOEV}

json.dump(comb, open('_autologs/leg_combos_w224.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
