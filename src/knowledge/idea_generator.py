# -*- coding: utf-8 -*-
"""idea_generator.py —— 经济学/金融学机制 idea 生成进程（李工 1009 指令）

与 combo_gen.py 的分工：
  combo_gen.py    = 把**已有**原子腿组合起来（穷举两两 → 三三）
  idea_generator.py = **造新腿**：按经济学/金融学机制产出此前不存在的 idea

纪律：
  - 产出的是「机制 → 表达式骨架」，骨架必须过权限实测（atoms.md 记 PERM/MATH 死区）
  - 禁止使用 atoms.md 已判死操作（regression_neut / vector_neut / tanh / ts_median 等）
  - 产出登记到 _autologs/idea_econ.json，并可 --emit-md 回写进 idea.md

用法：
  python src/knowledge/idea_generator.py --list
  python src/knowledge/idea_generator.py --emit json --out _autologs/idea_econ.json
"""
import os as _os, io, json, argparse
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

# 10 类经济/金融机制 → 每类 2~4 条表达式骨架
# 字段只用已确认可用的（台账实证 + 全量字段库），未验证字段需先探权限
MECHANISMS = [
    {
        'mid': 'M01',
        'name': '信息传递不充分（price discovery）',
        'econ': '价格对新信息反应不足 → 前期公告类信号在中期仍有预测力；反应过度则反转。',
        'atoms': [
            ('E101', 'group_rank(-ts_mean(returns, 60), industry)',
             '长周期负收益 = 市场对前期坏消息反应过度，中期反转', 'turnover_rev'),
            ('E102', 'group_rank(ts_delta(returns, 5), subindustry)',
             '短期收益跳升 = 信息已被消化，短期动量', 'mom_short'),
            ('E103', 'group_rank(-ts_delta(returns, 20), bucket(rank(adv20), range="0.1, 1, 0.1"))',
             '流动性差的股票价格调整慢，反转更强', 'illiq_rev'),
        ],
    },
    {
        'mid': 'M02',
        'name': '流动性与交易成本',
        'econ': '流动性溢价：低流动性资产需要更高回报补偿，但高冲击成本会侵蚀收益。',
        'atoms': [
            ('E201', 'group_rank(volume/ts_mean(volume, 120), subindustry)',
             '相对放量 → 关注度上升', 'liq_surprise'),
            ('E202', 'group_rank(ts_std_dev(returns, 20), bucket(rank(cap), range="0.1, 1, 0.1"))',
             '小盘高波动 = 流动性风险暴露', 'liq_risk'),
            ('E203', 'group_rank(volume/ts_mean(volume, 250), subindustry)',
             '年度尺度相对放量，剔除季节性', 'liq_surprise_long'),
        ],
    },
    {
        'mid': 'M03',
        'name': '投资者行为偏差（过度反应 / 处置效应）',
        'econ': '投资者对极端信息过度反应，随后回归；散户持仓集中度高的股票反转更强。',
        'atoms': [
            ('E301', 'group_rank(-ts_rank(close/open - 1, 20), subindustry)',
             '日内涨幅极端 → 处置效应卖出压力', 'disposition'),
            ('E302', 'group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)',
             '深度下跌后择时抄底资金进场', 'capitulation'),
            ('E303', 'group_rank(-ts_mean(open/ts_delay(close, 1) - 1, 5), subindustry)',
             '隔夜跳空频繁 = 情绪化定价', 'overnight_gap'),
        ],
    },
    {
        'mid': 'M04',
        'name': '质量溢价与风险补偿',
        'econ': '稳健盈利、低杠杆公司享有质量溢价，但被过度定价时同样跑输。',
        'atoms': [
            ('E401', 'group_rank(cashflow_op/enterprise_value, subindustry)',
             '经营现金流 / 企业价值 = 收益率，质量溢价', 'q_cfo_yield'),
            ('E402', 'group_rank(ebit/enterprise_value, industry)',
             '息税前利润 / EV = 无杠杆要求回报', 'q_ebit_yield'),
            ('E403', 'group_rank(-liabilities_curr/assets, subindustry)',
             '低短债负担 = 财务稳健溢价', 'q_leverage'),
        ],
    },
    {
        'mid': 'M05',
        'name': '分析师预期修正',
        'econ': '分析师上调预测后价格仍有 3~12 个月的漂移（PEAD，盈余公告后漂移）。',
        'atoms': [
            ('E501', 'group_rank(ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindustry)',
             '近月 EPS 预期修正幅度', 'pead_eps'),
            ('E502', 'group_rank(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, industry)',
             '分析师预测水平本身（含分歧）', 'analyst_level'),
            ('E503', 'group_rank(analyst_revision_rank_derivative, subindustry)',
             '预期排名导数 = 修正方向', 'pead_rank'),
        ],
    },
    {
        'mid': 'M06',
        'name': '公司行为（增发 / 回购 / 并购）',
        'econ': '增发折价稀释 → 中期跑输；回购信号管理层低估自身价值 → 中期跑赢。',
        'atoms': [
            ('E601', 'group_rank(ts_delta(cash/assets, 60), subindustry)',
             '现金头寸变化方向，代理回购/增发', 'cash_action'),
            ('E602', 'group_rank(fnd6_newqv1300_cicurrq/assets, subindustry)',
             '投资变动方向，代理资本开支周期', 'capex_cycle'),
            ('E603', 'group_rank(ts_av_diff(cash/assets, 45), bucket(rank(ts_rank(cap, 250)), range="0.1, 1, 0.1"))',
             '按市值分层的现金积累速度', 'cash_accum'),
        ],
    },
    {
        'mid': 'M07',
        'name': '融资约束与资产负债表',
        'econ': '融资约束企业投资受限 → 投资不足；外源融资依赖度高的企业风险溢价高。',
        'atoms': [
            ('E701', 'group_rank(liabilities_curr/assets, industry)',
             '短期融资依赖', 'fin_constraint'),
            ('E702', 'group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry)',
             '无形资产占比低 = 资产更硬，抵押能力强', 'asset_tangibility'),
            ('E703', 'group_rank(ts_av_diff(assets_curr/assets, 90), subindustry)',
             '流动性结构随时间变化', 'asset_mix_shift'),
        ],
    },
    {
        'mid': 'M08',
        'name': '风险分解（系统 / 特质）',
        'econ': '总收益里能被市场解释的部分 vs 公司特有部分；特质风险定价不足处有溢价。',
        'atoms': [
            ('E801', 'group_rank(systematic_risk_last_30_days, sector)',
             '系统性风险暴露（平台无人区字段，userCount 519~1318）', 'sys_risk'),
            ('E802', 'group_rank(unsystematic_risk_last_30_days, subindustry)',
             '特质风险暴露（同上）', 'idio_risk'),
            ('E803', 'group_rank(systematic_risk_last_30_days - unsystematic_risk_last_30_days, industry)',
             '两类风险之差 = 风险结构偏移', 'risk_mix'),
        ],
    },
    {
        'mid': 'M09',
        'name': '多因子评分（模型类字段）',
        'econ': '平台模型类字段本身是复合打分，其导数 = 隐含预期变化。',
        'atoms': [
            ('E901', 'group_rank(fscore_bfl_artifact, subindustry)',
             '模型综合评分原始值', 'fscore_raw'),
            ('E902', 'group_rank(fscore_bfl_composite_score_derivative, industry)',
             '综合评分导数 = 隐含预期变化', 'fscore_deriv'),
            ('E903', 'group_rank(composite_factor_score_derivative, subindustry)',
             '复合因子评分导数', 'cf_deriv'),
        ],
    },
    {
        'mid': 'M10',
        'name': '新闻 / 情绪向量',
        'econ': '新闻情绪未被完全定价，情绪改善后有漂移。',
        'atoms': [
            ('E1001', 'group_rank(vec_avg(nws18_qep), subindustry)',
             '新闻情绪极性均值', 'news_sent'),
            ('E1002', 'group_rank(vec_avg(nws18_nip), subindustry)',
             '新闻净影响极性', 'news_nip'),
        ],
    },
    {
        'mid': 'M12',
        'name': '表外契约义务与股权稀释（1011 新造）',
        'econ': '租赁付款计划、股权激励费用、未行权期权行权价是"契约性的未来流出"，'
                '不进利润表主流口径、分析师模型常不覆盖 ⇒ 定价不充分；'
                '义务久期越长、稀释越重，未来现金流被占用越多，中期跑输。',
        'atoms': [
            ('E1201', 'group_rank(ts_rank(operating_lease_minimum_payments_due_five_years/assets, 88), subindustry)',
             '五年租赁最小付款/资产 = 契约杠杆的久期视角', 'lease_dur'),
            ('E1202', 'group_rank(ts_rank(operating_leases_min_payments_3y/assets, 88), industry)',
             '三年租赁最小付款/资产 = 中短期契约刚性支出', 'lease_3y'),
            ('E1203', 'group_rank(ts_rank(share_award_expense_total/assets, 88), subindustry)',
             '股权激励费用/资产 = 用股权替代现金薪酬的隐性稀释成本', 'sbc_dil'),
            ('E1204', 'group_rank(ts_rank(options_outstanding_avg_exercise_price/close - 1, 88), industry)',
             '未行权期权平均行权价相对现价 = 激励对齐度（越价外管理层越不着急）', 'opt_moneyness'),
        ],
    },
    {
        'mid': 'M13',
        'name': '管理层指引区间（1011 新造，analyst4 guidance 无人区 userCount 1~18）',
        'econ': '指引是管理层对未来的自我承诺：区间宽度=管理层自身不确定度，'
                '下限=保守锚，上限/现价=市场对该承诺的定价折度。'
                '第三方分析师跟随滞后 ⇒ 价格对管理层自我披露反应不足。',
        'atoms': [
            ('E1301', 'group_rank(ts_rank((anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance - anl4_fs_guidances_advanced_af_nd_ebitda_minguidance)/abs(anl4_fs_guidances_advanced_af_nd_ebitda_minguidance), 88), subindustry)',
             'EBITDA 指引区间相对宽度 = 管理层不确定度', 'guid_width_ebitda'),
            ('E1302', 'group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance/close, 88), industry)',
             'EBITDA 指引上限/现价 = 隐含 EBITDA 收益率（管理层口径）', 'guid_yield'),
            ('E1303', 'group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_cfi_minguidance/assets, 88), subindustry)',
             '投资现金流指引下限/资产 = 管理层资本开支保守度', 'guid_capex_floor'),
            ('E1304', 'group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_epsr_minguidance/anl4_fs_guidances_advanced_af_nd_epsr_maxguidance, 88), industry)',
             'EPS 指引下/上限比 = 指引不对称（比值低 = 悲观下限拉开）', 'guid_skew'),
        ],
    },
    {
        'mid': 'M14',
        'name': '期权隐含风险的期限结构（1011 新造，绕开 skew 腿）',
        'econ': '长期 IV / 短期 IV = 不确定性是暂时事件冲击还是持久状态。'
                '期限斜率高 = 市场把风险定价在近端（事件型），事件过后回归；'
                '斜率低 = 风险是结构性的，长期被压制。与 moneyness skew 是不同维度，'
                '可避开 option8 已入池家族的撞点（atoms.md M-14：含 skew 腿一律撞）。',
        'atoms': [
            ('E1401', 'group_rank(ts_rank(implied_volatility_mean_360/implied_volatility_mean_60 - 1, 88), industry)',
             'IV 期限斜率（均值口径 360/60）', 'iv_term'),
            ('E1402', 'group_rank(ts_rank(implied_volatility_call_360/implied_volatility_call_60 - 1, 88), subindustry)',
             '看涨侧期限斜率 = 上行不确定性的久期', 'iv_term_call'),
            ('E1403', 'group_rank(ts_rank(implied_volatility_put_360/implied_volatility_put_60 - 1, 88), market)',
             '看跌侧期限斜率 = 下行保护成本的久期', 'iv_term_put'),
            ('E1404', 'group_rank(ts_rank(implied_volatility_mean_1080/implied_volatility_mean_30 - 1, 88), industry)',
             '超长/超短 IV 斜率（更极端的久期对比）', 'iv_term_long'),
        ],
    },
    {
        'mid': 'M15',
        'name': '商业关系图谱位置（1011 新造，pv13 供应链/客户关系图）',
        'econ': '公司在客户-竞争关系网络中的枢纽度决定信息暴露与冲击传导速度：'
                '枢纽节点被充分定价、边缘节点传导慢 ⇒ 收益补偿差异；'
                '竞争者相对数量 = 竞争强度，侵蚀超额收益的持续性。',
        'atoms': [
            ('E1501', 'group_rank(ts_rank(pv13_ustomergraphrank_hub_rank, 88), industry)',
             '客户图谱枢纽度（被多少客户节点指向）', 'cust_hub'),
            ('E1502', 'group_rank(ts_rank(pv13_revere_index_value, 88), subindustry)',
             '供应链暴露指数', 'sc_expose'),
            ('E1503', 'group_rank(ts_rank(rel_num_comp, 88), industry)',
             '竞争对手相对数量 = 竞争强度', 'comp_intens'),
            ('E1504', 'group_rank(ts_rank(pv13_com_page_rank, 88), market)',
             '公司关系图谱 PageRank = 网络中心度', 'cust_pagerank'),
        ],
    },
]

# atoms.md 已判死 / 平台无权限，算子级黑名单（生成器自检用）
DEAD_OPS = ['regression_neut', 'vector_neut', 'floor', 'tanh', 'sigmoid', 's_log_1p',
            'ts_decay_exp_window', 'ts_median', 'scale_down', 'arc_tan',
            'ts_skewness', 'ts_kurtosis', 'moment', 'entropy', 'triple_corr']


def selfcheck():
    bad = []
    for m in MECHANISMS:
        for aid, expr, _, _ in m['atoms']:
            for op in DEAD_OPS:
                if op in expr:
                    bad.append((aid, op))
    return bad


def emit_json():
    out = []
    for m in MECHANISMS:
        for aid, expr, meaning, tag in m['atoms']:
            out.append({
                'idea_id': aid, 'mech_id': m['mid'], 'mech': m['name'],
                'econ': m['econ'], 'expr': expr, 'meaning': meaning,
                'tag': tag, 'status': '新造', 'used': False,
            })
    p = ROOT / '_autologs' / 'idea_econ.json'
    json.dump(out, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('经济/金融机制 idea %d 条 -> %s' % (len(out), p))
    return out


def emit_md():
    out = json.load(open(ROOT / '_autologs' / 'idea_econ.json', encoding='utf-8'))
    L = []
    L.append('')
    L.append('## 2. 经济学/金融学机制 idea（idea_generator.py 产出，2026-10-09）')
    L.append('')
    L.append('> 这些是**此前不存在**的新腿，按机制产出、不参照已有表达式（李工 1009 指令）。')
    L.append('> 未跑过的标「新造」；跑过后在 §4 登记簿回写结果。')
    L.append('')
    for m in MECHANISMS:
        L.append('### %s %s' % (m['mid'], m['name']))
        L.append('')
        L.append('**机制**：%s' % m['econ'])
        L.append('')
        L.append('| idea_id | 表达式 | 经济含义 | 标签 | 状态 |')
        L.append('|---|---|---|---|---|')
        for aid, expr, meaning, tag in m['atoms']:
            st = '新造'
            for r in out:
                if r['idea_id'] == aid:
                    st = r['status']
            L.append('| %s | `%s` | %s | %s | %s |' % (aid, expr, meaning, tag, st))
        L.append('')
    p = ROOT / 'docs' / 'methodology' / 'idea_econ_part.md'
    io.open(p, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
    print('md -> %s' % p)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--emit', choices=['json', 'md'])
    ap.add_argument('--out')
    a = ap.parse_args()
    bad = selfcheck()
    if bad:
        print('自检失败，命中判死算子：', bad)
        raise SystemExit(1)
    print('自检通过：无判死算子')
    if a.emit == 'json':
        emit_json()
    elif a.emit == 'md':
        emit_md()
    else:
        for m in MECHANISMS:
            print('%s %s —— %d 条原子' % (m['mid'], m['name'], len(m['atoms'])))
