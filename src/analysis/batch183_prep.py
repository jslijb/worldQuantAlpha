# -*- coding: utf-8 -*-
"""batch183_prep.py —— 定向变体离线预筛（不跑模拟）
围绕 0917 两条过线组合的家族做定向变体，用 leg_lab 的离线 PnL 线性近似算
pred corr（对 81 条台账池）与 pred S，只把 pred maxcorr ≤ 0.55 且 pred S ≥ 2.0
的落盘给 mine_batch181.py 执行。
产出：_autologs/search_combos_w185.json
"""
import os as _os, pathlib as _pl, sys, json
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
sys.argv = ['noop', 'noop']  # 让 leg_lab 模块级 dispatch 静默通过（无匹配命令即结束）
sys.path.insert(0, str(_p.parent))
import leg_lab as LL

PV3 = {'P_vw5': 0.75, 'P_vd': 0.75, 'N_tr5': 0.75}
SPECS = {
 # —— COV 锚家族（npdM3G7z = 1.5*COV + opex + 1.25*N_tr5 的兄弟变体）——
 'c_liab_tr5':  {'M_cov': 1.5, 'M_liab': 1, 'N_tr5': 1.25},
 'c_txp_tr5':   {'M_cov': 1.5, 'M_txp': 1, 'N_tr5': 1.25},
 'c_debt_tr5':  {'M_cov': 1.5, 'M_debt': 1, 'N_tr5': 1.25},
 'c_tstk_tr5':  {'M_cov': 1.5, 'M_tstk': 1, 'N_tr5': 1.25},
 'c_g12_tr5':   {'M_cov': 1.5, 'M_g12': 1, 'N_tr5': 1.25},
 'c_tfvce_tr5': {'M_cov': 1.5, 'M_tfvce': 1, 'N_tr5': 1.25},
 'c_revT_tr5':  {'M_cov': 1.5, 'M_revt': 1, 'N_tr5': 1.25},
 'c_intc_tr5':  {'M_cov': 1.5, 'M_intc': 1, 'N_tr5': 1.25},
 'c_acc_tr5':   {'M_cov': 1.5, 'M_acc': 1, 'N_tr5': 1.25},
 'c_liab_int':  {'M_cov': 1.5, 'M_liab': 1, 'P_int20': 1.25},
 'c_liab_am':   {'M_cov': 1.5, 'M_liab': 1, 'P_am20': 1.25},
 'c_liab_c5':   {'M_cov': 1.5, 'M_liab': 1, 'P_c5': 1.25},
 'c_liab_vd':   {'M_cov': 1.5, 'M_liab': 1, 'P_vd': 1.25},
 'c_liab_tr20': {'M_cov': 1.5, 'M_liab': 1, 'P_tr20': 1.25},
 'c_liab_v120': {'M_cov': 1.5, 'M_liab': 1, 'P_v120': 1.25},
 'c_opex_int':  {'M_cov': 1.5, 'M_opex': 1, 'P_int20': 1.25},
 'c_opex_am':   {'M_cov': 1.5, 'M_opex': 1, 'P_am20': 1.25},
 # —— totassets 锚家族（levb0dQx 的兄弟变体）——
 't_ni_liab_debt': {'M_tot': 1.5, 'M_ni': 1, 'M_liab': 1, 'M_debt': 1, **PV3},
 't_ni_txp_opex':  {'M_tot': 1.5, 'M_ni': 1, 'M_txp': 1, 'M_opex': 1, **PV3},
 't_ni_liab_tstk': {'M_tot': 1.5, 'M_ni': 1, 'M_liab': 1, 'M_tstk': 1, **PV3},
 't_cov_liab_opex':{'M_tot': 1.5, 'M_cov': 1, 'M_liab': 1, 'M_opex': 1, **PV3},
 't_liab_opex':    {'M_tot': 1.5, 'M_liab': 1, 'M_opex': 1, 'N_tr5': 1.25},
 'c_t_liab':       {'M_cov': 1.5, 'M_tot': 1, 'M_liab': 1, 'N_tr5': 1},
 'c_liab_txp_pv3': {'M_cov': 1.5, 'M_liab': 1, 'M_txp': 1, **PV3},
}

EXPR = dict(LL.__dict__.get('_leg_exprs', {})) if False else None
# 腿表达式取自 leg_lab search 分支的 EXPR 表——直接重建：
G = LL.G_EXPR
EXPR = {
 'M_cov': G('ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120)'),
 'M_tot': G('anl4_fs_detail_estimate_1qf_v4_nd_totassets_mean/assets'),
 'M_ni':  G('-(fnd6_newa2v1300_ni - cashflow_op)/assets'),
 'M_liab':G('liabilities_curr/assets'),
 'M_txp': G('fnd6_txtubpospinc/assets'),
 'M_debt':G('debt_st/assets'),
 'M_tstk':G('fnd6_tstkc/assets'),
 'M_g12': G('fnd6_newqv1300_glcea12/assets'),
 'M_tfvce':G('fnd6_tfvce/assets'),
 'M_revt':G('fnd6_mfma2_revt/assets'),
 'M_intc':G('fnd6_intc/assets'),
 'M_acc': G('ts_av_diff(assets_curr/assets,30)'),
 'M_opex':G('operating_expense/assets'),
 'P_c5':  G('-ts_delta(close, 5)'),
 'P_vw5': G('-ts_delta(vwap, 5)'),
 'P_v120':G('volume/ts_mean(volume, 120)'),
 'P_tr20':G('-ts_rank(returns, 20)'),
 'P_am20':G('-ts_mean(abs(returns)/volume, 20)'),
 'P_vd':  G('(close - vwap)/vwap'),
 'P_int20':G('-ts_rank(close/open - 1, 20)'),
 'N_tr5': G('-ts_rank(returns, 5)'),
}

out = {}
rank = []
for name, spec in SPECS.items():
    r = LL.eval_combo(spec, verbose=False)
    if r is None:
        print(name, 'SKIP (PnL 缺)'); continue
    rank.append((r['maxcorr'], r['S'], name, spec, r['top'][:3]))
rank.sort(key=lambda t: (t[0], -t[1]))
for mx, S, name, spec, top in rank:
    print(f'{name:16s} predS={S:.2f} predCorr={mx:.4f} 撞{top[0][1] if top else "-"}')
# 过滤：pred corr ≤ 0.55 且 pred S ≥ 2.0，按 S 降序取前 12
keep = [t for t in rank if t[0] <= 0.55 and t[1] >= 2.0]
keep.sort(key=lambda t: -t[1])
for i, (mx, S, name, spec, top) in enumerate(keep[:12]):
    parts = []
    for leg, w in spec.items():
        e = EXPR[leg]
        parts.append(f'{w}*{e}' if w != 1 else e)
    out[f'w185_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3), 'maxcorr': round(mx, 4),
                            'nearest': top[0][1] if top else '', 'spec': spec, 'src': name}
json.dump(out, open('_autologs/search_combos_w185.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n过线 {len(keep)} 条，落盘 {min(len(keep),12)} 条 → _autologs/search_combos_w185.json')
