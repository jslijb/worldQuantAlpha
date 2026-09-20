import json, os
os.chdir(r"D:\Python\worldquant")

ANCH = {
    'xrent': 'fnd6_xrent/assets',
    'intc': 'fnd6_intc/assets',
    'glcea12': 'fnd6_newqv1300_glcea12/assets',
    'intan': 'annual_intangible_assets_net_carrying_value/assets',
    'aqi': 'fnd6_aqi/assets',
    'dxd5': 'fnd6_dxd5/assets',
    'mfma2': 'fnd6_mfma2_revt/assets',
    'mibtq': 'fnd6_mfmq_mibtq/assets',
    'tfvce': 'fnd6_tfvce/assets',
    'cicurrq': 'fnd6_newqv1300_cicurrq/assets',
    'tstkc': 'fnd6_tstkc/assets',
    'pstkl': 'fnd6_pstkl/assets',
}


def L(k, w=0.5, grp='subindustry'):
    return f'{w}*group_rank({ANCH[k]}, {grp})'


ENG = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)'
ENG_B = '0.4*group_rank(ts_av_diff(cashflow_op/enterprise_value,45), bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'


def M(expr, w=2.5, grp='subindustry'):
    return f'{w}*group_rank({expr}, {grp})'


comb = {}
# a: high/low 日内振幅版
comb['w219_a'] = {'expr': M('-ts_rank(high/low - 1, 10)') + ' + ' + L('xrent') + ' + ' + L('glcea12') + ' + ' + L('intan') + ' + ' + ENG}
# b: vwap/close 版
comb['w219_b'] = {'expr': M('-ts_rank(vwap/close - 1, 10)') + ' + ' + L('xrent') + ' + ' + L('intc') + ' + ' + L('glcea12') + ' + ' + ENG}
# c: returns 版（close/delay）
comb['w219_c'] = {'expr': M('-ts_rank(close/ts_delay(close,1) - 1, 10)') + ' + ' + L('xrent') + ' + ' + L('glcea12') + ' + ' + L('aqi') + ' + ' + ENG}
# d: 窗口 20
comb['w219_d'] = {'expr': M('-ts_rank(close/open - 1, 20)') + ' + ' + L('xrent') + ' + ' + L('mfma2') + ' + ' + L('mibtq') + ' + ' + ENG}
# e: 换分组 bucket(60)
B60 = 'bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1")'
comb['w219_e'] = {'expr': M('-ts_rank(close/open - 1, 10)', grp=B60) + ' + ' + L('xrent', grp=B60) + ' + ' + L('glcea12', grp=B60) + ' + ' + L('tfvce', grp=B60) + ' + ' + ENG_B}
# f: high/low 短窗 5
comb['w219_f'] = {'expr': M('-ts_rank(high/low - 1, 5)') + ' + ' + L('xrent') + ' + ' + L('cicurrq') + ' + ' + L('tfvce') + ' + ' + ENG}
# g: vwap/close 短窗 5
comb['w219_g'] = {'expr': M('-ts_rank(vwap/close - 1, 5)') + ' + ' + L('intc') + ' + ' + L('glcea12') + ' + ' + L('dxd5') + ' + ' + ENG}
# h: returns 窗口 20
comb['w219_h'] = {'expr': M('-ts_rank(close/ts_delay(close,1) - 1, 20)') + ' + ' + L('xrent') + ' + ' + L('mibtq') + ' + ' + L('tfvce') + ' + ' + ENG}
# i: 主腿加权重到 3.5（提 S）
comb['w219_i'] = {'expr': M('-ts_rank(close/open - 1, 10)', w=3.5) + ' + ' + L('xrent') + ' + ' + L('glcea12') + ' + ' + L('intan') + ' + ' + ENG}
# j: 四锚版
comb['w219_j'] = {'expr': M('-ts_rank(close/open - 1, 10)') + ' + ' + L('xrent') + ' + ' + L('glcea12') + ' + ' + L('intan') + ' + ' + L('aqi') + ' + ' + ENG}
# k: 隔夜 vs 日内拆分（开盘缺口版）
comb['w219_k'] = {'expr': M('-ts_rank(open/ts_delay(close,1) - 1, 10)') + ' + ' + L('xrent') + ' + ' + L('glcea12') + ' + ' + L('intan') + ' + ' + ENG}
# l: 收盘位置版
comb['w219_l'] = {'expr': M('-ts_rank((close - low)/(high - low) - 0.5, 10)') + ' + ' + L('xrent') + ' + ' + L('pstkl') + ' + ' + L('tstkc') + ' + ' + ENG}

json.dump(comb, open('_autologs/leg_combos_w219.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
