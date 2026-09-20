import json, os
os.chdir(r"D:\Python\worldquant")

# 池里高 S 成员的独有字段（未被提交组合占用的新主腿候选）
# 0mR2K6lr S3.45 = buyback + intangible + news_short_interest
# j23Pl0e5 S3.25 = anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high + txtubxintis + cash45
# pwRwWoJ3 S3.33 = 1.5*cfoev45 + fn_accrued_liab_curr_a + intangible


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


ENG = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'
ENG2 = '0.5*group_rank(ts_av_diff(cash/assets, 45), subindustry) + 0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'

comb = {}
# 新主腿：news_short_interest（fundamental2，0mR2K6lr 用过但配不同锚）
comb['w221_a'] = {'expr': G('news_short_interest', 2.0) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + G('fnd6_newqv1300_glcea12/assets', 0.5) + ' + ' + ENG}
# 新主腿：anl4 分析师预测（j23Pl0e5 用过）
comb['w221_b'] = {'expr': G('anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets', 2.0) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + G('fnd6_newqv1300_glcea12/assets', 0.5) + ' + ' + ENG}
# 新主腿：fn_accrued_liab_curr_a（pwRwWoJ3/O0N0R5NY 用过）
comb['w221_c'] = {'expr': G('fn_accrued_liab_curr_a/assets', 2.0) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + G('annual_intangible_assets_net_carrying_value/assets', 0.5) + ' + ' + ENG}
# 双新主腿：news + anl4
comb['w221_d'] = {'expr': G('news_short_interest', 1.5) + ' + ' + G('anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets', 1.5) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + ENG}
# news_short_interest + fn_accrued
comb['w221_e'] = {'expr': G('news_short_interest', 1.5) + ' + ' + G('fn_accrued_liab_curr_a/assets', 1.5) + ' + ' + G('fnd6_intc/assets', 0.5) + ' + ' + ENG}
# 日内反转 + news（跨族稀释）
comb['w221_f'] = {'expr': G('-ts_rank(close/open - 1, 10)', 1.5) + ' + ' + G('news_short_interest', 1.5) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + ENG}
# anal4 + 日内反转
comb['w221_g'] = {'expr': G('anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets', 1.5) + ' + ' + G('-ts_rank(close/open - 1, 10)', 1.5) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + ENG}
# news 主腿 + 双引擎（质量强化）
comb['w221_h'] = {'expr': G('news_short_interest', 2.0) + ' + ' + G('fnd6_xrent/assets', 0.5) + ' + ' + G('fnd6_intc/assets', 0.5) + ' + ' + ENG2}

json.dump(comb, open('_autologs/leg_combos_w221.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
