import json, os
os.chdir(r"D:\Python\worldquant")

B = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'


def A(k, w):
    return f'{w}*group_rank({k}/assets, {B})'


ENG = f'0.5*group_rank(ts_av_diff(cash/assets, 45), {B}) + 0.5*group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), {B}) + 0.5*group_rank(-ts_delta(close, 2), {B}) + 0.5*group_rank(volume/ts_mean(volume, 60), {B})'
EV = '0.5*group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)'

M = 'fnd6_mfma2_revt'
T = 'fnd6_mfmq_mibtq'
V = 'fnd6_tfvce'
X = 'fnd6_xrent'
TX = 'fnd6_txs'

comb = {}
# a: 双锚加权 1.5 + 第三锚 0.75
comb['w220_a'] = {'expr': A(M, 1.5) + ' + ' + A(T, 1.5) + ' + ' + A(V, 0.75) + ' + ' + ENG + ' + ' + EV}
# b: 主锚 2.0 加权
comb['w220_b'] = {'expr': A(M, 2.0) + ' + ' + A(T, 1.0) + ' + ' + A(V, 0.75) + ' + ' + ENG + ' + ' + EV}
# c: 三锚 1.25 + 第四锚 0.75
comb['w220_c'] = {'expr': A(M, 1.25) + ' + ' + A(T, 1.25) + ' + ' + A(V, 1.25) + ' + ' + A(TX, 0.75) + ' + ' + ENG + ' + ' + EV}
# d: 三锚均权 1.5
comb['w220_d'] = {'expr': A(M, 1.5) + ' + ' + A(T, 1.5) + ' + ' + A(V, 1.5) + ' + ' + ENG + ' + ' + EV}
# e: 双锚 2.0 + 第四锚 xrent
comb['w220_e'] = {'expr': A(M, 2.0) + ' + ' + A(T, 2.0) + ' + ' + A(X, 0.5) + ' + ' + ENG + ' + ' + EV}
# f: 主锚 2.5 + 单锚 0.75 + 引擎 + 事件
comb['w220_f'] = {'expr': A(M, 2.5) + ' + ' + A(T, 0.75) + ' + ' + A(V, 0.75) + ' + ' + ENG + ' + ' + EV}
# g: 三锚 1.25 + 事件腿加重 0.75（防 corr 随加权升高）
comb['w220_g'] = {'expr': A(M, 1.25) + ' + ' + A(T, 1.25) + ' + ' + A(V, 1.25) + ' + ' + ENG + ' + 0.75*group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)'}
# h: 三锚 1.5 + 事件腿 0.75
comb['w220_h'] = {'expr': A(M, 1.5) + ' + ' + A(T, 1.5) + ' + ' + A(V, 1.5) + ' + ' + ENG + ' + 0.75*group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)'}

json.dump(comb, open('_autologs/leg_combos_w220.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
print('written', len(comb))
