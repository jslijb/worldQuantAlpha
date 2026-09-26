# -*- coding: utf-8 -*-
"""probe_ops.py —— 查算子可用性 + 看 reg_res 已有产出（自写 UTF-8）"""
import io, json, os

ROOT = 'D:/Python/worldquant/'
L = []

f = ROOT + 'data/alpha_quality_analysis/operators.json'
L.append('operators.json 存在: %s' % os.path.exists(f))
names = set()
if os.path.exists(f):
    d = json.load(io.open(f, encoding='utf-8'))
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k in ('name', 'operator') and isinstance(v, str):
                    names.add(v)
                walk(v)
        elif isinstance(o, list):
            for x in o:
                walk(x)
    walk(d)
    L.append('解析出算子名 %d 个' % len(names))

WANT = ['ts_regression', 'ts_skewness', 'ts_kurtosis', 'ts_co_skewness', 'ts_co_kurtosis',
        'hump', 'ts_decay_linear', 'quantile', 'ts_rank', 'ts_zscore', 'ts_av_diff',
        'ts_std_dev', 'ts_corr', 'bucket', 'group_rank', 'vec_avg', 'vec_sum',
        'ts_min', 'ts_max', 'ts_arg_min', 'ts_arg_max', 'ts_backfill', 'signed_power',
        'ts_moment', 'ts_entropy', 'ts_count_nans', 'ts_scale', 'ts_sum', 'ts_product',
        'ts_median', 'ts_quantile', 'ts_returns', 'ts_theilsen', 'ts_triple_corr',
        'ts_poly_regression', 'ts_vector_neut', 'ts_vector_proj', 'regression_neut',
        'trade_when', 'if_else', 'winsorize', 'normalize', 'scale', 'rank', 'zscore']
if names:
    L.append('')
    L.append('== 目标算子可用性 ==')
    for w in WANT:
        L.append('  %-22s %s' % (w, '可用' if w in names else '❌ 未在清单中'))
else:
    L.append('(operators.json 无法解析，改为直接看官方清单文档)')

L.append('')
L.append('== reg_res 产出 ==')
g = ROOT + 'data/alpha_quality_analysis/mined/c04_s06_reg_res.json'
if os.path.exists(g):
    d = json.load(io.open(g, encoding='utf-8'))
    reg = d.get('regular') or {}
    i = d.get('is') or {}
    L.append('  _cid=%s id=%s' % (d.get('_cid'), d.get('id')))
    L.append('  expr=%s' % (str(reg.get('code') if isinstance(reg, dict) else reg)[:500]))
    L.append('  S=%.2f F=%.2f TO=%.4f tS=%.2f FAIL=%s'
             % (i.get('sharpe') or 0, i.get('fitness') or 0, i.get('turnover') or 0,
                (d.get('test') or {}).get('sharpe') or 0,
                [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']))
else:
    L.append('  (无)')

io.open(ROOT + '_autologs/_ops_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
