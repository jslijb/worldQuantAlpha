import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'
XR = G('fnd6_xrent/assets', 0.5)
CFOEV = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'
CORRV = '-ts_corr(close, volume, 20)'                      # 量价负相关（低 S 区域专属腿）
ACCR = '-(fnd6_newa2v1300_ni - cashflow_op)/assets'        # 应计质量
PRC20 = '-ts_av_diff(close, 20)'                            # 20 日价格变动反转
CFOTR = 'ts_rank(cashflow_op/enterprise_value, 60)'         # 现金流时序排名

comb = {}
comb['w225_a'] = {'expr': G(INV, 1.5) + ' + ' + G(CORRV, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_b'] = {'expr': G(INV, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_c'] = {'expr': G(CORRV, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_d'] = {'expr': G(ACCR, 2.0) + ' + ' + G(INV, 1.0) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_e'] = {'expr': G(INV, 1.5) + ' + ' + G('liabilities_curr/cap', 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_f'] = {'expr': G(INV, 1.5) + ' + ' + G('ts_rank(cashflow_op/enterprise_value, 60)', 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_g'] = {'expr': G(INV, 1.5) + ' + ' + G(PRC20, 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_h'] = {'expr': G(CORRV, 2.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_i'] = {'expr': G(INV, 1.5) + ' + ' + G('fnd6_xopr/assets', 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_j'] = {'expr': G(INV, 1.5) + ' + ' + G('ts_av_diff(ebit/enterprise_value, 30)', 1.5) + ' + ' + XR + ' + ' + CFOEV}
comb['w225_k'] = {'expr': G(CORRV, 1.5) + ' + ' + G(ACCR, 1.5) + ' + ' + XR + ' + ' + CFOEV}

json.dump(comb, open('_autologs/leg_combos_w225.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
