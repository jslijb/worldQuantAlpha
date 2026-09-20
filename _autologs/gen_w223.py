import json, os
os.chdir(r"D:\Python\worldquant")


def G(e, w, grp='subindustry'):
    return f'{w}*group_rank({e}, {grp})'


INV = '-ts_rank(close/open - 1, 10)'   # 日内反转（强度腿）
XR = G('fnd6_xrent/assets', 0.5)
CFOEV = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'

# 各种"未与高 S 成员绑定"的配对腿
pairs = {
    'a': 'fnd6_txtubxintis/assets',
    'b': 'fn_accrued_liab_curr_a/assets',
    'c': '-ts_rank(close, 5)',
    'd': 'ts_av_diff(assets_curr/assets, 30)',
    'e': 'fnd6_pstkl/assets',
    'f': 'fnd6_tstkc/assets',
    'g': 'fnd6_newqv1300_ivstq/assets',
    'h': 'fnd6_mfma2_revt/assets',
    'i': 'fnd6_lqpl1/assets',
    'j': 'fnd6_newa2v1300_ni/assets',
}
comb = {}
for tag, leg in pairs.items():
    comb[f'w223_{tag}'] = {'expr': G(INV, 1.5) + ' + ' + G(leg, 1.5) + ' + ' + XR + ' + ' + CFOEV}
# k: 加权版（把 inv 提到 2.0 提 S）
comb['w223_k'] = {'expr': G(INV, 2.0) + ' + ' + G('fn_accrued_liab_curr_a/assets', 1.5) + ' + ' + XR + ' + ' + CFOEV}
json.dump(comb, open('_autologs/leg_combos_w223.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
