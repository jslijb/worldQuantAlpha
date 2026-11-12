
## 2. 经济学/金融学机制 idea（idea_generator.py 产出，2026-10-09）

> 这些是**此前不存在**的新腿，按机制产出、不参照已有表达式（李工 1009 指令）。
> 未跑过的标「新造」；跑过后在 §4 登记簿回写结果。

### M01 信息传递不充分（price discovery）

**机制**：价格对新信息反应不足 → 前期公告类信号在中期仍有预测力；反应过度则反转。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E101 | `group_rank(-ts_mean(returns, 60), industry)` | 长周期负收益 = 市场对前期坏消息反应过度，中期反转 | turnover_rev | 新造 |
| E102 | `group_rank(ts_delta(returns, 5), subindustry)` | 短期收益跳升 = 信息已被消化，短期动量 | mom_short | 新造 |
| E103 | `group_rank(-ts_delta(returns, 20), bucket(rank(adv20), range="0.1, 1, 0.1"))` | 流动性差的股票价格调整慢，反转更强 | illiq_rev | 新造 |

### M02 流动性与交易成本

**机制**：流动性溢价：低流动性资产需要更高回报补偿，但高冲击成本会侵蚀收益。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E201 | `group_rank(volume/ts_mean(volume, 120), subindustry)` | 相对放量 → 关注度上升 | liq_surprise | 新造 |
| E202 | `group_rank(ts_std_dev(returns, 20), bucket(rank(cap), range="0.1, 1, 0.1"))` | 小盘高波动 = 流动性风险暴露 | liq_risk | 新造 |
| E203 | `group_rank(volume/ts_mean(volume, 250), subindustry)` | 年度尺度相对放量，剔除季节性 | liq_surprise_long | 新造 |

### M03 投资者行为偏差（过度反应 / 处置效应）

**机制**：投资者对极端信息过度反应，随后回归；散户持仓集中度高的股票反转更强。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E301 | `group_rank(-ts_rank(close/open - 1, 20), subindustry)` | 日内涨幅极端 → 处置效应卖出压力 | disposition | 新造 |
| E302 | `group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)` | 深度下跌后择时抄底资金进场 | capitulation | 新造 |
| E303 | `group_rank(-ts_mean(open/ts_delay(close, 1) - 1, 5), subindustry)` | 隔夜跳空频繁 = 情绪化定价 | overnight_gap | 新造 |

### M04 质量溢价与风险补偿

**机制**：稳健盈利、低杠杆公司享有质量溢价，但被过度定价时同样跑输。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E401 | `group_rank(cashflow_op/enterprise_value, subindustry)` | 经营现金流 / 企业价值 = 收益率，质量溢价 | q_cfo_yield | 新造 |
| E402 | `group_rank(ebit/enterprise_value, industry)` | 息税前利润 / EV = 无杠杆要求回报 | q_ebit_yield | 新造 |
| E403 | `group_rank(-liabilities_curr/assets, subindustry)` | 低短债负担 = 财务稳健溢价 | q_leverage | 新造 |

### M05 分析师预期修正

**机制**：分析师上调预测后价格仍有 3~12 个月的漂移（PEAD，盈余公告后漂移）。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E501 | `group_rank(ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindustry)` | 近月 EPS 预期修正幅度 | pead_eps | 新造 |
| E502 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, industry)` | 分析师预测水平本身（含分歧） | analyst_level | 新造 |
| E503 | `group_rank(analyst_revision_rank_derivative, subindustry)` | 预期排名导数 = 修正方向 | pead_rank | 新造 |

### M06 公司行为（增发 / 回购 / 并购）

**机制**：增发折价稀释 → 中期跑输；回购信号管理层低估自身价值 → 中期跑赢。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E601 | `group_rank(ts_delta(cash/assets, 60), subindustry)` | 现金头寸变化方向，代理回购/增发 | cash_action | 新造 |
| E602 | `group_rank(fnd6_newqv1300_cicurrq/assets, subindustry)` | 投资变动方向，代理资本开支周期 | capex_cycle | 新造 |
| E603 | `group_rank(ts_av_diff(cash/assets, 45), bucket(rank(ts_rank(cap, 250)), range="0.1, 1, 0.1"))` | 按市值分层的现金积累速度 | cash_accum | 新造 |

### M07 融资约束与资产负债表

**机制**：融资约束企业投资受限 → 投资不足；外源融资依赖度高的企业风险溢价高。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E701 | `group_rank(liabilities_curr/assets, industry)` | 短期融资依赖 | fin_constraint | 新造 |
| E702 | `group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry)` | 无形资产占比低 = 资产更硬，抵押能力强 | asset_tangibility | 新造 |
| E703 | `group_rank(ts_av_diff(assets_curr/assets, 90), subindustry)` | 流动性结构随时间变化 | asset_mix_shift | 新造 |

### M08 风险分解（系统 / 特质）

**机制**：总收益里能被市场解释的部分 vs 公司特有部分；特质风险定价不足处有溢价。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E801 | `group_rank(systematic_risk_last_30_days, sector)` | 系统性风险暴露（平台无人区字段，userCount 519~1318） | sys_risk | 新造 |
| E802 | `group_rank(unsystematic_risk_last_30_days, subindustry)` | 特质风险暴露（同上） | idio_risk | 新造 |
| E803 | `group_rank(systematic_risk_last_30_days - unsystematic_risk_last_30_days, industry)` | 两类风险之差 = 风险结构偏移 | risk_mix | 新造 |

### M09 多因子评分（模型类字段）

**机制**：平台模型类字段本身是复合打分，其导数 = 隐含预期变化。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E901 | `group_rank(fscore_bfl_artifact, subindustry)` | 模型综合评分原始值 | fscore_raw | 新造 |
| E902 | `group_rank(fscore_bfl_composite_score_derivative, industry)` | 综合评分导数 = 隐含预期变化 | fscore_deriv | 新造 |
| E903 | `group_rank(composite_factor_score_derivative, subindustry)` | 复合因子评分导数 | cf_deriv | 新造 |

### M10 新闻 / 情绪向量

**机制**：新闻情绪未被完全定价，情绪改善后有漂移。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1001 | `group_rank(vec_avg(nws18_qep), subindustry)` | 新闻情绪极性均值 | news_sent | 新造 |
| E1002 | `group_rank(vec_avg(nws18_nip), subindustry)` | 新闻净影响极性 | news_nip | 新造 |

### M12 表外契约义务与股权稀释（1011 新造）

**机制**：租赁付款计划、股权激励费用、未行权期权行权价是"契约性的未来流出"，不进利润表主流口径、分析师模型常不覆盖 ⇒ 定价不充分；义务久期越长、稀释越重，未来现金流被占用越多，中期跑输。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1201 | `group_rank(ts_rank(operating_lease_minimum_payments_due_five_years/assets, 88), subindustry)` | 五年租赁最小付款/资产 = 契约杠杆的久期视角 | lease_dur | 新造 |
| E1202 | `group_rank(ts_rank(operating_leases_min_payments_3y/assets, 88), industry)` | 三年租赁最小付款/资产 = 中短期契约刚性支出 | lease_3y | 新造 |
| E1203 | `group_rank(ts_rank(share_award_expense_total/assets, 88), subindustry)` | 股权激励费用/资产 = 用股权替代现金薪酬的隐性稀释成本 | sbc_dil | 新造 |
| E1204 | `group_rank(ts_rank(options_outstanding_avg_exercise_price/close - 1, 88), industry)` | 未行权期权平均行权价相对现价 = 激励对齐度（越价外管理层越不着急） | opt_moneyness | 新造 |

### M13 管理层指引区间（1011 新造，analyst4 guidance 无人区 userCount 1~18）

**机制**：指引是管理层对未来的自我承诺：区间宽度=管理层自身不确定度，下限=保守锚，上限/现价=市场对该承诺的定价折度。第三方分析师跟随滞后 ⇒ 价格对管理层自我披露反应不足。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1301 | `group_rank(ts_rank((anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance - anl4_fs_guidances_advanced_af_nd_ebitda_minguidance)/abs(anl4_fs_guidances_advanced_af_nd_ebitda_minguidance), 88), subindustry)` | EBITDA 指引区间相对宽度 = 管理层不确定度 | guid_width_ebitda | 新造 |
| E1302 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance/close, 88), industry)` | EBITDA 指引上限/现价 = 隐含 EBITDA 收益率（管理层口径） | guid_yield | 新造 |
| E1303 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_cfi_minguidance/assets, 88), subindustry)` | 投资现金流指引下限/资产 = 管理层资本开支保守度 | guid_capex_floor | 新造 |
| E1304 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_epsr_minguidance/anl4_fs_guidances_advanced_af_nd_epsr_maxguidance, 88), industry)` | EPS 指引下/上限比 = 指引不对称（比值低 = 悲观下限拉开） | guid_skew | 新造 |

### M14 期权隐含风险的期限结构（1011 新造，绕开 skew 腿）

**机制**：长期 IV / 短期 IV = 不确定性是暂时事件冲击还是持久状态。期限斜率高 = 市场把风险定价在近端（事件型），事件过后回归；斜率低 = 风险是结构性的，长期被压制。与 moneyness skew 是不同维度，可避开 option8 已入池家族的撞点（atoms.md M-14：含 skew 腿一律撞）。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1401 | `group_rank(ts_rank(implied_volatility_mean_360/implied_volatility_mean_60 - 1, 88), industry)` | IV 期限斜率（均值口径 360/60） | iv_term | 新造 |
| E1402 | `group_rank(ts_rank(implied_volatility_call_360/implied_volatility_call_60 - 1, 88), subindustry)` | 看涨侧期限斜率 = 上行不确定性的久期 | iv_term_call | 新造 |
| E1403 | `group_rank(ts_rank(implied_volatility_put_360/implied_volatility_put_60 - 1, 88), market)` | 看跌侧期限斜率 = 下行保护成本的久期 | iv_term_put | 新造 |
| E1404 | `group_rank(ts_rank(implied_volatility_mean_1080/implied_volatility_mean_30 - 1, 88), industry)` | 超长/超短 IV 斜率（更极端的久期对比） | iv_term_long | 新造 |

### M15 商业关系图谱位置（1011 新造，pv13 供应链/客户关系图）

**机制**：公司在客户-竞争关系网络中的枢纽度决定信息暴露与冲击传导速度：枢纽节点被充分定价、边缘节点传导慢 ⇒ 收益补偿差异；竞争者相对数量 = 竞争强度，侵蚀超额收益的持续性。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1501 | `group_rank(ts_rank(pv13_ustomergraphrank_hub_rank, 88), industry)` | 客户图谱枢纽度（被多少客户节点指向） | cust_hub | 新造 |
| E1502 | `group_rank(ts_rank(pv13_revere_index_value, 88), subindustry)` | 供应链暴露指数 | sc_expose | 新造 |
| E1503 | `group_rank(ts_rank(rel_num_comp, 88), industry)` | 竞争对手相对数量 = 竞争强度 | comp_intens | 新造 |
| E1504 | `group_rank(ts_rank(pv13_com_page_rank, 88), market)` | 公司关系图谱 PageRank = 网络中心度 | cust_pagerank | 新造 |

