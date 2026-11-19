# idea.md — Idea 原子库与组合登记簿（唯一事实源）

> 建立：2026-10-09（李工指令：「挖Alpha 因子始终要从idea 出发」「两两组合→三三组合」「已用组合要标记」「另开进程按经济学/金融学知识构建 idea 组合」）。

> **atoms.md 管「怎么打」，本文件管「打什么」**——atoms.md 是方法论库，idea.md 是 idea 库 + 组合登记簿。


## 0. 纪律（与 CLAUDE.md §3.10 同级，违反即违规）

1. **任何发模拟的批次，必须能追溯到本文件里若干个带ID 的 idea 原子**，且在 §3 组合登记簿登记。**不许凭空写表达式发模拟。**
2. **组合必须穷尽才升级**：先做全部两两组合（P×P）→用完再全部三三组合（P×P×P）→ 用完再四元。**不许跳级，也不许在同一组合上反复微调当新idea。**
3. **已用组合必须标记**：跑过的组合在 §3 登记簿打标记，写明结果（SF/tS/corr/入池与否）。**未标记的组合视同未挖。**
4. **已用组合不是废料，是下一跳的起点**：被corr 撞死的组合，其 idea 保留、只换载体（换分组轴 / 换窗长 / 换配腿），在 §3 标「可复活」，等池漂移或换轴时重新出。**禁止直接判死。**
5. **经济学/金融学进程是每日必做项**：另起进程按 10 类经济机制（信息传递 / 流动性溢价 / 行为偏差 / 质量溢价 / 分析师修正 / 公司行为 / 融资约束 / 风险分解 / 多因子评分 / 新闻情绪）产出**此前不存在**的新 idea 原子，**不参照已有表达式**，写入本文件 §2 后才可用于组合。生成器 `src/knowledge/idea_generator.py`。


## 1. Idea 原子库

### 1.1 F 类 — 基本面/估值机制原子（84 条，来自台账实证）

| idea_id | 表达式 | 台账用次数 | 金融含义 | 状态 |
|---|---|---|---|---|
| F001 | `group_rank(fnd6_xrent/assets, subindustry)` | 35 | 财务结构/估值 | 活跃 |
| F002 | `group_rank(-annual_intangible_assets_net_carrying_value/assets, subindustry)` | 18 | 财务结构/估值 | 活跃 |
| F003 | `group_rank(fn_accrued_liab_curr_a/assets, subindustry)` | 13 | 财务结构/估值 | 活跃 |
| F004 | `group_rank(liabilities_curr/assets, industry)` | 8 | 财务结构/估值 | 活跃 |
| F005 | `group_rank(liabilities_curr/assets, subindustry)` | 8 | 财务结构/估值 | 活跃 |
| F006 | `group_rank(fnd6_newqv1300_ivstq/assets, subindustry)` | 7 | 财务结构/估值 | 活跃 |
| F007 | `group_rank(-annual_intangible_assets_net_carrying_value / assets, subindustry)` | 7 | 财务结构/估值 | 活跃 |
| F008 | `group_rank(operating_expense/assets, subindustry)` | 6 | 财务结构/估值 | 活跃 |
| F009 | `group_rank(fnd6_newqv1300_glcea12/assets, subindustry)` | 6 | 财务结构/估值 | 活跃 |
| F010 | `group_rank(-(fnd6_newa2v1300_ni - cashflow_op) / assets, subindustry)` | 6 | 财务结构/估值 | 活跃 |
| F011 | `group_rank(fn_accrued_liab_curr_a / assets, subindustry)` | 6 | 财务结构/估值 | 活跃 |
| F012 | `group_rank(-(fnd6_newa2v1300_ni - cashflow_op)/assets, industry)` | 5 | 财务结构/估值 | 活跃 |
| F013 | `group_rank(fnd6_mfma2_revt/assets, industry)` | 5 | 财务结构/估值 | 活跃 |
| F014 | `group_rank(fnd6_newa1v1300_aol2/cap, subindustry)` | 5 | 财务结构/估值 | 活跃 |
| F015 | `group_rank(fnd6_pstkl/cap, subindustry)` | 5 | 财务结构/估值 | 活跃 |
| F016 | `group_rank(-(fnd6_newa2v1300_ni - cashflow_op)/assets, subindustry)` | 5 | 财务结构/估值 | 活跃 |
| F017 | `group_rank(fnd6_xrent/assets, industry)` | 4 | 财务结构/估值 | 活跃 |
| F018 | `group_rank(fnd6_newqv1300_cimiiq/assets, subindustry)` | 4 | 财务结构/估值 | 活跃 |
| F019 | `group_rank(authorized_stock_buyback_amount/assets, subindustry)` | 4 | 财务结构/估值 | 活跃 |
| F020 | `group_rank(fnd6_newqv1300_dpactq/cap, subindustry)` | 4 | 财务结构/估值 | 活跃 |
| F021 | `group_rank(fnd6_intc/assets, subindustry)` | 4 | 财务结构/估值 | 活跃 |
| F022 | `group_rank(fnd6_xrent / assets, subindustry)` | 4 | 财务结构/估值 | 活跃 |
| F023 | `group_rank(fnd6_xopr/assets, subindustry)` | 3 | 财务结构/估值 | 活跃 |
| F024 | `group_rank(fnd6_txtubadjust/cap, subindustry)` | 3 | 财务结构/估值 | 活跃 |
| F025 | `group_rank(-annual_intangible_assets_net_carrying_value/assets, industry)` | 3 | 财务结构/估值 | 活跃 |
| F026 | `group_rank(liabilities_curr/cap, industry)` | 2 | 财务结构/估值 | 活跃 |
| F027 | `group_rank(fnd6_mfma2_revt/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F028 | `group_rank(fnd6_newqv1300_lol2q/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F029 | `group_rank(fnd6_txtubxintis/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F030 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_grossincome_high/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F031 | `group_rank(fnd6_mfmq_mibtq/cap, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F032 | `group_rank(fnd6_lqpl1/cap, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F033 | `group_rank((close - vwap)/vwap, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F034 | `group_rank(fnd6_tfvce/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F035 | `group_rank(fnd6_txs/cap, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F036 | `group_rank(fnd6_newqv1300_cshopq/assets, subindustry)` | 2 | 财务结构/估值 | 活跃 |
| F037 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_cfi_low/assets, industry)` | 2 | 财务结构/估值 | 活跃 |
| F038 | `group_rank(-anl4_fs_detail_estimate_1qf_v4_nd_netdebt_mean/assets, industry)` | 2 | 财务结构/估值 | 活跃 |
| F039 | `group_rank(divide(liabilities_curr, assets), industry)` | 2 | 财务结构/估值 | 活跃 |
| F040 | `liabilities/assets` | 1 | 财务结构/估值 | 活跃 |
| F041 | `liabilities_curr/cap` | 1 | 财务结构/估值 | 活跃 |
| F042 | `group_rank(ts_sum(if_else(close < open, volume, 0), 5)/ts_sum(volume, 5), industry)` | 1 | 财务结构/估值 | 活跃 |
| F043 | `group_rank(debt_st/assets, industry)` | 1 | 财务结构/估值 | 活跃 |
| F044 | `group_rank(operating_expense/assets, industry)` | 1 | 财务结构/估值 | 活跃 |
| F045 | `signed_power(liabilities_curr/assets, 0.5)` | 1 | 财务结构/估值 | 活跃 |
| F046 | `liabilities_curr/assets` | 1 | 财务结构/估值 | 活跃 |
| F047 | `group_rank(fnd6_xopr/assets, industry)` | 1 | 财务结构/估值 | 活跃 |
| F048 | `group_rank(fnd6_xopr/assets,subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F049 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_ptpr_mean/assets, industry)` | 1 | 财务结构/估值 | 活跃 |
| F050 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_cfi_low/assets, subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F051 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_sga_median/assets, subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F052 | `group_rank(news_short_interest, subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F053 | `group_rank(forward_price_90/forward_price_30 - 1, subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F054 | `group_rank(-annual_intangible_assets_net_carrying_value/sales, subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F055 | `group_rank(-ts_arg_min(returns, 10), subindustry)` | 1 | 财务结构/估值 | 活跃 |
| F056 | `quantile(ts_av_diff(cashflow_op/enterprise_value,45))` | 1 | 财务结构/估值 | 活跃 |
| F057 | `group_rank(liabilities_curr/assets, sector)` | 1 | 财务结构/估值 | 活跃 |
| F058 | `group_rank(fnd6_xrent/assets, sector)` | 1 | 财务结构/估值 | 活跃 |
| F059 | `group_rank(fnd6_newqv1300_glcea12/assets, sector)` | 1 | 财务结构/估值 | 活跃 |
| F060 | `group_rank(anl4_fs_detail_estimate_1qf_v4_nd_ptpr_median/assets, subindustry)` | 1 | 财务结构/估值 | 活跃 |

### 1.2 T 类 — 量价/技术机制原子（234 条，来自台账实证）

| idea_id | 表达式 | 台账用次数 | 金融含义 | 状态 |
|---|---|---|---|---|
| T001 | `rank(volume/ts_mean(volume, 60))` | 28 | 量价/流动性 | 活跃 |
| T002 | `group_rank(-ts_delta(close, 2), subindustry)` | 27 | 量价/流动性 | 活跃 |
| T003 | `group_rank(-ts_rank(returns, 5), subindustry)` | 22 | 量价/流动性 | 活跃 |
| T004 | `group_rank(-ts_rank(returns, 20), subindustry)` | 21 | 量价/流动性 | 活跃 |
| T005 | `group_rank(-ts_mean(abs(returns)/volume, 20), subindustry)` | 21 | 量价/流动性 | 活跃 |
| T006 | `group_rank(ts_av_diff(cashflow_op/enterprise_value,45), subindustry)` | 19 | 量价/流动性 | 活跃 |
| T007 | `group_rank(ts_av_diff(cash/assets, 45), subindustry)` | 12 | 量价/流动性 | 活跃 |
| T008 | `rank(-ts_delta(close, 2))` | 11 | 量价/流动性 | 活跃 |
| T009 | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), subindustry)` | 11 | 量价/流动性 | 活跃 |
| T010 | `group_rank(-ts_rank(close, 5), industry)` | 10 | 量价/流动性 | 活跃 |
| T011 | `group_rank(-ts_rank(close/open - 1, 20), subindustry)` | 9 | 量价/流动性 | 活跃 |
| T012 | `group_rank(-ts_rank(returns, 20), industry)` | 8 | 量价/流动性 | 活跃 |
| T013 | `group_rank(ts_av_diff(cash/assets, 30), subindustry)` | 8 | 量价/流动性 | 活跃 |
| T014 | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), subindustry)` | 8 | 量价/流动性 | 活跃 |
| T015 | `group_rank(-ts_corr(close, volume, 20), industry)` | 7 | 量价/流动性 | 活跃 |
| T016 | `rank(volume/ts_mean(volume, 120))` | 7 | 量价/流动性 | 活跃 |
| T017 | `group_rank(volume/ts_mean(volume, 120), subindustry)` | 7 | 量价/流动性 | 活跃 |
| T018 | `group_rank(-ts_delta(close, 10), subindustry)` | 6 | 量价/流动性 | 活跃 |
| T019 | `group_rank(ts_av_diff(cash/assets,45), subindustry)` | 6 | 量价/流动性 | 活跃 |
| T020 | `group_rank(-ts_rank(close/open - 1, 10), subindustry)` | 6 | 量价/流动性 | 活跃 |
| T021 | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), bucket(rank(ts_std_dev(returns, 20)), range` | 6 | 量价/流动性 | 活跃 |
| T022 | `group_rank(ts_mean(anl4_fs_actual_1qf_v4_nd_netdebt_value - anl4_fs_detail_estimate_1qf_v4_nd_netdeb` | 6 | 量价/流动性 | 活跃 |
| T023 | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry)` | 5 | 量价/流动性 | 活跃 |
| T024 | `group_rank(ts_av_diff(cash/assets, 45), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 5 | 量价/流动性 | 活跃 |
| T025 | `group_rank(-ts_delta(close, 2), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 5 | 量价/流动性 | 活跃 |
| T026 | `group_rank(volume/ts_mean(volume, 60), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 5 | 量价/流动性 | 活跃 |
| T027 | `group_rank(ts_av_diff(cash/assets, 45), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")` | 4 | 量价/流动性 | 活跃 |
| T028 | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 45), bucket(rank(ts_mean(volume*close, 20)), ran` | 4 | 量价/流动性 | 活跃 |
| T029 | `group_rank(-ts_delta(close, 2), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 4 | 量价/流动性 | 活跃 |
| T030 | `group_rank(volume/ts_mean(volume, 60), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 4 | 量价/流动性 | 活跃 |
| T031 | `group_rank(ts_av_diff(assets_curr/assets,30), subindustry)` | 4 | 量价/流动性 | 活跃 |
| T032 | `group_rank(if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0), subindustry)` | 4 | 量价/流动性 | 活跃 |
| T033 | `group_rank(-ts_rank(close, 5), subindustry)` | 4 | 量价/流动性 | 活跃 |
| T034 | `group_rank(ts_delta(ts_backfill(((anl4_fs_guidances_advanced_qf_nd_netdebt_maxguidance + anl4_fs_gui` | 4 | 量价/流动性 | 活跃 |
| T035 | `group_rank(ts_av_diff(cash/assets, 30), industry)` | 3 | 量价/流动性 | 活跃 |
| T036 | `group_rank(-ts_rank(close, 10), industry)` | 3 | 量价/流动性 | 活跃 |
| T037 | `group_rank(-ts_av_diff(close, 20), industry)` | 3 | 量价/流动性 | 活跃 |
| T038 | `group_rank(-ts_delta(close, 5), industry)` | 3 | 量价/流动性 | 活跃 |
| T039 | `group_rank(fnd6_cicurr/assets, bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 3 | 量价/流动性 | 活跃 |
| T040 | `group_rank(fnd6_intc/assets, bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 3 | 量价/流动性 | 活跃 |
| T041 | `group_rank(-ts_delta(vwap, 5), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T042 | `group_rank(volume/ts_mean(volume, 90), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T043 | `group_rank(-ts_delta(close, 20), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T044 | `group_rank(-ts_rank(returns, 10), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T045 | `group_rank(-ts_rank(volume/ts_mean(volume, 120), 20), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T046 | `group_rank(-ts_mean(open/ts_delay(close, 1) - 1, 5), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T047 | `group_rank(-ts_delta(close, 5), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T048 | `group_rank(fnd6_newqv1300_cicurrq/assets, bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")` | 3 | 量价/流动性 | 活跃 |
| T049 | `group_rank(-ts_rank(close/open - 1, 10), industry)` | 3 | 量价/流动性 | 活跃 |
| T050 | `group_rank(-ts_mean(abs(returns)/volume, 20), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0` | 3 | 量价/流动性 | 活跃 |
| T051 | `group_rank(vec_avg(nws18_qep), subindustry)` | 3 | 量价/流动性 | 活跃 |
| T052 | `group_rank(ts_delta(fnd6_mfma2_revt, 252) / assets, industry)` | 3 | 量价/流动性 | 活跃 |
| T053 | `group_rank((0.4 * rank(-ts_delta(close, 2)) + group_rank(-ts_mean(abs(returns)/volume, 20), subindus` | 3 | 量价/流动性 | 活跃 |
| T054 | `group_rank(-ts_rank(close, 20), industry)` | 2 | 量价/流动性 | 活跃 |
| T055 | `group_rank(ts_av_diff(ebit/enterprise_value, 30), industry)` | 2 | 量价/流动性 | 活跃 |
| T056 | `rank(volume/ts_mean(volume, 90))` | 2 | 量价/流动性 | 活跃 |
| T057 | `group_rank(ts_av_diff(cash/assets, 45), bucket(rank(ts_rank(cap, 250)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T058 | `group_rank(volume/ts_mean(volume, 60), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T059 | `group_rank(-ts_rank(open/ts_delay(close, 1) - 1, 20), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T060 | `group_rank(-ts_mean(open/ts_delay(close,1) - 1, 5), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T061 | `group_rank(ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindus` | 2 | 量价/流动性 | 活跃 |
| T062 | `group_rank(if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T063 | `group_rank(liabilities_curr/assets, bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T064 | `group_rank(-ts_delta(close, 20), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T065 | `group_rank(fnd6_xrent/assets, bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T066 | `group_rank(-ts_delta(close, 5), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T067 | `group_rank(-ts_mean(abs(returns)/volume, 20), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1,` | 2 | 量价/流动性 | 活跃 |
| T068 | `group_rank(-ts_rank(returns, 5), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T069 | `group_rank(-ts_delta(close, 5), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T070 | `group_rank(-ts_rank(returns, 5), bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T071 | `group_rank(-ts_rank(returns, 20), bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T072 | `group_rank(ts_delta(cash/assets, 60), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T073 | `group_rank(ts_av_diff(cashflow_op/enterprise_value,45), bucket(rank(adv20), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T074 | `group_rank(-ts_rank(returns, 20), bucket(rank(adv20), range="0.1, 1, 0.1"))` | 2 | 量价/流动性 | 活跃 |
| T075 | `group_rank(ts_delta(fnd6_newa2v1300_ni / assets, 132), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T076 | `group_rank(vec_avg(nws18_nip), subindustry)` | 2 | 量价/流动性 | 活跃 |
| T077 | `(2.0*group_rank(ts_delta(fnd6_newa2v1300_ni / assets, 66), subindustry) + group_rank(-annual_intangi` | 2 | 量价/流动性 | 活跃 |
| T078 | `(2.0*1.5*group_rank(fnd6_pstkl/cap, subindustry) + group_rank(ts_av_diff(cashflow_op/enterprise_valu` | 2 | 量价/流动性 | 活跃 |
| T079 | `(group_rank(anl4_fs_detail_estimates_advanced_af_nd_capex_std/assets, industry) + group_rank(fnd6_ne` | 2 | 量价/流动性 | 活跃 |
| T080 | `(group_rank(liabilities_curr/assets, industry) + group_rank((ts_backfill(anl4_fs_actual_1qf_v4_nd_ca` | 2 | 量价/流动性 | 活跃 |

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
| **E504** | `group_rank((anl4_fs_guidances_advanced_af_nd_epsr_maxguidance - anl4_fs_guidances_advanced_af_nd_epsr_minguidance)/abs(anl4_fs_guidances_advanced_af_nd_epsr_minguidance), subindustry)` | **管理层 EPS 指引区间宽度**：maxguidance 与 minguidance 的相对差。区间宽 = 管理层自己都没把握 ⇒ 未来业绩不确定性高、预期分歧大 ⇒ 定价不足 | guid_width | **新造★**（cov=1.000 userCount=1，真无人区） |
| **E505** | `group_rank(anl4_fs_guidances_advanced_af_nd_cfo_minguidance/assets, subindustry)` | 管理层 CFO 指引下限/资产 = **管理层对自身现金流的保守度**。指引下限低 = 管理层预期差 ⇒ 下调风险 | guid_floor | 新造★ |
| **E506** | `group_rank((anl4_fs_guidances_advanced_af_nd_epsr_maxguidance + anl4_fs_guidances_advanced_af_nd_epsr_minguidance)/2 - anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, subindustry)` | **管理层指引中值 − 分析师预测** = 管理层与分析师的分歧。差大 = 分析师未跟随管理层调整 ⇒ 未来下修 ⇒ 跑输 | guid_gap | 新造★ |
| **E507** | `group_rank(anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance/anl4_fs_guidances_advanced_af_nd_ebitda_minguidance, subindustry)` | EBITDA 指引的上下限倍数（同 E504 的无量纲版本） | guid_ratio | 新造★ |

**M05-1010 使用边界**：
1. `anl4_fs_guidances_advanced_af_nd_*` 系列 **cov=1.000、userCount=1**（atoms.md §无人区已记）
   ⇒ 平台收录极少，**corr 天然低**，是 1010 后第二个降corr 方向（第一个是 f2 的 oci）。
2. 该系列每个指标成对存在 `maxguidance` / `minguidance`，天然形成"区间宽度"信号 ——
   这是 M05 机制（分析师预期修正）的**全新变体**：从"第三方分析师修正"转向
   "管理层自己的指引区间"，信息源更正、更少被套利。
3. ⚠ 未验证：`anl4_fs_detail_estimate_*` 系列在 atoms.md 记有"稀疏死数据"警告，
   E506 用到它，需先跑探针确认字段有效。E504/E505/E507 只用 guidance 系列，风险低。

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

### M11 会计科目穿透：绕过利润表直接进权益的科目（1010 新机制，fundamental2 数据集）

**机制**（与 M04 质量溢价的区别）：质量溢价看的是"利润质量"（应计、毛利），
本机制看的是**根本没经过利润表、直接计入权益的会计科目**。
这类科目满足三个条件：① 市场对其定价最不充分（不进利润表，分析师模型常不覆盖）；
② 常常是大额负值（养老金重估、外币折算差额）；③ 与资产负债表其他科目独立。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| **E1101** | `group_rank(other_comprehensive_income_net_tax/assets, subindustry)` | **其他综合收益/总资产**：外币折算差额+养老金重估+权益法份额+套期储备变动，全绕过利润表。OCI 高 = 净资产里有一大块市场看不见且常为负 ⇒ 定价偏低 | oci_pen | **已验证★**（SF3.72/tS1.49/平台corr0.5447/id 3qVkVR8X） |
| E1102 | `group_rank(current_minimum_operating_lease_payment/assets, subindustry)` | 当期应付经营租赁款/资产 = **表外杠杆当期强度**。租店经营（零售/餐饮/航空）真实负债不在表内，市场定价不足 | lease_cur | 已验证（SF3.29/tS0.18/平台corr0.7083） |
| E1103 | `group_rank(future_minimum_operating_lease_payments/assets, subindustry)` | 未来经营租赁最小付款/资产 = 表外杠杆的**久期视角** | lease_fut | 新造 |
| E1104 | `group_rank(sbp_equity_nonvested_count/fn_entity_common_stock_shares_out_a, subindustry)` | 未归属股权激励/总股本 = **表外稀释 + 管理层过度自信代理**（Cooper/Gulen/Schill：过度自信者高估成长低估风险⇒后续跑输） | sbp_dil | 已验证（SF2.47/tS0.67/平台corr0.7273） |
| E1105 | `group_rank(option_award_outstanding_count/fn_entity_common_stock_shares_out_a, subindustry)` | 未行权期权/总股本 = 潜在稀释的另一口径 | opt_dil | 新造（SF2.27 带 FAIL） |
| E1106 | `group_rank(debt_issuance_proceeds_2/assets, subindustry)` | 债务发行所得/资产 = **再融资节奏**，发行高峰期资本压力与扩张意图同时上升 | dbt_issue | 已验证（SF2.54/tS0.51） |
| E1107 | `group_rank(-(debt_repayments_total + line_of_credit_repayments)/assets, subindustry)` | 偿还总额/资产 = 债务到期压力（正相反方向） | dbt_repay | 新造 |
| **E1108**（禁用） | ~~`group_rank(income_taxes_paid_total/income_tax_expense_total, ...)`~~ | 实缴税/税费用、递延税资产/负债、有效税率差 | tax_* | **1010 判死**：cov≥0.7 下 SF 仅 0.65~1.96，tax_cash/tax_dtl/tax_eff/tax_dta/compr_tax/compr_val 六个全带 LOW_SHARPE+LOW_FITNESS。会计口径差异在美国市场无定价。见 atoms.md D-30 |

**使用边界（1010 实测，踩坑记录）**：
1. **只用 cov≥0.7 的字段**（cov 0.6 那批信号太钝，见 D-30 原始判死依据）。
2. 有效四信号里**只有 E1101 同时达标 SF≥4.2 的底子与 tS≥1.3**，
   E1102/E1104 的 tS 只有 0.18/0.67（样本外不稳）⇒ **只能当差异化配腿，不能单独做主腿**。
3. 反过来 E1101（tS 1.49）适合做主腿，用 E1102/E1104/E1106 做配腿提 SF——
   这三者的 corr 都在 0.71~0.75，与 E1101 的 0.5447 差0.16~0.20，**叠加不会把 corr 推过0.70**。

## 2.5 1011 新增机制原子（idea_generator.py M12~M15，字段全部实测存在于平台全量清单）

> 选取口径：`all_fields_usa_top3000.json` 里 **cov≥0.75 + 台账从未使用 + userCount 低** 的 MATRIX 字段；
> 构造统一用 10-10 实证有效的 `group_rank(ts_rank(x, 88), <轴>)`（把慢速基本面比率做成时序位置，避开池内横截面比例扎堆）。

### M12 表外契约义务与股权稀释（fundamental2 契约类明细）

**机制**：租赁付款计划/股权激励费用/未行权期权行权价是"契约性的未来流出"，不进利润表主流口径、
分析师模型常不覆盖 ⇒ 定价不充分。与 M04 质量溢价的区别：M04 看盈利能力，这里看**未来被占用的现金与股本**。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1201 | `group_rank(ts_rank(operating_lease_minimum_payments_due_five_years/assets, 88), subindustry)` | 五年租赁最小付款/资产 = 契约杠杆久期（uc=14 cov=0.79） | lease_dur | 新造★ |
| E1202 | `group_rank(ts_rank(operating_leases_min_payments_3y/assets, 88), industry)` | 三年租赁最小付款/资产（uc=18 cov=0.82） | lease_3y | 新造★ |
| E1203 | `group_rank(ts_rank(share_award_expense_total/assets, 88), subindustry)` | 股权激励费用/资产 = 隐性稀释成本（uc=13 cov=0.80） | sbc_dil | 新造★ |
| E1204 | `group_rank(ts_rank(options_outstanding_avg_exercise_price/close - 1, 88), industry)` | 未行权期权平均行权价相对现价 = 激励对齐度（uc=12 cov=0.75） | opt_moneyness | 新造★ |

### M13 管理层指引区间（analyst4 guidance 无人区，uc=1~18、cov=1.00）

**机制**：指引是管理层对未来的自我承诺；区间宽度=管理层自身不确定度，下限=保守锚，
上限/现价=市场对该承诺的定价折度。第三方分析师跟随滞后 ⇒ 反应不足。
（与 E504~E507 的区别：那批用 `epsr` 指标，本批换 **ebitda / cfi** 指标并统一做时序化构造）

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1301 | `group_rank(ts_rank((anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance - anl4_fs_guidances_advanced_af_nd_ebitda_minguidance)/abs(anl4_fs_guidances_advanced_af_nd_ebitda_minguidance), 88), subindustry)` | EBITDA 指引区间相对宽度 = 管理层不确定度 | guid_width_ebitda | 新造★ |
| E1302 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_ebitda_maxguidance/close, 88), industry)` | EBITDA 指引上限/现价 = 管理层口径的隐含收益率 | guid_yield | 新造★ |
| E1303 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_cfi_minguidance/assets, 88), subindustry)` | 投资现金流指引下限/资产 = 资本开支保守度 | guid_capex_floor | 新造★ |
| E1304 | `group_rank(ts_rank(anl4_fs_guidances_advanced_af_nd_epsr_minguidance/anl4_fs_guidances_advanced_af_nd_epsr_maxguidance, 88), industry)` | EPS 指引下/上限比 = 指引不对称 | guid_skew | 新造★ |

### M13.1（10-13 扩）管理层指引**区间宽度族**：腿全部取 analyst4 冷字段，不带任何池内老腿

**为什么开这一格**（三条实测）：① D-73 判死的是「单个冷字段 × 一阶单层」，同型本轮读数 nf27/nh27/f177 最高 S 仅 0.81/0.57/0.91；
② 已过 S≥1.78 的 249 条 guidance 件（bt2/bt14/bt15/dq）**每条都配了池内老腿**（`liabilities_curr/assets` 等），
本地 cmax 已算的 34 条最小 0.7187 ⇒ 高分是靠老腿借来的，相关性也是；
③ 「多腿且腿全部来自 analyst4 冷字段」这个格子从没跑过。字段口径：cov≥0.95 + 我方从未用过 + 平台拥挤度≤全站 P50
（最冷的一对 max/min 全站只有 1~3 个 alpha、1~3 个人在用）。

**机制**：`(max − min)/|min|` = 管理层自我不确定度（分歧越大未来越易证伪，做多确定性）；
`max/median` = 指引不对称（乐观偏度）；`ts_delta(estimate)` = 分析师跟随后上调/下调。

| idea_id | 表达式骨架 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1305 | `group_rank(-ts_mean((max-min)/abs(min), 22), subindustry) + group_rank(ts_mean((max-min)/abs(min), 22), subindustry)` | 两指标区间宽度对照（反号×正号） | guid_width_pair | 待跑 g53 |
| E1306 | `group_rank(-ts_mean((max-min)/abs(min), 66), industry) ×2` | 长窗宽度，INDUSTRY 分组 | guid_width_66 | 待跑 g53 |
| E1307 | `1.2*宽度A(sub) + 宽度B(ind) + 0.8*宽度C(sub)` | 三指标宽度加权 | guid_width_trio | 待跑 g53 |
| E1308 | `宽度(sub) + group_rank(ts_mean(high/low, 22), sub)` | 宽度 × 指引不对称 | guid_width_skew | 待跑 g53 |
| E1309 | `宽度(sub) + group_rank(ts_delta(<median 预期>, 60), sub)` | 宽度 × 预期修正方向 | guid_width_rev | 待跑 g53 |

### M14 期权隐含风险的期限结构（option8，★刻意绕开 skew 腿）

**机制**：长期 IV / 短期 IV = 不确定性是暂时事件冲击还是持久状态。斜率高 = 风险被定价在近端（事件型），
事件过后回归；斜率低 = 结构性风险、长期被压制。
**为什么选它**：atoms.md M-14 判定 option8 里 `skew` 腿既是 tS 之源也是 corr 之源（含 skew 的结构一律撞 0.93~0.98），
而"去 skew 的替代 tS 源 = IV 期限斜率"是当日明列的**未试轴**。期限斜率用的是同侧不同到期日，与 moneyness skew 不同维度。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1401 | `group_rank(ts_rank(implied_volatility_mean_360/implied_volatility_mean_60 - 1, 88), industry)` | IV 期限斜率（均值口径） | iv_term | 新造★ |
| E1402 | `group_rank(ts_rank(implied_volatility_call_360/implied_volatility_call_60 - 1, 88), subindustry)` | 看涨侧期限斜率 | iv_term_call | 新造★ |
| E1403 | `group_rank(ts_rank(implied_volatility_put_360/implied_volatility_put_60 - 1, 88), market)` | 看跌侧期限斜率（下行保护成本久期） | iv_term_put | 新造★ |
| E1404 | `group_rank(ts_rank(implied_volatility_mean_1080/implied_volatility_mean_30 - 1, 88), industry)` | 超长/超短斜率 | iv_term_long | 新造★ |

### M15 商业关系图谱位置（pv13 客户/竞争关系网络）

**机制**：枢纽节点信息暴露充分、冲击传导快；边缘节点传导慢 ⇒ 收益补偿差异；
竞争者相对数量衡量竞争强度对超额收益持续性的侵蚀。

| idea_id | 表达式 | 经济含义 | 标签 | 状态 |
|---|---|---|---|---|
| E1501 | `group_rank(ts_rank(pv13_ustomergraphrank_hub_rank, 88), industry)` | 客户图谱枢纽度（uc=858 cov=0.79） | cust_hub | 新造★ |
| E1502 | `group_rank(ts_rank(pv13_revere_index_value, 88), subindustry)` | 供应链暴露指数（uc=505 cov=0.86） | sc_expose | 新造★ |
| E1503 | `group_rank(ts_rank(rel_num_comp, 88), industry)` | 竞争对手相对数量 = 竞争强度（uc=1613 cov=0.89） | comp_intens | 新造★ |
| E1504 | `group_rank(ts_rank(pv13_com_page_rank, 88), market)` | 公司图谱 PageRank = 网络中心度（uc=1685 cov=0.91） | cust_pagerank | 新造★ |

**使用边界（1011 先验，避免重复踩坑）**
1. 单腿裸信号预计 S≤1.9（10-10 处女字段天花板），**必须 3 腿以上合成才可能过 S+F≥4.2**；
   合成时一条老配腿都不能带（10-10 嫁接批教训：混入 cfo 老腿 → corr 残留 0.71）。
2. `option8` 的 skew 字段（`implied_volatility_mean_skew_*`）**不入本批**——D-21 已实证含 skew 结构全撞 6XKr8wG 家族。
3. `model16/model51` 字段群只能当佐腿（权重≤0.6），主腿判死（D-38）。

## 3. 组合登记簿（每个跑过的组合必须在此登记）

> 生成器：`src/knowledge/combo_gen.py`（两两 / 三三）·台账：`_autologs/combo_ledger.json`（机器可读，回写以它为准）

登记字段：combo_id / 组成 idea_id / 组合层级 / 生成批次 / SF / tS / TO / corr / 平台判决 / 状态

状态取值：**未使用** · **已跑** · **过线** · **已入池** · **可复活**（撞 corr 但 idea 保留，换轴/换腿/换池再出） · **判死**（同组合两次以上结构性失败）

| combo_id | 组成 idea_id | 层级 | 批次 | SF | tS | TO | corr | 平台判决 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| C000cd536 | F001+T009 | 2 | p2a | — | — | — | — | — | 已跑 |
| C06a77936 | F001+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C032bd817 | F002+F003 | 2 | p2a | — | — | — | — | — | 已跑 |
| C034abb13 | F002+T008 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01c68e8f | F003+T007 | 2 | p2a | — | — | — | — | — | 已跑 |
| C007577d7 | F003+T012 | 2 | p2a | — | — | — | — | — | 已跑 |
| C013ae751 | F004+T032 | 2 | p2a | — | — | — | — | — | 已跑 |
| C02bdbab0 | F004+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C057bac97 | F005+F011 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0646d62e | F005+T011 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0603e8fa | F006+T021 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0198f624 | F006+T023 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01a13231 | F007+T007 | 2 | p2a | — | — | — | — | — | 已跑 |
| C02b94a6e | F007+T035 | 2 | p2a | — | — | — | — | — | 已跑 |
| C051ddf47 | F008+T032 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01ba0f39 | F008+T049 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01a3e0eb | F009+F021 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03a6a258 | F009+T050 | 2 | p2a | — | — | — | — | — | 已跑 |
| C00cbc1f7 | F010+T029 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09830a6e | F010+T048 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07a718e3 | F011+T006 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03b12c44 | F011+T037 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01626b62 | F012+F013 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0b569c7f | F012+T051 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0b01ec3c | F013+F025 | 2 | p2a | — | — | — | — | — | 已跑 |
| C068799b1 | F013+T018 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0211ddaf | F014+F016 | 2 | p2a | — | — | — | — | — | 已跑 |
| C019aa5a1 | F014+T049 | 2 | p2a | — | — | — | — | — | 已跑 |
| C08d62e69 | F015+T050 | 2 | p2a | — | — | — | — | — | 已跑 |
| C021ca4ba | F015+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0cb18f5b | F016+T040 | 2 | p2a | — | — | — | — | — | 已跑 |
| C04e89657 | F016+T041 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0b910227 | F017+T036 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0be61eb1 | F017+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0779b05a | F018+F019 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03226e2e | F018+F024 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0155f639 | F019+T004 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09b33dc0 | F019+T051 | 2 | p2a | — | — | — | — | — | 已跑 |
| C070eddf4 | F020+T005 | 2 | p2a | — | — | — | — | — | 已跑 |
| C06c00b98 | F020+T047 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0cd8770b | F021+T003 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01eb4756 | F021+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09865fe4 | F022+T004 | 2 | p2a | — | — | — | — | — | 已跑 |
| C153778d8 | F022+T017 | 2 | p2a | — | — | — | — | — | 已跑 |
| C052f4485 | F023+T010 | 2 | p2a | — | — | — | — | — | 已跑 |
| C08c8e234 | F023+T017 | 2 | p2a | — | — | — | — | — | 已跑 |
| C006a9fd9 | F024+T021 | 2 | p2a | — | — | — | — | — | 已跑 |
| C04bc989e | F024+T049 | 2 | p2a | — | — | — | — | — | 已跑 |
| C08f37fa7 | F025+T029 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0070bea3 | F025+T035 | 2 | p2a | — | — | — | — | — | 已跑 |
| C030e6bc1 | T001+T010 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0bba0d94 | T001+T017 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09b6be00 | T002+T015 | 2 | p2a | — | — | — | — | — | 已跑 |
| C040cf221 | T002+T027 | 2 | p2a | — | — | — | — | — | 已跑 |
| C04ebb05d | T003+T004 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0838e25d | T003+T034 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0bd29bf7 | T004+T016 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09c75617 | T004+T036 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03660645 | T005+T031 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0904ada3 | T005+T039 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0e668d65 | T006+T038 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07479ed2 | T006+T051 | 2 | p2a | — | — | — | — | — | 已跑 |
| C05018ee9 | T007+T043 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0f814048 | T007+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03d96be3 | T008+T034 | 2 | p2a | — | — | — | — | — | 已跑 |
| C064c041a | T008+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C082533eb | T009+T015 | 2 | p2a | — | — | — | — | — | 已跑 |
| C022b150d | T009+T032 | 2 | p2a | — | — | — | — | — | 已跑 |
| C19dc3f6c | T010+T028 | 2 | p2a | — | — | — | — | — | 已跑 |
| C02ab3df2 | T010+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C04e597c0 | T011+T045 | 2 | p2a | — | — | — | — | — | 已跑 |
| C11652fa3 | T011+T046 | 2 | p2a | — | — | — | — | — | 已跑 |
| C09b93a07 | T012+T029 | 2 | p2a | — | — | — | — | — | 已跑 |
| C017ce473 | T012+T031 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0027bb74 | T013+T016 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0384831b | T013+T047 | 2 | p2a | — | — | — | — | — | 已跑 |
| C133b7878 | T014+T046 | 2 | p2a | — | — | — | — | — | 已跑 |
| C10bf0165 | T014+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| C06f4a4e4 | T015+T047 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07d429dd | T015+T051 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0b228a3e | T016+T021 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0e514f07 | T016+T023 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0acf09e8 | T017+T040 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0b9deeba | T017+T044 | 2 | p2a | — | — | — | — | — | 已跑 |
| C068affba | T018+T030 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0140e23c | T018+T037 | 2 | p2a | — | — | — | — | — | 已跑 |
| C044d56d0 | T019+T028 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0a24d615 | T020+T040 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07aa2a8b | T021+T045 | 2 | p2a | — | — | — | — | — | 已跑 |
| C005171b4 | T022+T034 | 2 | p2a | — | — | — | — | — | 已跑 |
| C1a743750 | T023+T039 | 2 | p2a | — | — | — | — | — | 已跑 |
| C00fa8b5a | T024+T037 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0808c83b | T025+T043 | 2 | p2a | — | — | — | — | — | 已跑 |
| C03c883ae | T026+T047 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0008b516 | T027+T038 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07d63270 | T028+T044 | 2 | p2a | — | — | — | — | — | 已跑 |
| C1a90bfb7 | T029+T043 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0dd665a5 | T030+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0079ff0d | T031+T035 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0474e339 | T032+T041 | 2 | p2a | — | — | — | — | — | 已跑 |
| C273e850f | T033+T042 | 2 | p2a | — | — | — | — | — | 已跑 |
| C00908a00 | T034+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01802b61 | T035+T045 | 2 | p2a | — | — | — | — | — | 已跑 |
| C2351d75a | T036+T042 | 2 | p2a | — | — | — | — | — | 已跑 |
| C13bf28b6 | T037+T042 | 2 | p2a | — | — | — | — | — | 已跑 |
| C14ba801e | T038+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C14d7a021 | T039+T043 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01b5d11c | T040+T048 | 2 | p2a | — | — | — | — | — | 已跑 |
| C07535650 | T041+T043 | 2 | p2a | — | — | — | — | — | 已跑 |
| C0ccd309e | T042+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C01c6a4be | T043+T048 | 2 | p2a | — | — | — | — | — | 已跑 |
| C42a31ad1 | T044+T046 | 2 | p2a | — | — | — | — | — | 已跑 |
| C24e8414b | T045+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C2a330be7 | T046+T049 | 2 | p2a | — | — | — | — | — | 已跑 |
| C316d0fbb | T047+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| C5fb4ad5d | T048+T050 | 2 | p2a | — | — | — | — | — | 已跑 |
| C30da3587 | T049+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| C05c6c23b | T050+T051 | 2 | p2a | — | — | — | — | — | 已跑 |
| C367d7061 | T051+T052 | 2 | p2a | — | — | — | — | — | 已跑 |
| Cd57f4eb2 | T052+T053 | 2 | p2a | — | — | — | — | — | 已跑 |
| C39a79263 | E1302+E1401+E1203 | 3 | n15_1011 | -0.37 | -1.65 | 0.070 | — | 判死（S≤1.0，D-43） | 判死 |
| C42bab286 | E1302+E1502+E1401 | 3 | n15_1011 | -0.17 | -1.24 | 0.061 | — | 判死（S≤1.0，D-43） | 判死 |
| Ccf7435b5 | E1201+E1304+E1501 | 3 | n15_1011 | 1.61 | 0.64 | 0.038 | — | 判死（S≤1.0，D-43） | 判死 |
| Cf83f0cfc | E1203+E1402+E1303 | 3 | n15_1011 | 1.40 | -0.09 | 0.051 | — | 判死（S≤1.0，D-43） | 判死 |
| C4fef981e | E1401+E1301+E1503 | 3 | n15_1011 | 0.93 | 0.10 | 0.090 | — | 判死（S≤1.0，D-43） | 判死 |
| C8ebb6229 | E1501+E1302+E1201 | 3 | n15_1011 | 0.97 | -0.18 | 0.048 | — | 判死（S≤1.0，D-43） | 判死 |
| Cd857f696 | E1502+E1403+E1304 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |
| Ca687c018 | E1303+E1204+E1504 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |
| C7e735369 | E1402+E1503+E1301 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |
| C179f89ee | E1204+E1303+E1404 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |
| C9b9437db | E1504+E1401+E1201 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |
| Cc987cde0 | E1304+E1202+E1502 | 3 | n15_1011 | — | — | — | — | 未跑（批被中止） | 未使用 |

| L1ca1eaa5 | 见 expr | 3 | bl19_1011 | 4.05 | 1.35 | 0.163 | — | S<=1.0 或 FAIL | 判死 |
| Lbf99307c | 见 expr | 3 | bl19_1011 | 6.71 | 2.67 | 0.147 | — | 未判 | 已跑 |
| L9e9c27c5 | 见 expr | 3 | bl19_1011 | 3.97 | 1.28 | 0.125 | — | 未判 | 已跑 |
| L751f3088 | 见 expr | 3 | bl19_1011 | 6.71 | 2.67 | 0.147 | — | 未判 | 已跑 |
| La3f97548 | 见 expr | 3 | bl19_1011 | 4.03 | 1.39 | 0.073 | — | 未判 | 已跑 |
| Lca40da52 | 见 expr | 3 | bl19_1011 | 5.96 | 1.89 | 0.086 | — | 未判 | 已跑 |
| Lb6a87f9b | 见 expr | 3 | bl19_1011 | 2.91 | 1.89 | 0.099 | — | S<=1.0 或 FAIL | 判死 |
| Lc61d3848 | 见 expr | 3 | g17_1011 | 3.1 | 0.60 | 0.138 | — | 未判 | 已跑 |
| Lf759cdc8 | 见 expr | 3 | g17_1011 | 3.31 | 1.65 | 0.117 | — | 未判 | 已跑 |
| L77377b16 | 见 expr | 3 | g17_1011 | 3.59 | 2.77 | 0.143 | — | S<=1.0 或 FAIL | 判死 |
| L10114d34 | 见 expr | 3 | g17_1011 | 3.15 | 0.80 | 0.112 | — | 未判 | 已跑 |
| L657fb594 | 见 expr | 3 | g17_1011 | 3.52 | 1.78 | 0.075 | — | 未判 | 已跑 |
| L37a8f014 | 见 expr | 3 | lc19_1011 | 3.45 | 0.70 | 0.153 | 0.6191 | GATE-FAIL | 已跑 |
| L164aef9e | 见 expr | 3 | lc19_1011 | 2.5 | -0.48 | 0.132 | 0.5037 | GATE-FAIL | 已跑 |
| Lfe39b93e | 见 expr | 3 | lc19_1011 | 2.41 | 0.30 | 0.164 | 0.7033 | GATE-FAIL | 已跑 |
| L978da6e7 | 见 expr | 3 | lc19_1011 | 4.51 | 3.12 | 0.347 | 0.9571 | GATE-FAIL | 已跑 |
| Lbd77404f | N_tr5+M_intc+K_page | 3 | lc19b_1011 | 4.18 | 2.57 | 0.190 | 0.7480 | GATE-FAIL | 已跑 |
| L564cd3dd | N_tr5+M_intc+K_page | 3 | lc19b_1011 | 4.05 | 2.70 | 0.229 | 0.7298 | GATE-FAIL | 已跑 |
| L118e8aaa | N_tr5+M_intc+K_impact | 3 | lc19b_1011 | 4.72 | 2.77 | 0.210 | 0.9994 | GATE-FAIL | 已跑 |
| Ldbc08492 | N_tr5+M_intc+K_impact | 3 | lc19b_1011 | 4.91 | 2.32 | 0.128 | 0.9835 | BLOCK | 可复活 |
| Lf038d3ba | 见 expr | 3 | lc19d_1011 | 4.91 | 2.32 | 0.128 | 0.9835 | BLOCK | 可复活 |
| L6d973020 | 见 expr | 3 | lc19d_1011 | 4.75 | 2.15 | 0.098 | 0.9641 | BLOCK | 可复活 |
| L99122bf4 | 见 expr | 3 | lc19d_1011 | 4.88 | 2.14 | 0.106 | 0.9726 | GATE-FAIL | 已跑 |
| L7869c3b9 | 见 expr | 3 | lc19d_1011 | 4.84 | 2.21 | 0.123 | 0.9812 | BLOCK | 可复活 |
| Ld3aae4c6 | N_tr5+M_cov+M_cfoQ | 3 | lc19e_1011 | 3.1 | 0.87 | 0.147 | 0.8012 | GATE-FAIL | 已跑 |
| Lfc0b6f53 | N_tr5+M_intc+K_impact | 3 | lc19f_1011 | 4.72 | 2.77 | 0.210 | 0.9994 | GATE-FAIL | 已跑 |
| L4ed28edf | N_tr5+M_intc+K_impact | 3 | lc19f_1011 | 4.74 | 2.73 | 0.196 | 1.0000 | ACCEPTED | 已入池 |
| Lb6b5591e | N_tr5+M_intc+K_impact | 3 | lc19f_1011 | 4.74 | 2.73 | 0.196 | 1.0000 | BLOCK | 可复活 |
| L4cd8558d | N_tr5+M_intc+K_impact | 3 | lc19f_1011 | 4.76 | 2.64 | 0.179 | 0.9990 | BLOCK | 可复活 |
| Le81b1905 | K_impact+Q_cfoV+Q_accR | 3 | lc19g_1011 | 4.6 | 0.49 | 0.126 | 0.5965 | GATE-FAIL | 已跑 |
| L9526cdd2 | N_tr5+K_page+Q_pstI | 3 | lc19m_1011 | 3.24 | 2.67 | 0.280 | 0.7231 | GATE-FAIL | 已跑 |
| L65e0b407 | N_tr5+L_txt+P_am20 | 3 | lc19m_1011 | 4.02 | 1.87 | 0.271 | 0.7641 | GATE-FAIL | 已跑 |
| L4e6e82d1 | N_tr5+M_cov+M_tstk | 3 | lc19m_1011 | 3.63 | 2.34 | 0.200 | 0.6544 | GATE-FAIL | 已跑 |
| L470c056b | N_tr5+M_txp+Q_accR | 3 | lc19m_1011 | 2.76 | 1.59 | 0.240 | 0.6743 | GATE-FAIL | 已跑 |
| L5ac100bd | N_tr5+P_am20+M_cov | 3 | lc19m_1011 | 3.68 | 2.05 | 0.231 | 0.7741 | GATE-FAIL | 已跑 |
| Ld2b67eb5 | N_tr5+L_cash+M_intc | 3 | lc19x_1011 | 4.5 | 2.05 | 0.171 | 0.7579 | GATE-FAIL | 已跑 |
| L08a6c5d7 | N_tr5+L_cash+M_opex | 3 | lc19x_1011 | 4.0 | 2.43 | 0.118 | — | 未判 | 已跑 |
| Ld417e316 | N_tr5+L_cfo+N_am60 | 3 | lc19x_1011 | 4.6 | 2.19 | 0.211 | 0.7938 | GATE-FAIL | 已跑 |
| L6cb09132 | N_tr5+L_cfo+P_am20 | 3 | lc19x_1011 | 4.66 | 2.07 | 0.212 | 0.7905 | GATE-FAIL | 已跑 |
| Lf648dfdd | N_tr5+M_cov+Q_accR | 3 | lc19x_1011 | 3.37 | 1.32 | 0.196 | 0.6028 | GATE-FAIL | 已跑 |
| L7672cca8 | N_tr5+M_intc+M_revt | 3 | lc19x_1011 | 3.94 | 2.40 | 0.204 | 0.7962 | GATE-FAIL | 已跑 |
| L63ba41cf | N_tr5+M_opex+K_page | 3 | lc19x_1011 | 4.49 | 3.45 | 0.126 | 0.6957 | BLOCK | 可复活 |
| L9402ab0c | N_tr5+N_am60+Q_cfoV | 3 | lc19x_1011 | 4.55 | 1.66 | 0.190 | 0.7711 | BLOCK | 可复活 |
| L09443c60 | N_tr5+P_am20+Q_cfoC | 3 | lc19x_1011 | 4.37 | 1.46 | 0.190 | 0.7889 | BLOCK | 可复活 |
| L08b093cc | N_tr5+P_am20+Q_cfoV | 3 | lc19x_1011 | 4.63 | 1.55 | 0.191 | 0.7687 | BLOCK | 可复活 |
| L638aff7d | N_tr5+L_cash+M_intc | 3 | lc19y_1011 | 4.7 | 1.96 | 0.139 | 0.7874 | GATE-FAIL | 已跑 |
| La37e8175 | N_tr5+L_cash+M_intc | 3 | lc19y_1011 | 4.78 | 2.20 | 0.153 | 0.7796 | GATE-FAIL | 已跑 |
| Lbf02f2ca | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 3.56 | 2.66 | 0.152 | 0.7121 | GATE-FAIL | 已跑 |
| L3b4ef745 | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 3.95 | 3.31 | 0.194 | 0.7063 | GATE-FAIL | 已跑 |
| Ld2b7add9 | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 3.95 | 3.00 | 0.135 | 0.7162 | GATE-FAIL | 已跑 |
| L86ec467d | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 4.16 | 3.17 | 0.116 | 0.7220 | GATE-FAIL | 已跑 |
| Lde5def4c | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 3.32 | 2.43 | 0.159 | 0.7202 | GATE-FAIL | 已跑 |
| Lcd35bbf3 | N_tr5+M_opex+K_page | 3 | lc19y_1011 | 3.53 | 2.59 | 0.149 | — | 未判 | 已跑 |
| L1ea22dc2 | 见 expr | 3 | bl19_1011 | 0 | — | 0.000 | — | S<=1.0 或 FAIL | 判死 |
| L398a4307 | 见 expr | 3 | bl19_1011 | 0 | — | 0.000 | — | S<=1.0 或 FAIL | 判死 |
| L62504f03 | 见 expr | 3 | bl19_1011 | 0 | — | 0.000 | — | S<=1.0 或 FAIL | 判死 |
| Lb6ec2af8 | 见 expr | 3 | bl19_1011 | 0 | — | 0.000 | — | S<=1.0 或 FAIL | 判死 |
| Le4f7d97a | 见 expr | 3 | bl19_1011 | 0 | — | 0.000 | — | S<=1.0 或 FAIL | 判死 |
| Lf8e2350e | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z15_1011 | 4.58 | 0.35 | 0.096 | 0.5972 | GATE-FAIL | 已跑 |
| Lae09084a | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z15_1011 | 4.75 | 0.40 | 0.112 | 0.5877 | GATE-FAIL | 已跑 |
| L160f5982 | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z15_1011 | 4.7 | 0.65 | 0.141 | 0.6466 | GATE-FAIL | 已跑 |
| L0ebdc9f0 | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z15_1011 | 4.7 | 0.35 | 0.150 | 0.5435 | GATE-FAIL | 已跑 |
| L38c33d99 | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z20_1011 | 4.83 | 0.41 | 0.105 | 0.5845 | GATE-FAIL | 已跑 |
| L5e53704c | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z20_1011 | 4.52 | 0.30 | 0.080 | 0.6048 | GATE-FAIL | 已跑 |
| Lf952c35c | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z20_1011 | 4.32 | 0.38 | 0.067 | 0.6708 | GATE-FAIL | 已跑 |
| Lf41f1bd2 | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z25_1011 | 4.47 | 0.23 | 0.070 | 0.6113 | GATE-FAIL | 已跑 |
| L32642c9c | K_impact+Q_cfoV_bkt+Q_accR_rk | 3 | lc19z25_1011 | 4.51 | 0.43 | 0.074 | 0.6728 | GATE-FAIL | 已跑 |

| Lae3ff8f8 | M_opex+P_c2+K_page | 3 | lc20m_1011 | 5.06 | 3.38 | 0.093 | 0.7373 | BLOCK | 可复活 |
| Lbe2a2adf | N_tr5+L_cash+M_accI | 3 | lc20m_1011 | 4.32 | 2.23 | 0.164 | 0.7104 | BLOCK | 可复活 |
| Le8cc858f | N_tr5+M_cfoQ+Q_xrI | 3 | lc20m_1011 | 3.97 | 0.90 | 0.149 | 0.8090 | GATE-FAIL | 已跑 |
| Lb48d04dc | N_tr5+M_intc+Q_accS | 3 | lc20m_1011 | 4.95 | 2.64 | 0.168 | 0.8041 | BLOCK | 可复活 |
| Lf4ad9021 | N_tr5+N_am60+Q_xrV | 3 | lc20m_1011 | 4.46 | 1.66 | 0.181 | 0.7897 | BLOCK | 可复活 |
| L1753c4f4 | N_tr5+P_am20+L_xr | 3 | lc20m_1011 | 5.52 | 1.57 | 0.154 | 0.8350 | BLOCK | 可复活 |
| L7c419b14 | N_tr5+Q_accR+M_cov | 3 | lc20m_1011 | 3.61 | 1.23 | 0.168 | 0.7032 | GATE-FAIL | 已跑 |
| L5c89c197 | N_tr5+Q_cfoQ+Q_xrS | 3 | lc20m_1011 | 4.03 | 0.97 | 0.168 | 0.7812 | GATE-FAIL | 已跑 |
| L7217b184 | N_tr60+K_page+Q_accS | 3 | lc20m_1011 | 4.47 | 2.63 | 0.179 | 0.7316 | BLOCK | 可复活 |
| L8e68ad21 | N_tr60+M_intc+Q_accC | 3 | lc20m_1011 | 5.3 | 2.64 | 0.181 | 0.9040 | BLOCK | 可复活 |
| L5baffdc9 | P_c2+M_revt+N_am60 | 3 | lc20m_1011 | 4.68 | 2.38 | 0.162 | 0.9174 | BLOCK | 可复活 |
| L3593fb90 | P_int20+K_page+L_xr | 3 | lc20m_1011 | 4.79 | 2.33 | 0.215 | 0.7763 | GATE-FAIL | 已跑 |
| L51a1a9ce | P_int20+M_intc+Q_accL | 3 | lc20m_1011 | 5.0 | 2.62 | 0.180 | 0.9309 | GATE-FAIL | 已跑 |
| Lc1166b91 | P_int20+P_am20+Q_xrI | 3 | lc20m_1011 | 4.91 | 1.86 | 0.215 | 0.8242 | GATE-FAIL | 已跑 |
| L7c838729 | P_int20+Q_cfoQ+Q_accC | 3 | lc20m_1011 | 3.7 | 1.34 | 0.156 | 0.8181 | GATE-FAIL | 已跑 |
| L88c7f765 | P_tr20+K_auth+Q_xrS | 3 | lc20m_1011 | 4.89 | 2.10 | 0.269 | 0.8055 | GATE-FAIL | 已跑 |
| L82c1d90c | P_tr20+K_page+Q_xrI | 3 | lc20m_1011 | 5.13 | 2.12 | 0.184 | 0.8179 | BLOCK | 可复活 |
| Lfecc3d36 | P_tr20+L_aol+M_accI | 3 | lc20m_1011 | 4.49 | 2.23 | 0.147 | 0.9095 | BLOCK | 可复活 |
| Le915b855 | P_tr20+M_cfoQ+Q_accC | 3 | lc20m_1011 | 3.86 | 1.30 | 0.156 | 0.8212 | GATE-FAIL | 已跑 |
| Lec99cba1 | P_tr20+M_revt+Q_accI | 3 | lc20m_1011 | 4.28 | 2.36 | 0.169 | 0.8031 | BLOCK | 可复活 |
| Lc395ff0a | P_tr20+M_tstk+K_accI | 3 | lc20m_1011 | 4.48 | 2.19 | 0.182 | 0.7653 | BLOCK | 可复活 |
| La08c1979 | P_tr20+N_am60+L_xr | 3 | lc20m_1011 | 5.73 | 1.75 | 0.164 | 0.8409 | BLOCK | 可复活 |
| L63d0d969 | P_tr20+P_am20+Q_accL | 3 | lc20m_1011 | 4.73 | 2.00 | 0.155 | 0.8200 | BLOCK | 可复活 |
| Lf3706376 | P_tr20+P_c20+Q_xrV | 3 | lc20m_1011 | 4.6 | 2.26 | 0.242 | 0.7532 | GATE-FAIL | 已跑 |
| Le684b88a | P_tr20+Q_accR+M_intc | 3 | lc20m_1011 | 4.49 | 1.60 | 0.224 | 0.8384 | GATE-FAIL | 已跑 |
| Lf8a65543 | P_tr20+Q_cfoQ+Q_accS | 3 | lc20m_1011 | 3.89 | 1.27 | 0.155 | 0.8216 | GATE-FAIL | 已跑 |
| Laa8f3212 | N_tr5+M_intc+Q_accS | 3 | lc20n_1011 | 1.77 | 2.16 | 0.178 | — | S<=1.0 或 FAIL | 判死 |
| L66f4e65b | N_tr60+M_intc+Q_accC | 3 | lc20n_1011 | 2.05 | 1.40 | 0.211 | — | S<=1.0 或 FAIL | 判死 |
| L98ebce1d | P_tr20+N_am60+L_xr | 3 | lc20n_1011 | 2.16 | 0.61 | 0.169 | — | S<=1.0 或 FAIL | 判死 |
| Lf70749fd | P_tr20+P_am20+L_xr | 3 | lc20n_1011 | 2.25 | 0.80 | 0.170 | — | S<=1.0 或 FAIL | 判死 |
| Ld77ccddc | M_opex+P_c2+K_page | 3 | lc20n_1011 | 2.59 | 2.06 | 0.106 | — | SF<4.0 闸门不过 | 判死 |
| L780a5035 | N_tr60+K_page+Q_accS | 3 | lc20n_1011 | 1.33 | 0.62 | 0.205 | — | S<=1.0 或 FAIL | 判死 |
| Lcffc1af1 | P_int20+M_intc+Q_accL | 3 | lc20n_1011 | 1.54 | 1.53 | 0.209 | — | S<=1.0 或 FAIL | 判死 |
| Lbc501e5c | P_tr20+P_am20+Q_accL | 3 | lc20n_1011 | 1.71 | 1.04 | 0.167 | — | S<=1.0 或 FAIL | 判死 |

统计：已跑 227（1011 腿库线 58 条 + lc19z 9 条 + lc20m 26 条 + lc20n T500 8 条并入 + g19 SECTOR 手术 6 条）

| Lb55bd49b | KPrMxl2g | 3 | g19_1011 | 4.42 | 1.88 | 0.053 | 0.8013 | BLOCK | 判死 |
| Ldd577763 | P0gbl1YJ | 3 | g19_1011 | 5.66 | 2.50 | 0.087 | 0.7217 | 重复消耗 | 重复 |
| Lc5b5509f | ZYAvkE1x | 3 | g19_1011 | 5.07 | 1.43 | 0.082 | 0.8213 | BLOCK | 判死 |
| L2a6322a8 | d516nL1K | 3 | g19_1011 | 4.21 | 1.43 | 0.051 | 0.7338 | 重复消耗 | 重复 |
| L345ac027 | xAbpMp9m | 3 | g19_1011 | 3.78 | 2.36 | 0.041 | 0.7393 | GATE-FAIL | 判死 |
| L2aa15ffd | JjQJlJXj | 3 | g19_1011 | 4.69 | 1.10 | 0.051 | 0.8054 | GATE-FAIL | 判死 |
| L3f0d21ab | 1011i 捡漏入池 4 口：ZYA9oeb3(g18_A1veMe9E_neSECTOR 平台0.687) / WjelxZJd(mix_03 0.6954) / j28Vd5kO(sp1009m_11 0.6986) / 1YZW01PJ(k88_01 0.6731) | 3 | 存量重验 | — | — | — | ≤0.705 | 全部平台 PASS | 已入池 |

## 4. 已用组合标记（跑过即打标记，禁止重复消耗模拟配额）

**规则**：① 组合一旦跑过，状态置「已跑」，同一组合不再重新发模拟（换轴/换腿的变形须另建 combo_id）；② 撞 corr 死的标「可复活」，等池漂移或换轴时用 `combo_gen.py --revive` 重出；③ 入池的标「已入池」并在台账留证。

### 4.1 1009 实测回写（母件 × 经济新腿 组合，全部 SUBINDUSTRY + 母件原 decay）

| 组合 | 主腿 idea | 佐腿 idea（经济机制） | 设定 | 实测 SF | tS | TO | corr | 判决 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| f15b_d14_32 | le8Evzp8 族（xrent+cash+cfo+close+vol） | E803 风险结构差 | SUBI d14 | 5.97 | 1.43 | 0.079 | — | 待判 | 已跑 |
| f15b_d14_07 | Vk6Za7Lw 族 | E801 系统性风险 | SUBI d14 | 6.42 | 1.65 | 0.118 | 0.8116 | 撞 corr | 可复活 |
| f15b_d14_10 | 同族 | E802 特质风险 | SUBI d14 | 6.38 | 1.76 | 0.109 | 0.8138 | 撞 corr | 可复活 |
| le8_d4_03 | le8Evzp8 族 | E803 | SUBI **d4** | 5.69 | **2.01** | 0.163 | 0.8099 | 撞 corr | 可复活 |
| le8_d4_05 | 同族 | E803 | SUBI d4 | 5.56 | 1.82 | 0.163 | 0.8089 | 撞 corr | 可复活 |
| f15b_d14_27 | 同族 | E501 预期修正 | SUBI d14 | 5.33 | 1.67 | 0.084 | **0.8121**（超0.66仅8） | 差 0.248 | **可复活（最优先）** |
| f15b_d16_01 | kqVvoRMP 族 | — | SUBI d16 | 4.76 | 1.28 | 0.105 | 0.8024 | 撞 corr | 可复活 |

**1012 三批登记（g21 新字段 16 / g22 重跑 10 / g23 解析式高 S 合成 12）。判决线已升 1.15，见 atoms.md D-65。**

| 组合 | 主腿/来源 | 佐腿（机制或预筛） | 设定 | 实测 SF | tS | TO | 本地 cmax | 判决 | 状态 |
|---|---|---|---|---|---|---|---|---|---|
| g21_00(npPGw6ed) | correlation_last_360_days_spy | 全新字段机制 | SUBI d10 | 0.09 | -0.06 | 0.0817 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_01(Vk0QKM10) | news_atr_ratio | 全新字段机制 | SUBI d10 | 0.49 | -0.06 | 0.1284 | 未判(闸前死) | SHARPE/FITNESS | 已跑 |
| g21_02(wpb7XPnQ) | sales_estimate_count | 全新字段机制 | SUBI d10 | 2.80 | 1.49 | 0.0704 | 未判(闸前死) | SUB_UNIVERSE_SHARPE | 已跑 |
| g21_03(mL6nelpW) | antidilutive_securities_eps_exclusion_count | 全新字段机制 | SUBI d10 | 0.99 | -0.37 | 0.1884 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_04(ZYAVkVKn) | correlation_last_360_days_spy | 全新字段机制 | SUBI d10 | -0.42 | -0.47 | 0.1066 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_05(N1VEkZ1L) | correlation_last_360_days_spy | 全新字段机制 | SUBI d10 | -0.14 | -0.88 | 0.1579 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_06(akxm2kex) | antidilutive_securities_eps_exclusion_count | 全新字段机制 | SUBI d10 | 1.31 | -0.01 | 0.0133 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_07(Vk0QwVlG) | mean_editorial_commentary_sentiment | 全新字段机制 | SUBI d10 | 1.99 | 0.21 | 0.2584 | 未判(闸前死) | FITNESS | 已跑 |
| g21_08(E5Rn0oEP) | news_pe_ratio | 全新字段机制 | SUBI d10 | 1.20 | -0.3 | 0.101 | 未判(闸前死) | SHARPE/FITNESS | 已跑 |
| g21_09(QPKRrdXg) | sales_estimate_count | 全新字段机制 | SUBI d10 | 0.38 | 0.19 | 0.0522 | 未判(闸前死) | SHARPE/FITNESS | 已跑 |
| g21_10(omWjwAQ5) | news_atr_ratio | 全新字段机制 | SUBI d10 | 0.34 | -0.53 | 0.3426 | 未判(闸前死) | SHARPE/FITNESS | 已跑 |
| g21_11(6XK6PY0Y) | correlation_last_360_days_spy | 全新字段机制 | SUBI d10 | -0.28 | -0.81 | 0.1034 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_12(npPGk3Vw) | vested_equity_award_total_value | 全新字段机制 | SUBI d10 | 1.40 | 0.13 | 0.0134 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_13(N1VEWpLL) | news_atr_ratio | 全新字段机制 | SUBI d10 | 1.97 | 0.2 | 0.0834 | 未判(闸前死) | FITNESS | 已跑 |
| g21_14(vR27nNbv) | news_mins_20_pct_dn | 全新字段机制 | SUBI d10 | 1.59 | 1.12 | 0.0502 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g21_15(QPKRr3j5) | correlation_last_360_days_spy | 全新字段机制 | SUBI d10 | 0.54 | -0.61 | 0.1683 | 未判(闸前死) | SHARPE/FITNESS/SUB_UNIVERSE_SHARPE | 已跑 |
| g22_00(gJZNqr9v) | qM0bJmJ2 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 5.80 | 2.84 | 0.1265 | 0.7661 | 撞墙1.15 gap15=-0.335 | 已跑 |
| g22_01(vR27nYAQ) | LLZwlGmL 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 5.59 | 3.15 | 0.2675 | 0.7689 | 撞 corr(未进beat) gap15=+0.000 | 已跑 |
| g22_02(88PWk2qq) | pwR1v8Ro 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 4.82 | 1.65 | 0.1077 | 0.7893 | 撞墙1.15 gap15=-0.195 | 已跑 |
| g22_03(ZYAVw1L3) | gJbo1jqK 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 5.04 | 2.41 | 0.1127 | 0.7622 | 撞墙1.15 gap15=-0.045 | 已跑 |
| g22_04(j2AJzVpZ) | j2AJzVpZ 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 5.19 | 2.05 | 0.1075 | 0.7288 | 撞墙1.15 gap15=-0.228 | 已跑 |
| g22_05(pw5bJ2ao) | npP0JJ0q 重跑 | 条目级 decay30 不生效→按默认 d10 重跑 | SUBI d10 | 5.35 | 2.06 | 0.1252 | 0.7187 | 撞 corr(未进beat) gap15=+0.000 | 已跑 |
| g22_06 | XgJxwzG0 抬S手术 | 应 decay30 | — | — | — | — | 0.7584 | 中止：mine_from_spec 静默忽略条目级设置 | 未跑 |
| g22_07 | E5RNkO3L 抬S手术 | 应 decay30 | — | — | — | — | 0.7792 | 中止：mine_from_spec 静默忽略条目级设置 | 未跑 |
| g22_08 | QPKAEmPW 抬S手术 | 应 decay30 | — | — | — | — | 0.7574 | 中止：mine_from_spec 静默忽略条目级设置 | 未跑 |
| g22_09 | kqV89LJd 抬S手术 | 应 decay30 | — | — | — | — | 0.7900 | 中止：mine_from_spec 静默忽略条目级设置 | 未跑 |
| g23_00(QPKRqeRQ) | 2rO9wZvJ+1YXrP2Oz 合成 | 预筛 predS 3.39 ≥1.15×2.39 | SUBI d10 | 6.68 | 2.63 | 0.1428 | 0.7707 | 撞墙：出 spec 时墙 2.39，今日 d516QO9v(S3.39) 入库后活墙 3.45，gap15=-0.647 | 已跑 |
| g23_01(9qW5bg2K) | QPba58lr+9qjqNl1r 合成 | 预筛 predS 3.29 ≥1.15×2.82 | SUBI d10 | 6.41 | 2.66 | 0.1421 | 0.8808 | 撞墙：出 spec 时墙 2.82，今日 d516QO9v(S3.39) 入库后活墙 3.39，gap15=-0.648 | 已跑 |
| g23_02 | blRJRxvl+d51wo9Yg 合成 | predS 3.28 | SUBI d10 | — | — | — | 0.7218 | 算子数 74~81 超 64 上限，平台直接拒(白烧 2 发) | 死 |
| g23_03(omWjAYoJ) | blRJRxvl+88jxNmVq 合成 | 预筛 predS 3.27 ≥1.15×2.82 | SUBI d10 | 6.36 | 2.46 | 0.1405 | 0.8609 | 撞墙：出 spec 时墙 2.82，今日 d516QO9v(S3.39) 入库后活墙 3.45，gap15=-0.737 | 已跑 |
| g23_04(O08dqnmb) | blRJRxvl+N1alPkze 合成 | 预筛 predS 3.25 ≥1.15×2.82 | SUBI d10 | 6.30 | 2.42 | 0.1416 | 0.8618 | 撞墙：出 spec 时墙 2.82，今日 d516QO9v(S3.39) 入库后活墙 3.45，gap15=-0.757 | 已跑 |
| g23_05(omWjAJRb) | omLK3KA2+d5bleWeX 合成 | 预筛 predS 3.21 ≥1.15×2.51 | SUBI d10 | 6.60 | 2.14 | 0.1141 | 0.7817 | 撞墙：出 spec 时墙 2.51，今日 d516QO9v(S3.39) 入库后活墙 3.39，gap15=-0.668 | 已跑 |
| g23_06(GrOjYOOG) | 2rwZNnN8+zq8JXwdX 合成 | 预筛 predS 3.19 ≥1.15×2.58 | SUBI d10 | 6.21 | 2.56 | 0.1477 | 0.7427 | 撞墙：出 spec 时墙 2.58，今日 d516QO9v(S3.39) 入库后活墙 2.92，gap15=-0.218 | 已跑 |
| g23_07 | 3qXnAveX+6Xj25gkP 合成 | predS 3.10 | SUBI d10 | — | — | — | 0.7301 | 算子数 74~81 超 64 上限，平台直接拒(白烧 2 发) | 死 |
| g23_08(LLZoqzae) | omLK3KA2+d5bleWeX 合成 | 预筛 predS 3.09 ≥1.15×2.58 | SUBI d10 | 6.39 | 2.06 | 0.098 | 0.7507 | 撞墙：出 spec 时墙 2.58，今日 d516QO9v(S3.39) 入库后活墙 3.39，gap15=-0.718 | 已跑 |
| g23_09(2rmVQ2Yb) | wpb3qXnd+78ZGmRV5 合成 | 预筛 predS 3.07 ≥1.15×2.39 | SUBI d10 | 6.85 | 2.71 | 0.1674 | 0.8339 | 撞墙：出 spec 时墙 2.39，今日 d516QO9v(S3.39) 入库后活墙 3.45，gap15=-0.547 | 已跑 |
| g23_10(2rmVQ2Yb) | wpb3qXnd+vRkY66xQ 合成 | 预筛 predS 3.07 ≥1.15×2.39 | SUBI d10 | 6.85 | 2.71 | 0.1674 | 0.8339 | 双胞胎：与上一条表达式同（腿序不同），按 D-60 不交，gap15=-0.547 | 已跑(不交) |
| g23_11(O08dq3od) | e7Q0E9ap+2rO9LxgJ 合成 | 预筛 predS 3.07 ≥1.15×2.58 | SUBI d10 | 6.17 | 2.26 | 0.1755 | 0.8503 | 撞墙：出 spec 时墙 2.58，今日 d516QO9v(S3.39) 入库后活墙 3.45，gap15=-0.797 | 已跑 |

| g25_00(pw5b797g) | trade_when(volume>ts_mean20) 门控 + xrent 族主腿 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 4.33 | 2.11 | 0.1503 | 0.7257 | BLOCK 墙 2.68 需 3.082 gap15=-0.30 | 已跑 |
| g25_01(3qVmA8GZ) | fnd6_newqv1300_ivstq+cimiiq 族移植 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 4.29 | 0.87 | 0.1481 | 0.7260 | tS 0.87 不过闸 | 已跑 |
| g25_02(MP3vpANr) | xrent 族同腿不同权变体移植 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 5.19 | 1.52 | 0.1461 | 0.9310 | 被自己孩子 P0gL2gVw(0.9310) 拦：拆腿件入池后母件当场作废 | 已跑 |
| g25_03(RR6xpXxg) | xrent+cash45+cashflow45/ev+价格2+量能60 五腿族 | TOP1000 移植，本族手术料源 | TOP1000 SUBI d10 | 5.20 | 1.49 | 0.1473 | 0.9336 | 同上，被 P0gL2gVw 拦（入池前 0.7171） | 可复活(族已封) |
| g25_04(vR27Llar) | cimiiq/xrent 族 0.50 权重版 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 5.59 | 1.76 | 0.1205 | 0.8939 | BLOCK 墙 2.81 需 3.231 | 已跑 |
| g25_05(N1VEprJE) | xrent+cimiiq 短表达式版 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 4.84 | 1.46 | 0.1522 | 0.8820 | BLOCK 墙 2.68 需 3.082 | 已跑 |
| g25_06(RR6xp5M1) | cimiiq 主副腿 0.35/0.65 反版权 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 5.34 | 1.64 | 0.1048 | 0.7928 | BLOCK 墙 2.81 需 3.231 | 已跑 |
| g25_07(mL6n80Ap) | Amihud(-abs(returns)/volume60) 主腿族 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 5.23 | 1.92 | 0.1761 | 0.9187 | BLOCK 墙 2.68 需 3.082 | 已跑 |
| g25_08(e7QMOXME) | annual_intangible_assets 主腿 + 价格副腿 | TOP1000 移植找低墙 | TOP1000 SUBI d10 | 4.72 | 1.66 | 0.1799 | 0.8009 | BLOCK 墙 2.68 需 3.082 | 已跑 |
| g26_00(leKwl0eN) | quantile(group_rank(xrent)) 分位包装 | 换包装算子改 PnL 投影 | TOP1000 SUBI d10 | 4.08 | 1.27 | 0.1017 | 0.8104 | SF/tS 双不过闸 | 已跑 |
| g26_01(zqb7mPLd) | fnd6_pstkl/cap 主腿 + 现金流副腿 | 换主腿字段 | TOP1000 SUBI d10 | 3.72 | 1.86 | 0.1155 | 0.7245 | SF 3.72 不过闸 | 已跑 |
| g26_02(6XK69jaY) | group_neutralize(signed_power(量能)) | 换包装算子改 PnL 投影 | TOP1000 SUBI d10 | 3.89 | 1.35 | 0.2231 | 0.6948 | TO 0.223 超线 + SF 3.89 不过闸 | 已跑 |
| g26_03(blO0qael) | fnd6_pstkl/cap 主腿第二变体 | 换主腿字段 | TOP1000 SUBI d10 | 3.38 | 1.42 | 0.0638 | 0.6855 | SF 3.38 不过闸（corr 已到直通区门口） | 已跑 |
| g27_00(6XK6jZg5) | RR6xpXxg 拆腿：只去 xrent | 手术记分台 D-70 | TOP1000 SUBI d10 | 4.11 | 1.44 | 0.174 | 0.6650 | SF 4.11 不过闸（xrent 一刀 -0.0521 要花 S 0.45） | 已跑 |
| g27_01(P0gL2gVw) | RR6xpXxg 拆腿：只去量能腿 | 手术记分台 D-70 | TOP1000 SUBI d10 | 4.85 | 1.58 | 0.1417 | 0.6425 | 直通 ACCEPTED，平台 selfCorr 0.6505（本地+0.008）——量能腿一刀 -0.0746 只花 S 0.15 | 已入池 |
| g27_02(Wjerbrlo) | RR6xpXxg 拆腿：xrent+量能都去 | 手术记分台 D-70 | TOP1000 SUBI d10 | 3.66 | 1.54 | 0.1695 | 0.6425 | corr 与只删量能腿完全相同 ⇒ 第二刀白烧；SF 3.66 不过闸 | 已跑 |
| g27_03(YPM3bR1A) | RR6xpXxg：现金流窗口 45→120 | 手术记分台 D-70 | TOP1000 SUBI d10 | 4.95 | 1.89 | 0.147 | 0.7096 | 改窗口只降 corr 0.0075，仍被墙拦 | 已跑 |
| g27_04(KPrArjvN) | RR6xpXxg：价格腿 ts_delta(close) 2→7 | 手术记分台 D-70 | TOP1000 SUBI d10 | 4.89 | 1.55 | 0.1301 | 0.7102 | 改窗口只降 0.0069，仍拦 | 已跑 |
| g27_05(N1VEVqg7) | RR6xpXxg：去 xrent + 窗口 120 | 手术记分台 D-70 | TOP1000 SUBI d10 | 3.85 | 1.91 | 0.1727 | 0.6630 | SF 3.85 不过闸 | 已跑 |
| g27_06(E5RnRelm) | RR6xpXxg：主副腿权重 0.65/0.35→0.50/0.50 | 手术记分台 D-70 | TOP1000 SUBI d10 | 5.16 | 1.63 | 0.142 | 0.6924 | 带内墙被否：墙@0.70=0 看着直通，墙@0.685=wpbqEPAx S2.41→需 2.77，实际 S 2.73 只余 0.004 | 已跑 |
| g27_07(RR6x67Oa) | RR6xpXxg：去 xrent+去量能+价格腿 7 | 手术记分台 D-70 | TOP1000 SUBI d10 | 3.33 | 1.59 | 0.1417 | 0.6315 | SF 3.33 不过闸（corr 最低的件死于 SF） | 已跑 |
| g28_00(0mrZPqp2) | scl12_sentiment 稀有字段骨架 | 验「只用 1~2 口稀有字段是否天生无墙」 | TOP3000 SUBI d10 | 1.92 | 0.65 | 0.2364 | — | 闸前死 S 1.27 | 判死 |
| g28_01(mL6na3Kx) | news_short_interest 稀有字段骨架 | 同上 | TOP3000 SUBI d10 | 1.05 | -0.23 | 0.0289 | — | 闸前死 S 0.67 | 判死 |
| g28_02(d51Jam62) | forward_price_90/30 稀有字段骨架 | 同上 | TOP3000 SUBI d10 | 0.29 | -0.64 | 0.1596 | — | 闸前死 S 0.22 | 判死 |
| g28_03(88PWNO0X) | implied_volatility_call_90/30 骨架 | 同上 | TOP3000 SUBI d10 | 1.79 | 1.5 | 0.1815 | — | 闸前死 S 1.11 | 判死 |
| g28_04(xAb7vYvN) | accumulated_oci_net_of_tax_value 骨架 | 同上 | TOP3000 SUBI d10 | 1.50 | 0.2 | 0.0442 | — | 闸前死 S 0.95 | 判死 |
| g28_05(xAb7vrZp) | fnd6_tstkc 稀有字段骨架 | 同上 | TOP3000 SUBI d10 | 0.69 | 1.11 | 0.029 | — | 闸前死 S 0.49 | 判死 |
| g28_06(A1vXxExw) | anl4_afv4_eps_high/low 分歧度骨架 | 同上 | TOP3000 SUBI d10 | 4.09 | 0.2 | 0.0783 | — | 闸前死 tS 0.20（S 2.25 是唯一接近的） | 判死 |
| g28_07(blO0a1dl) | scl12_sentiment 变体 | 同上 | TOP3000 SUBI d10 | 2.06 | -0.17 | 0.1468 | — | 闸前死 S 1.26 | 判死 |

| g32_0a(LLZorJ3M) | cx_04 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d14 | 4.76 | 1.65 | 0.1218 | 0.7230 | BLOCK 墙 2.58 需 2.967 实 2.46；母件 corr 0.7173→删完反升 +0.0057 | 已跑 |
| g32_0b(0mrZ6dl2) | dn_00 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d14 | 5.83 | 3.02 | 0.1096 | 0.7607 | BLOCK 墙 3.45 需 3.967 实 2.88；一刀只降 0.0075 | 已跑 |
| g32_1a(E5RnLvxL) | g23x_06 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d10 | 5.96 | 2.48 | 0.144 | 0.7499 | BLOCK 墙 2.92 需 3.358 实 3.04；一刀反升 +0.0072 | 已跑 |
| g32_1b(LLZorG8n) | w228_g 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d10 | 4.75 | 2.66 | 0.2229 | 0.8515 | TO 0.223 超线；且删腿使 corr +0.0747（本批唯一反向样本） | 已跑 |
| g32_1c | g23x_00 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d10 | — | — | — | — | 平台语法拒 Unexpected character ','：tidy 未清 "…) + , -1)" 空加数，白烧 1 发（规则已补） | 死 |
| g32_2a(e7QMvWbJ) | om6_12 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d40 | 4.79 | 1.39 | 0.0503 | 0.7467 | BLOCK 墙 3.39 需 3.898 实 2.52；一刀 −0.0002（等于没动） | 已跑 |
| g32_3a(kqgp9rNl) | push_d30_06 删量能腿 | 跨族手术记分台 D-71 | TOP3000 SUBI d30 | 5.07 | 1.67 | 0.0616 | 0.7195 | BLOCK 墙 3.39 需 3.898 实 2.62；本批最像样的一刀 −0.0303，仍差 1.28 | 已跑 |
| g32_4a | cba30_03 双刀(量能+Amihud) | 跨族手术记分台 D-71 | TOP3000 SECTOR d40 | — | — | — | — | 平台语法拒 signed_power(, 2)：第二刀删空了函数唯一实参，白烧 1 发（规则已补） | 死 |
| g32_5a(qM02V671) | x245_w228g_MAR 删量能腿 | 跨族手术记分台 D-71 | TOP3000 MARKET d10 | 4.76 | 2.33 | 0.2133 | 0.7573 | TO 0.213 超线；一刀 −0.0300 | 已跑 |

| g36_00(JjQ9V6dE) | QP 定权三腿合成 omLka3N5+rKOoJarE+akbgabjv | D-74 QP 线首弹 | TOP3000 SUBI d10 | 4.19 | 1.08 | 0.2392 | — | 我方三闸不过（SF 4.19 / tS 1.08 / TO 0.239） | 已跑 |
| g36_01(Wje5ERJo) | QP 定权三腿 ZYb1QE6Q+88j23vEl+mLmla0gp | 同上 | TOP3000 SUBI d10 | 5.44 | 2.36 | 0.1409 | 0.6717 | **平台 /check 全 PASS，selfCorr 0.6809 直通**；预测 0.6282 低报 0.053 | 已交 10-12 |
| g36_02(2rmYrL8J) | QP 定权三腿（d15 组） | 同上 | TOP3000 SUBI d15 | 5.67 | 1.56 | 0.1296 | 0.6930 | **贴线**（0.685~0.70 带内），按「不许贴线交货」不交，留作腿 | 不交 |
| g36_03(Vk0WkVwV) | QP 定权三腿 E5p2vN30+akbg71w1+2rw2NObx | 同上 | TOP3000 SUBI d10 | 4.57 | 2.19 | 0.0975 | 0.6098 | **平台 /check 全 PASS，selfCorr 0.6243 本批最干净**；预测 0.6350 反而偏悲观 | 已交 10-12 |
| g36_04(MP3rPwZr) | QP 定权三腿（本批 S 第二高） | 同上 | TOP3000 SUBI d10 | 5.48 | 2.23 | 0.1360 | 0.6871 | **贴线 +0.002**，李工明令「这个不交就下一个」 | 不交 |
| g37_00(KPr1Pg5x) | QP 定权三腿（高 S 低 TO 组） | D-74 QP 线首弹 | TOP3000 SUBI d10 | 5.46 | 2.35 | 0.3324 | — | TO 0.332 超线；且墙 3.10 需 3.565 | 已跑 |
| g37_01(leKmenGN) | QP 定权三腿 RRV7QVQn+QP37JW0G+pwPlK163 | 同上 | TOP3000 SUBI d8 | 5.85 | 2.17 | 0.1661 | 0.7374 | **平台 /check 全 PASS＝弱墙豁免道实弹兑现**（对手 1 条 墙 2.35 需 1.15×2.35=2.702，实 S 3.08 余 +0.378）；本批 SF 最高 | 已交 10-12 |
| g37_02(O0830A3d) | QP 定权三腿 58z2EEPM+KPN2g1bk+6Xj2pjlO | 同上 | TOP3000 SUBI d10 | 5.28 | 2.29 | 0.1354 | 0.6523 | 平台 /check 全 PASS(selfCorr 0.6480)，**但与 `Wje5ERJo` 互相关 0.9496 ⇒ 按 D-77 撤下，留作腿** | 撤下(双胞胎) |
| a1_00..75(80 发) | 20 个池外稀有字段 × 4 个一阶模板（9 数据集） | 一阶 ATOM 线 D-73 | TOP3000 各族 | 最高 2.01 | — | — | — | **整线判死：0 条过四闸，最高 SF 只有 2.01**；冷字段冷在弱不是冷在撞墙 | 判死 |

| g41_03(npPEY17q) | QP 三腿 QPbovKag+levNawqO+ZYAvRZ3n（腿池 134→148 后的新靶） | D-76 补判喂腿 | TOP3000 SUBI d10 | 5.60 | 2.31 | 0.1495 | 0.7801 | **预测 0.6295 → 实测 0.7801（误差 +0.15，D-78 的头号样本）**：对手 3 条 墙 2.82 需 3.243，实 S 2.96 差 0.283 | 判死 |
| g41_06(omWdAmev) | QP 三腿 xA3Evm8p+mL6WLwW5+P02A8RlJ | 同上（今日第 4 条） | TOP3000 SUBI d10 | 5.11 | 2.25 | 0.1492 | 0.6737 | **平台 /check 全 PASS，selfCorr 0.6702 直通**；与另 3 条待交件互相关最大 0.61（不过 D-77 双胞胎闸） | 已交 10-12 |

| g44_00(3qVNxvMX) | QP 三腿 QPbovKag+pw5k96Qg+levNawqO（=g43_01 靶） | D-76 L1 备货 | TOP3000 SUBI d10 | 5.61 | 2.53 | 0.1542 | 0.6682 | 平台 /check 全 PASS，但 **预测 0.5432 → 实测 0.6682（+0.125，D-78 第 2 例）**；L1 线 0.60 不过 ⇒ 只留作腿 | 不交(L1) |
| g44_01(leKm2N82) | QP 三腿 58z2EEPM+gJZ52NXg+KPN2g1bk（=g43_02 靶） | 同上 | TOP3000 SUBI d10 | 5.31 | 2.31 | 0.1630 | 0.6844 | 平台 /check 全 PASS，**预测 0.5644 → 实测 0.6844（+0.120）**；离本地直通线只差 0.0006=贴线，按「不许贴线交货」+L1 双重不交 | 不交(L1) |
| g44t_00(blOwPg0m) | 与 `3qVNxvMX` 同表达式，**只把 universe 换成 TOP1000** | D-79 换池验证 | TOP1000 SUBI d10 | 3.86 | 3.17 | 0.1597 | 0.5653 | **换池一刀 −0.103：selfCorr 0.5653 已达 L1**；但 SF 5.61→3.86（−31%）掉到我方 4.2 闸下 ⇒ 买到 corr、输掉 SF；sub-universe 闸 1.37/1.17 反而过 | 判死(SF) |
| g44t_01(rKexzwMJ) | 与 `leKm2N82` 同表达式，只换 TOP1000 | 同上 | TOP1000 SUBI d10 | 2.80 | 1.86 | 0.1806 | 0.5499 | **−0.135 到 0.5499，L1 达标**；SF 5.31→2.80（−47%）不过闸 | 判死(SF) |

统计：已跑 388（本次并入 g36 5 + g37 3 + a1 80 + g41 2 + g44 4 = 94；g36/g37 里 3 条已于 10-12 提交入池、`O0830A3d` 因与 `Wje5ERJo` 互相关 0.9496 按 D-77 撤下、2 条贴线不交、2 条我方闸不过；g41 里 1 条已提交 1 条判死；g44 四条全不交——TOP3000 两条 L1 不过、TOP1000 两条 SF 不过，构成 D-79 的双向证据；a1 整线 80 发判死，日志留档 64 行最高 SF 2.01。**10-12 实交 4 条：`Wje5ERJo`/`Vk0WkVwV`/`leKmenGN`/`omWdAmev` 全 ACCEPTED，墙池 209→213**）

**本轮结论（写死，不再重复踩）**

1. **母件设定必须原样继承**（见 atoms.md D-34）。套 MARKET+decay40 会把 SF 6.19 打成 1.93。
2. **decay 4 是本族甜点**：tS 从 1.48 抬到 2.01，SF 只掉 0.3，TO 仍在 16% 内。
3. **死因是 S 不是 corr**：need 被池里 S=3.45 的 `0mR2K6lr` 顶到 3.795，本批 S 封顶 3.11。**先量 need 再提 S**。
4. **经济新腿本身不是主腿**：`systematic_risk_*` / `fscore_bfl_*` / `composite_factor_score_derivative` 裸信号 SF≤2.9，只能当佐腿（权重 0.6）。这条 1009 已实测确认。
5. **最优先复活项**：`QPKOlw8X`（f15b_d14_27）只差 0.248，且超 0.66 对手仅 8 个——池子一变就能过。

**本轮结论（1012，g25~g28 + 手术记分台 D-70，写死，不再重复踩）**

1. **合并族已封，不可再用**：P0gL2gVw 入池后，xrent / cash / cashflow / 价格 / 量能这一整族全军覆没——RR6xpXxg 本地 corr 从 0.7171 跳到 0.9336，MP3vpANr 到 0.9310。自己孩子入池，母件当场作废，这是 D-70「一族一口是算术」的直接体现。
2. **blend 路线判死（预测器未标定）**：`blend_search_1011.py` 的 predS/pred corr 系统性低估合成后 cmax +0.04~+0.15，g23 十条 10/10 BLOCK。重标定之前不再投合成批次。
3. **换 universe 移植 ≠ 去相关**：同一表达式 TOP3000↔TOP1000 交叉对照 17 组，移植后 corr 常常更高而不是更低。g25 九发的 cmax 全在 0.72~0.93，没有一发因为换池掉进直通区。此路封。
4. **稀有字段裸骨架判死**：g28 八发（scl12_sentiment / news_short_interest / forward_price / implied_volatility / accumulated_oci / fnd6_tstkc / anl4_afv4）S 封顶 2.25，全部闸前死。稀有字段只能做副腿，做不了主腿——这条推翻了 atoms.md 里「稀有=无墙」的假设。
5. **量能腿是当前唯一便宜的手术刀**：一刀 -0.0746 corr 只花 S 0.15（P0gL2gVw 实证）；xrent 一刀 -0.0521 要花 S 0.45；改窗口/改权重只动 S 不动 corr（-0.007 / -0.007 / -0.025）。手术队列按「本族未切过 + 高流行度腿」排，一个族只许切一刀。
6. **带内墙必须双底线校验**：0.685~0.70 之间是误杀带。g27_06(E5RnRelm) 就是典型——@0.70 墙为 0 看着直通，@0.685 墙 wpbqEPAx S2.41 需 2.77，实际 S 2.73 只差 0.004，属于赌平台读数，判死不改。

### M14（1013 深夜队列）内层刀重开 + 纯冷数据集探针

**排队的四批（g57 收尾后串行，脚本 `_autologs/_run_g589.sh` / `_run_g60.sh` / `_run_g61.sh` 用哨兵文件互锁）**

| 批 | 发数 | 靶/做法 | 依据 | 读法 |
|---|---|---|---|---|
| g57 | 91 跑到第 3 组 | 删腿产线（0.65~0.75 母件，含 p2 删两条腿） | D-90/D-92 | 尾巴件 cmax 落点 |
| g58 | 4 | `xAbzvLbn`（全场最低 0.6491）**内层删一项** | D-95（内层刀此前是哑的） | 一刀是否 ≥−0.055 |
| g59 | 30 | 0.70~0.725 未动母件，**一次删两条腿(p2)** | D-92 留的活口 | p2 刀程能不能到 −0.15 |
| g60 | 61 | 0.70~0.765 段 17 个**老母件重开细刀**（DEDUP 去掉已打过的 472 刀） | D-95 | 细刀 vs 粗刀的 Δcmax 分布 |
| g61 | 64 | **整件纯冷数据集**四腿合成：option9(pcr_oi/pcr_vol/breakeven 期限比)、option8(IV−HV 波动率风险溢价、call/put 偏度)、model51(beta/系统性风险比)、socialmedia12(情绪×buzz)，32 表达式 × TOP3000/TOP1000 同 SUBI d5 | D-94（1,153 条门槛件**每一条**都带 fnd6/fnd2/anl4/pv1 腿；池里 option9 仅 2 次、model16/model51 0 次） | 只要 1 条 S≥1.78 且 cmax<0.65 ⇒ 明天进料口；全批最高 S<1.4 ⇒ 与 D-73/D-88 同判死 |

⚠ 与 1012 结论 4（「稀有字段做不了主腿，S 封顶 2.25」）的关系：那条是老四闸下判的死，**S 2.25 在新三门下本来就过 G1**，
当年死于 SF/TO 闸而不是死于 corr ⇒ g61 不是重复踩，是把同一批素材换到新的判决线上重估。g61 跨池同表达式配对（32 对）顺便给
D-94 的 ΔS/Δcmax 表补样本。

**夜自动尾巴（`_autologs/_run_tail.sh` → `_tail_decide_1013.py`，等 G61ALLDONE 后自判）**

已备料未发：`g62` = 0.725~0.80 段 26 个母件的 p2/细刀 121 发；`g63` = 冷空间第二探针（news18 Ravenpack 情绪与新颖度、
model16 fscore_* 与 *_rank_derivative、socialmedia8、option8 改用「偏离自身 20 日均值」构造）24 表达式 × 2 池 = 48 发。
决策规则写死：**出现 ≤0.5957 且过三门的子件，或任一刀程 ≤−0.12 ⇒ 追加 g62；否则不投 g62（禁止同空间加注），只投 g63**。
两条都不空转：夜间算力在 01:30 之后还有 6 小时以上。

### M15（1014 队列）混节奏 ⇒ 字段级冷料 ⇒ 分组轴配对

| 批 | 发数 | 靶/做法 | 依据 | 读法 |
|---|---|---|---|---|
| g69 | 41(实落 40) | 单数据集慢冷件（option8/model51/model16 × 慢模板） | D-105 重开条件 | **判死**：重开条件 0 条，最强 `g69_32` S1.94/cmax0.7400（D-107） |
| g70 | 46(实落 45) | **跨数据集**纯冷 4~6 腿复合 × 4 慢模板 | 107 条腿表 | 墙第一次到 0.6032（`g70_24` 只卡 G3，D-108）；corr(S,cmax)=0.639 |
| g71 | 35+35 | 5 个 g70 实测族 × 7 变体（混节奏/全慢/加稀释腿/原样），decay10 与 decay20 各一批 | D-108③（节奏刀 4 正 4 负）+ D-95（decay 换 TO 不换 S） | 首发 `g71_01 omopO9Ql` **S2.22/F1.75/后劲0.86/零 FAIL**，是本项目史上第一条"三门已过只等 cmax"的件 |
| g72 | 46 | **字段级**冷料：news18/news12/option9/model16 的池外字段（`event_sentiment_score`、`global_event_novelty_score_2`、`option_breakeven_150`、`multi_factor_static_score_derivative` 等），沿用 g71_01 的"2 快 + 2 慢"四腿形状 + 单腿对照 | 字段撞池实测：`nws18_nip` 被我已交池 **7 条**用过、`nws18_qep` 3 条、`scl12_buzz`/`implied_volatility_call_30` 各 1 条；而 news18 有 36 个 coverage≥0.95 的字段我一次没试过 | 配对读法：g72 复合 vs g70 同形状 ⇒ 换字段值多少 Δcmax |
| g72b | 10 | g72_00~04 逐字同表达式，只把腿里 `subindustry` 换 `industry`/`sector` | D-95 只量过换中性化的 ΔS≈0，从没在冷复合上量过 Δcmax | 5 对配对差 = 分组轴刀程 |

**串行与互锁**：g71 发射+判决+PnL/cmax（`_wait71_1014.sh`）跑完打印 `CMAX71ALLDONE`，`_run_g72all_1014.sh` 才开 g72/g72b ⇒
全程只有一个进程在打 API（429 已吃掉 `g70_02`/`g71_00`，不再制造第三个）。

**已知口径漏洞（要在 g72 判决前补）**：`POOL_FIELDS` 只从本地 mined 拿到 181/219 条池件表达式，剩 38 条没有表达式 ⇒
"字段池外"是下界判断。补法：`GET /alphas/{id}` 拉那 38 条的 regular.code（只读、38 发，等发射窗口空出来做）。

### M16（1014 晚间队列）判分口径换血：G3 从本地矩阵改成平台 `/check` 真值

**为什么换**：18:3x 实测 `GET /alphas/{id}/check` 对**未提交**件会重算并返回 `SELF_CORRELATION value=0.5568 limit=0.7`
（同一条 alpha 的详情端点同项仍是 `PENDING`）。此前 G3 只能靠本地 218 条 PnL 矩阵近似，D-108/D-110 实测偏差 ±0.008、
方向还不固定 ⇒ 0.60 上下那条带内的件本地判生死都不可信。现在带内一律送检（详见 atoms.md D-110①②⑦）。

| 批 | 发数 | 靶/做法 | 依据 | 读法 |
|---|---|---|---|---|
| g73 | 77 | F24/F20/F00 三族的**节奏位置全枚举**（2慢2快 6 + 1慢3快 4 + 3慢1快 4 + δ120 中档 6 = 18/族），加 16 个**跨组拼新族**（固定赢家节奏 FFSS），加赢家邻居的稀释腿 | 赢家 omopO9Ql = F24 FFSS；g71 只试了"前2慢/后2慢/全慢"三种位置；同族 FFFF(vROq8Ajw) sc 0.5949 而 FFSS sc 0.5568 ⇒ 位置本身就是刀 | 位置网格上 sc 与 F 怎么动；跨组新族能不能复现 FFSS 的形状 |
| g73b | 25 | g73 里 F24 的 14 个节奏位置 + 稀释腿，换 **decay20** | D-95 换 decay 的 ΔS≈0，主要改 TO ⇒ 改 F | 同形状 decay 10/20 的 TO、F、sc 三联读数 |
| g74 | 8 | 两个**平台 sc 已实测干净**的形状 FFFF / FFSS × decay {5,15,25,30} | vROq8Ajw 三门全过只差 F 0.18（TO 0.2348 偏高）；omopO9Ql F1.75 离 EXCELLENT 门票实测 F≥2.01 差 0.26 | 把 decay→TO→F 这条刀程量成网格（4 点/形状） |
| 送检 | 400 + 剩余 ~560 | 全库存 `G1+G2+交单F` 已过、内嵌 checks 零 FAIL、未提交的 **960 条**（表达式去重后）按 F 降序打 `/check` 拿平台 sc 真值 | 这 960 条历史上只按本地 cmax 判过生死 | 抽前 3 条真值 0.8325/0.8970/0.8465 ⇒ 强件确实贴墙；有翻案的就是当日供给 |

**串行互锁（全程只有一个进程打 API）**：g73/g73b（打印 `G73ALLDONE`）→ 400 条送检（`CHECKSWEEPDONE`）→
g74 发射+判决（`G74DONE`）→ 剩余库存送检（`SWEEPTAILDONE`）。送检进度落 `_autologs/_checked_ids_1014.json`，
结果累计落 `_autologs/_g3free_1014.json` ⇒ 任何一轮被打断都不重复花钱。

**新出现的流程限制（必须逐条串行交单）**：`/check` 的对手集合 = 当前已入池的我的件。提交 1 条后池子 +1，
**其余候选的 sc 真值全部作废、要重打**。所以"送检一批→一次交一批"不成立，只能送检→交 1 条→重送检。

### M17（1116 周复盘）本周 16 入池 / 9 被拒的配方判据

全量数据见 `docs/research/weekly_alpha_review_2026-11-16.md`（平台 API 实拉 + verdict 逐份读）。

**新验证配方**
- GLB gSc returns 双腿家族 4/4（d5al5ljw/LLKlxA7m/YPaWd16q/WjlWKLPj）：`0.5*gSc(-ts_std_dev(returns,120),G) + 1.4~1.5*gSc(-ts_av_diff(returns,45|60),G)`，MINVOL1M/STATISTICAL/decay64。G 互换=corr 重掷刀；sector+country 交叉组最强（S2.85/F2.01）。同族每日 ≤1 条。
- 主题限定超级 d5almKdJ：selection=`(1-self_correlation)*in(datasets,"model51")` + limit10 + decay25 → S3.18/F3.22/TO0.0533 ACTIVE。超级配额可按数据集家族轮吃（下一个候选：global_seasonal_model / predictive_starmine）。

**失败模式定量（9 条 POST 级）**
- PROD 杀 4 条：WjlK1b2k(0.8856,S8.26)、QP0mXGY5(0.8263,S8.73)、vRAavlk3(0.7061)、1YW6pJQJ(0.7002，差 0.0002)——高 S 特赦在 0.82+ 密集区无效；压线 0.68~0.699 先 decay+6 再交。
- LOW_FITNESS 杀 5 条：RReZrkq0 TO0.4405→F0.56 最极端；6XMg30YJ/O0WKmPAJ F0.65、YPaXdv2l 0.75、A1xq6OPe 0.92。TO>0.25 的批不发模拟。
- 预检频次（当前提交器实例）：SKIP-PROD 12 条 corr 0.6972~0.8226；SKIP-LOCAL 85 条，失败项 TOP：LOW_FITNESS 117 次 > IS_LADDER 34 ≈ LOW_SHARPE 34 > HIGH_TURNOVER 24 > GLB EMEA 8（分区短板）。

**多样性记账（本周 13 常规的族分布）**
GLB gSc returns 族 4 / option 主腿 3 / fnd6 主腿 2 / 混合引擎 3 / tm+tcm 1（KPgepR9k，ATOM 红线下不可复制）。下周方向：gSc 族限流，配额让给新数据集主腿。

**流程项**：/competitions/challenge 11-16 起 404，isScore/rank 断链待修（锚点停在 10-06 isScore 9691/rank 14）；OS count=360 与台账对平（d5almKdJ 漏记已补）。

### M18（1116 15:2x）★ 每日一 idea 轮转制 —— 多样性来自 idea，不来自模板

**李工指令原文（11-16 15:2x）**：
> 「每个 idea 单独构造，这样多样性就自然而然有了，你那模板套，怎么都不会有多样性，这样无法提升 VF。
> idea 只能决定数据集，其他的有很多空间来造，我们可以每天用一个 idea 提交 4 个普通的 Alpha，
> 今天用财务类的 idea，明天有新闻/情绪…，量价类的优先级最低，这样一轮循环后，我再回到财务类的 idea，
> 继续造，这样多样性就不用刻意了，自然而然就有了」

**据此确立的作业制（覆盖一切"批量凑件"做法）**：
1. **一天 = 一个 idea = 4 条普通 Alpha**（配额 4 常规，正好一批）。
   4 条必须是**同一个 idea 的不同构造**（不同腿/不同变换/不同外壳），
   **不是** 4 个 idea 各一条，更**不是** 模板批量生成。
2. **idea 决定数据集**；数据集确定后，**构造空间是自由度**（不是模板自由度）。
3. **轮转顺序（李工指定）**：财务类 → 新闻/情绪类 → 分析师类 → …… → **量价类垫底**。
   一轮循环完再回财务类，**在同一 idea 家族上再深挖**（不是换新字段，是换新构造）。
4. **多样性由此自动达成**：idea 维每日只 +1 个新值、数据集维每日只 +1 个新值，
   而 operator 维/构造维在**同一个 idea 内部**自然铺开。
   ⇒ **禁止**为了"多样性"而机械换数据集/换外壳/换字段——那是人海战术。

**11-16 当日 idea = M18-01「营运资本错配压力」（fundamental23）**

- **经济机制链**：
  应收膨胀（客户占款）→ 现金被占用 → 同时应付收缩（供应商收紧信用、挤兑）→
  现金缓冲薄 → 营运资本净缺口扩大 → 只能靠外部融资或砍投资 → 未来盈利与股价承压。
- **为什么这个机制未被定价**：这四个科目都是**存量时点值**，
  市场定价关注利润表（EPS/营收）与其变化，
  而**营运资本的结构性错配**需要跨 3~4 个资产负债表科目做**组合**才能读出来，
  单看任一科目都无信号 ⇒ 这是「组合才产生信息」的典型 idea。
- **字段（全部 fundamental23 单数据集，ATOM 合规；平台权限已验：45 件 UNSUBMITTED）**：
  | 字段 | 语义 | 在机制里的角色 |
  |---|---|---|
  | accounts_receivable_current | 应收账款净额 | 占款规模 |
  | accounts_receivable_gross | 应收账款毛额 | 毛-净差 = 已计提减值 |
  | allowance_for_doubtful_accounts | 坏账准备 | 账龄恶化的直接证据 |
  | accounts_payable_current | 应付账款（流动） | 供应商挤兑强度 |
  | accounts_payable_noncurrent | 应付账款（非流动） | 供应商长期信用意愿 |
  | accounts_payable_trade_creditors | 应付贸易债权人 | 纯商业信用（剔金融性应付） |
  | accounts_payable_notes | 应付票据 | 票据化 = 供应链票据池占比 |
  | accounts_cash_and_equivalents | 现金及等价物 | 缓冲厚度 |
  | accounts_total_current_assets | 流动资产合计 | 分母（规模归一） |
  | accounts_receivable_total_5 | 应收账款合计 | 口径交叉验证 |
- **4 条构造（同一 idea 的 4 个不同构造，非模板）**：
  | 编号 | 构造切入 | 经济含义 |
  |---|---|---|
  | M18-01-A | **净营运资本缺口的时间变化**：`(AR_total - AP_current) / 流动资产` 的 ts 差分 | 缺口在扩还是在补 |
  | M18-01-B | **毛-净缺口（隐含减值率）**：`1 - AR_net/AR_gross` 的时序位置 | 账龄是否在恶化 |
  | M18-01-C | **商业信用比（供应链地位）**：`AP_trade_creditors / AP_total` 的变化 | 供应商给不给信用 |
  | M18-01-D | **现金缓冲覆盖**：`(cash - AP_current) / 流动资产` 的趋势 | 缓冲还剩多少 |
  4 条各自成条（单数据集 ≥3 字段），**共用同一经济机制**，用于比较"哪条腿最能读出机制"。
- **登记状态**：待跑。

**M18-02（明日候选）新闻/情绪类**：
- 备选机制①：负面情绪的**强度 vs 广度**（负面计数高但文章数不增 = 集中利空 vs 全面悲观）
- 备选机制②：情绪的**持续性**（新闻情绪的半衰期 vs 股价吸收速度）
- 数据集候选：mmp_nlp_sentiment（121 字段，uc 0~10，极冷）/ twitter_sentiment_l2（18 字段）

**M18-03（轮转第三站）分析师类**：analyst27 / analyst16 / model109
- 备选机制①：分析师**修正的宽度 vs 深度**（谁在上调 vs 上调幅度）
- 备选机制②：评级**期限结构**（近 12 月评级 vs 近 24 月评级的加速度）


---

### M19（1116 16:00~17:20）★ 分析师惊喜「形状」重写 + 字段语义纠错 + 形状微调制

#### M19-0 前置纠错：字段语义用错 = 表达式写错（李工 11-16 16:00 判据反转）

> 「每一个 idea 都经过验证的，绝对可以搞出 Alpha 来，现在只看相关度能否够，
>   你说的 S,F 这些过不了，绝对是没有理解这个 idea，表达式写错了。」

**新判据（覆盖一切"按 S 高低取舍"的旧表述）**：
- S/F 过不了门 ⇒ **表达式写错了**，不是 idea 不行、不是 S 低。
- S/F 门 = **表达式正确性检查器**，不是 idea 判决书。
- S 是**当前形状**的属性 ⇒ 动作是**改形状**，不是取负、不是换 idea。
- 前置动作固定为：**归因（拆腿）→ 在有信号的腿上做形状微调**。

**查出来的字段语义错（Jj8gZxvA / IDEA_M19）**：
| 字段 | 我一直以为 | 平台权威 description | 真实 dataset |
|---|---|---|---|
| `act_q_ebi_surprisenum` | EBIT 惊喜值 | Number of estimates used for surprise calculation of actual EBIT（**估计家数**） | **analyst7** |
| `act_q_ner_surprisenum` | 净利润惊喜 | Number of estimates used for surprise calculation of actual net profit（**估计家数**） | **analyst7** |
| `act_q_bps_surprisemean` | 账面惊喜 | Mean surprise (actual − estimate) of actual BVPS（**这条才对**） | analyst7 |

⇒ 原式 LEG1 实为「分析师覆盖广度变化」、LEG3 实为「估计家数变异系数」，
  与 SURPRISE_SHAPE **无关**；idea 要的"形状"（mean 相对 std 的信噪比）
  **根本没用到 `surprisestd`**。台账标的 `earnings4` **也是错的**。

**analyst7 surprise 三件套（写表达式必须按这个来）**：
- `act_q_XXX_surprisemean` = **惊喜水平**（实际 − 一致预期）
- `act_q_XXX_surprisestd` = **惊喜分歧**（分析师之间预期差）
- `act_q_XXX_surprisenum` = **覆盖广度**（几个分析师）

**纪律**：写表达式前先查 description（`_grid/show_ds_fields.py`），不靠字段名猜；
  idea 名字决定选哪个字段族；dataset 以字段自带 `dataset.id` 为准。

#### M19-01 惊喜「形状」的机制推导（水平 × 分歧 两维）

| 水平 | 分歧 | 含义 | 预期 |
|---|---|---|---|
| 高 | 低 | 一致性超预期 = 真信息 | 正向漂移（PEAD） |
| 高 | 高 | 惊喜大但预期乱（一次性/口径变化） | 不可持续 |
| 低 | 高 | 预期乱且没兑现 | 负向 |

⇒ **核心量 = `surprisemean / surprisestd`（信噪比 = t 统计量）**：
  不是"惊喜有多大"，而是"惊喜**相对自身分歧**有多突出"。
⇒ **第二维 = 跨科目一致性**：EPS 与 Sales/EBIT 惊喜是否同向。
  同向 = 经营实质改善（可持续）；背离 = 靠一次性项目/口径调整（不可持续）。

#### M19-02 四条构造（同一 idea 的四种独立读法，各手写，非模板套）

| 编号 | 构造 | 字段 | 经济含义 |
|---|---|---|---|
| H1 | `surprisemean/surprisestd` | eps / ebi | 信噪比（惊喜相对分歧多突出） |
| H2 | 惊喜**变化率之差** | eps vs sal | 会计口径 vs 经营口径背离 ⇒ 一次性成分 |
| H3 | `eps × ebi` 惊喜乘积 | eps, ebi | 跨科目同向 = 一致性 |
| H4 | `surprisestd/surprisenum` | eps | 分歧是"人少而乱"还是"人多而分歧" |

设置层轮换（同一批 5 条，universe/neutralization/decay/truncation 全部铺开）：
TOP3000+SUBINDUSTRY+d10+0.08 / TOP1000+INDUSTRY+d20+0.05 / TOP500+SECTOR+d30+0.03
/ TOP2000+MARKET+d44+0.02 / TOP2000U+SUBINDUSTRY+d15+0.01
（★ TOP2000U 实测平台不可用，已换 TOP200。）

#### M19-03 形状微调制（六动作，每动有经济含义，工具 `_grid/morph.py`）

| 动作 | 做什么 | 经济含义 |
|---|---|---|
| A1 加层 | 内核外再套 ts_zscore(n) | 信号由「跨股比值」变为「该股自身历史的异常偏离」（换信息维度） |
| A2 减层 | 剥内核 ts_zscore / 剥 ts_decay_linear | 保留幅度信息 / 去掉平滑（换手升、信号更即时） |
| A3 换窗口 | 最长窗口换档 | 改信号记忆长度（长窗稳而钝，短窗灵而躁） |
| A4 换归一 | ts_zscore → ts_rank | 时序归一由「几个标准差」改为「历史序位」，免疫极端财报 |
| A5 换分组 | subindustry → industry/sector | 换「同业参照系」 |
| A6 换外壳 | group_zscore → group_scale/zscore | 换最终排序语义（保留量纲 / 丢掉同业参照） |

**归因实测（Jj8gZxvA 拆腿，4 条全落）**：
| 腿 | S | F | TO | tS | 解读 |
|---|---|---|---|---|---|
| FULL | -0.14 | -0.02 | 0.113 | -0.38 | rnS=+0.05 |
| LEG1 | **-0.39** | -0.11 | 0.064 | **+1.51** | ★ tS 全场最高 ⇒ 不是没信号，是 IS 段被风险暴露压住 |
| LEG2 | -0.09 | -0.01 | 0.204 | 0.38 | 换手太高 |
| LEG3 | -0.54 | -0.18 | 0.083 | -0.33 | 纯拖累 |

⇒ 正确动作：**在 LEG1 上做形状微调**（不是整条取负），且必须换成**真的惊喜字段**。

#### M19-04 平台 USA EQUITY 实测可用清单（11-16 逐个 POST 验证）

- **universe 6 项**：TOP3000 / TOP2000 / TOP1000 / TOP500 / TOP200 / TOPSP500
- 不可用（HTTP400）：TOP1500 / TOP1200 / TOP400 / TOP100 / TOP2500 / TOP1600 / TOP2000U
  / MINVOL1M / ILLIQUID_MINVOL1M / TOPDIV3000
- **neutralization 6 项**：NONE / MARKET / SECTOR / INDUSTRY / SUBINDUSTRY / STATISTICAL
  （COUNTRY 不可用）

---

### M20（1116 17:20~18:00）★ 形状微调实测：group_scale 外壳最优 + 算子数与 S 无关（再证）

#### M20-01 今日唯一有信号的方向 = 分析师惊喜「信噪比」

M19 四条构造里只有 **H1（`surprisemean/surprisestd`）** 跑出真信号，
其余三条（S=0.37 / +0.27 / 负）全塌 ⇒ **idea 本身成立，形状要调**。

基准件（`M1902_H1_snr_eps`，id `RRe2Y1Ez`）：
```
group_zscore(ts_decay_linear(ts_zscore(ts_mean(act_q_eps_surprisemean,60)
                                          /ts_mean(act_q_eps_surprisestd,60),120),10),subindustry)
```
→ S=+0.90 F=+0.40 TO=0.037 tS=-0.68 rnS=+0.48

**同日同族控变量对照（11 算子的 Jj8gZxvA vs 5 算子的 M1902_H1）**：

| cid | 算子数 | S | 说明 |
|---|---|---|---|
| M1902_H1_snr_eps | **5** | **+0.90** | 今日最高 |
| M1902_H1_snr_ebit | 5 | +0.71 | EBIT 口径 |
| M1902_H2_divergence | 7 | +0.37 | tS=+1.56 |
| M1902_H3_consistency | 5 | +0.27 | |
| SYN_analyst7_C1_0（=Jj8gZxvA） | **11** | **-0.14** | 字段语义全错 |

⇒ **算子最多的那条 S 最低**。算子数与 S 非单调（详见 M20-03）。

#### M20-02 ★ 形状微调实测：外壳 `group_scale` 把 S 从 0.90 顶到 1.00

`_grid/morph_m1902_h1_eps.json` 18 条（同一内核，只动外壳/窗口/设置层）实测：

| 变体 | 动作 | S | F | TO | 判定 |
|---|---|---|---|---|---|
| **MA6_groupzscoregro** | **group_zscore → group_scale** | **+1.00** | **+0.46** | 0.038 | ★★ **checks 无任何 FAIL** |
| MA4_tszscoretsrank | ts_zscore → ts_rank | +0.92 | +0.40 | 0.032 | FAIL×2 |
| D4 | decay 10→4 | +0.91 | +0.40 | 0.040 | FAIL×3 |
| D20 | decay 10→20 | +0.89 | +0.39 | 0.040 | FAIL×3 |
| NSECTOR | 中性化→SECTOR | +0.89 | +0.39 | 0.040 | FAIL×3 |
| NMARKET | 中性化→MARKET | +0.87 | +0.38 | 0.040 | FAIL×3 |
| D44 | decay 10→44 | +0.85 | +0.37 | 0.030 | FAIL×3 |
| MA5_subindustrysec | 分组→sector | +0.80 | +0.35 | 0.040 | FAIL×3 |
| MA5_subindustryind | 分组→industry | +0.79 | +0.34 | 0.040 | FAIL×3 |
| MA6_groupzscorezsc | 去掉 group 层 | +0.79 | +0.34 | 0.040 | FAIL×3 |
| MA3_12045 | zscore 窗口 120→45 | +0.67 | +0.24 | 0.040 | FAIL×2 |
| MA2_tsdecaylinear | 剥掉 ts_decay_linear | +0.24 | +0.10 | 0.024 | FAIL×4 |
| MA2_tszscoretszsco | 剥掉内核 ts_zscore | +0.23 | +0.10 | 0.066 | FAIL×3 |

**三条可复用的形状知识**：
1. **`group_scale` > `group_zscore`**（同内核同设置，1.00 vs 0.90）——
   group_scale 把值压到 0~1 区间，**天然有界、不产生极端离群权重**；
   group_zscore 会给离群股极大权重。⇒ 外壳排序语义是形状知识，不是玄学。
2. **外壳三层都在贡献，缺一即塌**：剥 decay → 0.24，剥 zscore → 0.23，
   剥 group → 0.79。⇒ 这三层不是"堆复杂度"，是各自承担不同职责
   （decay=平滑换手 / ts_zscore=跨股归一 / group=同业参照系）。
3. **decay 越小越好**（d4 > d10 > d20 > d44），说明该信号**信息衰减快**，
   印证 PEAD 漂移集中在事件后短窗。

#### M20-03 ★ 再证：算子数与 S 无关（"≥8 算子"是编的数字，二次实测）

**台账 360 条【已过门】件**的算子数 × S（本次新算，事实源 = SUBMITTED_LEDGER.csv）：

| 算子数 | n | S 中位 | 算子数 | n | S 中位 |
|---|---|---|---|---|---|
| 0 | 5 | 1.55 | 12 | 12 | 2.50 |
| 3 | 11 | 2.06 | 13 | 13 | 2.44 |
| 4 | 16 | 2.33 | 15 | 15 | 2.38 |
| 5 | 18 | 2.45 | 18 | 14 | 2.39 |
| 7 | 15 | 2.42 | 20 | 12 | 2.24 |
| 8 | 19 | 2.38 | 23 | 5 | 2.55 |
| 9 | 18 | 2.29 | 30 | 1 | 2.77 |
| 10 | 23 | 2.45 | 37 | 1 | 2.22 |

⇒ 全区间 S 中位 2.05~2.55，**无单调性**。过门件里 0 算子的有 5 条、
3 算子的有 11 条、37 算子的也有 1 条。**算子数与 S 无因果关系**。

**台账过门件的外壳分布（新算）**：
| 外壳 | n | 占比 | S 中位 |
|---|---|---|---|
| **group_rank** | **345** | **95.8%** | **2.31** |
| group_scale | 4 | 1.1% | 2.51 |
| group_zscore | 2 | 0.6% | 1.81 |
| 无外壳 | 7 | 1.9% | 1.64 |

⇒ 历史 95.8% 的过门件用 `group_rank` 外壳。李工 11-16 已解禁 group_rank，
  后续外壳轮换应把 group_rank 纳入首选集合（实测 M20-02 里 group_scale 优于 group_zscore，
  但历史池的 group_rank 样本量最大，是下一个必测点）。

#### M20-04 ★ 相关度不是瓶颈（李工 11-16 16:15「现在只看相关度能否够」）

`_grid/corr_gate.py` 对今日全部候选的判定（池 341 条，池组合 Sharpe a=4.1956）：

| alpha | S(自身) | maxCorr | 门槛 ρ* | 结论 |
|---|---|---|---|---|
| A1xgbgJl（M1902_H1_snr_ebit） | 1.072 | **0.3097** | 0.2536 | corr 低但自身 S 不够 |
| RRe2Y1Ez（M1902_H1_snr_eps） | 0.753 | **0.4121** | 0.1777 | 同上 |
| oma39Pwn（MA3_12045） | 0.739 | **0.3793** | 0.1745 | 同上 |
| **O0WbbKvd（MA6_groupzscoregro）** | 0.847 | **0.4083** | 0.2002 | 同上 |

⇒ **maxCorr 0.31~0.41，全部远低于平台线 0.70** ⇒ 相关度这一关已过，
  瓶颈 100% 在 S。平台 `/alphas/{id}/correlations/prod|self` 端点返 200 空 body
  （与既往记录一致），判定只能靠 `/check` + 本地 corr_gate（本地与平台差 0.007）。

#### M20-05 内核归因批（`_grid/batch_1116j_m19_core.json`，15 条，1116 17:35 发）

外壳统一用 M20-02 胜出的 `group_scale(ts_decay_linear(ts_zscore(K,120),10),subindustry)`，
settings 全同（TOP3000/SUBINDUSTRY/decay10/trunc0.08）⇒ 唯一变量是内核。

| 组 | 检验 | cid |
|---|---|---|
| A 裸内核 | 惊喜水平 / 分歧 / 信噪比 / 惊喜zscore 各自裸跑 | A1~A4 |
| B 形状假设 | H1 当期比值 / H2 分歧当否决项 / H2 极端(不含分歧) / H3 增量 | B1~B4 |
| C 窗口扫描 | ts_mean 窗口 30 / 120 / 250 | C1~C3 |
| D 论文维度 | **Guo 2019 惊喜新鲜度**（`days_from_last_change`）乘法 / 加法 | D1~D2 |
| E 跨科目 | EPS信噪比 − Sales信噪比 / 二者之比 | E1~E2 |

**D 组 = Guo 2019（"Underreaction, Overreaction, and Dynamic Autocorrelation of Stock Returns"）
的机制落地**：美国月度收益 2/3 时间与过去正相关、1/3 负相关；
投资者**看不到盈利新闻自相关结构的时变性** ⇒ 财报季前半年盈利新闻自相关下降
⇒ 投资者把新近新闻与旧新闻混淆 ⇒ **overreact** ⇒ 下期负收益。
⇒ 决定方向的是惊喜的**"新旧程度"**，不只水平。
analyst7 的 surprise 字段在两次财报更新之间为常数 ⇒ `days_from_last_change` 正好量化新鲜度。

★ 修正一处错误：原方案里的 `act_q_eps_surprisenum` **在 fields_usa_meta.json 中不存在**
（act_q_eps 只有 surprisemean / surprisestd 两个 surprise 字段）⇒ 会 HTTP400，已删该条。

---

### M22（1116 17:50~18:30）★★ 画瓢路线：从论坛现成模板出（李工 16:45 纠正后）

**李工纠正**：「idea 为什么这么困难？别人都有代码啊，你照着画瓢，微调下，就可以提交了，
现在直接放弃idea」⇒ 我 16:00~16:45 在从零手写表达式，把简单的事做难了。

#### M22-01 现成代码在哪（本地存档，事实源）
| 来源 | 位置 | 内容 |
|---|---|---|
| **ATOM 主帖官方 4 模板** | `docs/forum/atom_pack/post_main.txt` L138-147 | `group_rank(ts_mean(F,20)/ts_mean(F,120),subindustry)` / `group_neutralize(ts_zscore(F,60),subindustry)` / `ts_decay_linear(-ts_rank(F,252),10)` / `group_rank(ts_delta(F,20)/ts_std_dev(F,60),sector)`；作者原话「100% 纯血统单数据集 ATOM 模板」「经过实战检验」；官方设置 USA/TOP3000/decay=6/SUBINDUSTRY/trunc=0.08 |
| **AI 工作流帖已验证模式** | `refs/post_39925324948119_*.txt` L52, L245-248 | `rank(anl4_afv4_eps_number)*rank(ts_rank(anl4_afv4_eps_mean/close,40))`（作者实测提交 7 条，最高 S=1.92/F=1.50）；「已验证有效的模式」4 条 |
| **官方选字段秘诀** | 同上 L124-136 | 「按 onboard 时间 dateCreated 由近到远降序 + alphaCount 由低到高升序」+ coverage>=0.80 |

#### M22-02 ★★ 形状 > 字段（同一批实测，最重要的一条）
蓝海字段（alphaCount=0，2026-04-01 最新 onboard）× 官方 4 模板，同一批内对照：

| 字段 | T1(均值比) | T2(ts_zscore+行业中性) | T3(分位均值回归) | T4(差分/波动) | 极差 |
|---|---|---|---|---|---|
| analyst_ebitda_diffusion_fy1_3m | **+0.84** | **-0.21** | +0.36 | +0.67 | **1.05** |
| analyst_ebitda_revision_ntm_1m | +0.68 | **-0.67** | +0.61 | +0.52 | **1.35** |
| analyst_revenue_revision_fy1_3m | +0.56 | +0.15 | — | +0.67 | 0.52 |

⇒ **同一个字段换模板，S 差 1.05~1.35**；而不同字段在同一模板下只差 0.1~0.3。
⇒ **形状（模板）是 S 的主因，字段是次因**。这正是李工"照着画瓢，微调下"的实证依据。

**T1（长短周期均值比）在 3 个字段上都排第一/第二** ⇒ 现成模板本身是有效的，
问题在**字段与模板的配对**，不在模板本身。

#### M22-03 ★ 踩坑：官方模板不能套「已聚合字段」
`analyst_ebitda_diffusion_fy1_3m` 平台 description：
"Diffusion ratio (upward vs downward) of analyst revisions for next fiscal year (FY1) EBITDA forecast, calculated over the past 3 months"
⇒ 它**本身就是比率、且已经聚合过 3 个月**。再套 `ts_mean(20)/ts_mean(120)`
= 把已算好的边际变化再平滑一次 ⇒ 信号被抹平 ⇒ S 只剩 0.84。

**分档判据**：
| 字段原生形态 | 适配模板 | 不适配 |
|---|---|---|
| 原始累计型（assets / eps_mean / 余额） | T1 均值比 / T4 差分比 | — |
| **已聚合比率型**（diffusion / ratio / beta / mad / nums） | **T3 分位均值回归 / 最小干预外壳** | **T1 均值比（会抹平）** |
| **已变化率型**（revision_ntm_1m / *_chg） | **T3 / 最小干预外壳** | T1 / T4（重复差分） |

⇒ 新工具 `_grid/forum_templates.py --native` 会按字段名关键词
（diffusion/revision/nums/ratio/mad/beta/change/score）自动跳过朴素模板。

#### M22-04 ★★ ATOM 门误杀新字段（已修，代码级）
**现象**：原生批 50 条被 ATOM 门拦掉 10 条，报「无法判定数据集归属的字段: beta_ray_250d」。
**根因**：平台 `GET /data-fields` 一次只返 **10000 条**（分页上限），
本地 `fields_usa_meta.json` 也是 10000 条 ⇒ **最新 onboard 的字段查不到归属**
⇒ 唯一硬拦门误杀（`beta_ray_250d`/`beta_gld_250d` 平台真值都是 pv20，alphaCount=0/1）。

**修复**（`src/core/atom.py`）：`dataset_of()` 加**平台定点查询兜底**
（`GET /data-fields?search=<字段>`，命中就写回本地权威表），
⇒ 以后新字段不会因缓存缺口被误杀。已实测 `beta_ray_250d → pv20`、
`close → pv1`、`assets → fundamental6`。

#### M22-05 历史遗留件：自有件全死，但【他人件是最大的 idea 库】★
扫全池 mined：
- **8267 个**「checks 无 FAIL + S≥1.58 + F≥1.0 + 未入台账」⇒ 其中 **7830 个是他人公开 alpha**
- **437 个是自有的** ⇒ 按 ATOM 筛出 166 个（analyst4 144 / fundamental2 22）
  ⇒ ★ 但 corr_gate 实测 30 个候选全部 FAIL：maxCorr **0.75~1.00**
  （最像的都是池内已收录的 `d516QO9v` / `pwRwWoJ3` / `e79PvPpE`）
  ⇒ **自有历史件这条路封死，不要再翻**。

> ★★ **勘误（11-16 17:40 李工纠正）**：上面把"他人件不可提交"直接写成了"这条路封死"，
> **这是错的**。他人 alpha **不能原样提交**（它们在生产池里，PROD corr ≈ 1.0），
> **但它们是最大的现成 idea + 代码库** ⇒ 正确用法是
> **「拿别人的想法 → 换冷门数据集/低使用字段重新实现 → 微调」**。
> ⇒ 全量 15129 条（作者 LJ49886）里，**197 条是 ATOM 单数据集 + checks 无 FAIL + S≥1.58 + F≥1.0**
> 的高质量件，**其中 ai_equity_alpha（池内 0 条）/ analyst_consensus（池内 0 条）是最佳落点**。
> ⇒ 见 M24。

---

### M24（1116 17:40~）★★★ 别人的 idea + 自己实现 + corr 优先（李工 17:40 纠正后）

**李工原话**：
> 「下载的 idea 我感觉也不全，很多 idea 有给代码，或者表达式，我们需要实现别人的想法，
> 然后微调这样能够通过平台的门槛就可以了，这个时候最需要考虑的是相关度的问题。
> 你实现了不一定能提交，因为相关度可能大于 0.7，
> 如果你其他的指标都无法通过，那只能说明你的表达式不对，
> 我不知道你在做什么，貌似一直像以前那样套旧壳」

#### M24-01 ★★★ 三条硬规则（覆盖此前所有"自己造 idea / 套模板"的做法）

| 规则 | 内容 | 依据 |
|---|---|---|
| **R1** | **想法必须来自别人已验证的表达式**（本地库 15129 条 / 论坛存档帖），**不自编 idea** | 「很多 idea 有给代码，或者表达式」 |
| **R2** | **不照抄别人表达式**——别人已提交的 alpha 在生产池里，照抄 PROD corr ≈ 1.0 必死 ⇒ 做法是**拿同一想法的因子换冷门数据集重新实现 + 微调** | 「你实现了不一定能提交，因为相关度可能大于 0.7」 |
| **R3** | **corr 是第一筛子，不是最后一步**：池内占用高的数据集直接放弃；别人用过的字段变体（alphaCount 高）也避开；优先「池内 0 条 + 平台 alphaCount 低」 | 「这个时候最需要考虑的是相关度的问题」 |

**★ 判据反转（李工 17:40 重申）**：
「如果你其他的指标都无法通过，那只能说明你的表达式不对」
⇒ S/F/TO 过不了门 ⇒ **不是 idea 不行、不是数据集不行、不是"这条没用"**，而是**表达式写错了**。
⇒ 动作 = **换实现方式 / 微调外壳**，不是丢弃想法。

#### M24-02 ★ 旧壳出不了货（实测证据，两批全灭）

| 批 | 做法 | 条数 | 最高 S | FAIL≥3 条数 |
|---|---|---|---|---|
| 1116m 原生批 | 最小干预外壳 × 蓝海字段 | 17/50 | **0.78** | 17/17 |
| 1116n 论坛模板批 | 官方 5 模板 × 蓝海字段 | 19/110 | **1.03**（唯一 FAIL=0） | 18/19 |
| 1116l 蓝海批 | 官方 4 模板 × alphaCount=0 字段 | 20/20 | 1.03 | — |
⇒ **全部复用 11 月初的老外壳（`group_rank(ts_mean/ts_delta(ts_zscore(...)))`）⇒ S 全部卡在 1.0 以下**
⇒ 证实李工判断：**「貌似一直像以前那样套旧壳」**。
⇒ 破局点不是"再调外壳"，而是**换想法来源（别人的已验证 idea）+ 换数据集（池内 0 条）+ 换外壳家族**。

#### M24-03 ★ 平台算好的 alpha 因子分 = 最理想的"别人的想法"（ai_equity_alpha）

**为什么它是最佳落点**（全部实测）：
| 条件 | ai_equity_alpha 实测 |
|---|---|
| 池内占用 | **0 条**（台账 360 条里一个都没有）|
| 平台 alphaCount（= 全网用得少 ⇒ PROD corr 天然低）| 43 个字段中 **多数 0~8**，最高 34 |
| pyramid 倍率 | **1.3**（平台鼓励方向，VF 加成）|
| 覆盖率 | 0.91 |
| 想法成熟度 | **平台自己算好的因子分**（应计质量/资产减值风险/商业模式透明度/分析师情绪/修正动量/覆盖广度/预测准确度/资产效率/分歧度）|

**43 个因子按经济含义分 10 组**（每组 = 一个独立的 idea）：
`accrual_quality`(3) / `impairment_risk`(5) / `opacity_governance`(4) /
`analyst_sentiment`(12) / `analyst_revision`(6) / `analyst_coverage`(4) /
`surprise_quality`(3) / `forecast_accuracy`(1) / `asset_efficiency`(4) / `dispersion`(1)

**实现方式（微调维度）**：
- 外壳取自**别人已验证件**：`zscore(group_rank(ts_delta(F,22),g))`（别人 ai_equity_alpha 上 S=2.55）、
  `ts_rank(ts_delta(F,60),120)`（别人 analyst4 上 S=1.65）、双因子等权合成
- 微调轴：**分组**（industry/subindustry/sector/market）× **归一**（zscore/rank/group_zscore/group_scale）× **窗口**（22/60/120）
- 字段选法：**同族内 alphaCount 最低的** ⇒ 与生产池里用过的变体天然错开 ⇒ corr 低
- 批规模：66 条（10 组 × [单因子×4 分组 + 双因子×2 + 趋势腿]），ATOM 门 66/66 PASS

#### M24-04 ★ 别人库里可直接用的 197 条（ATOM 单集 + 无 FAIL + S≥1.58 + F≥1.0）

| dataset | n | S 中位 | max | 我方池占用 |
|---|---|---|---|---|
| **option8** | 96 | 1.92 | 2.27 | 1 条 |
| fundamental6 | 58 | 1.84 | 2.46 | 8 条 |
| pv1 | 16 | 2.01 | 2.22 | 5 条 |
| **analyst_consensus** | 10 | 1.75 | 1.80 | **0 条** ✅ |
| **ai_equity_alpha** | 9 | 1.92 | **2.55** | **0 条** ✅ |
| analyst4 | 7 | 1.84 | 1.85 | 0 条（但池内 anl4 件 111 条是混集）|
| model51 | 1 | 1.86 | 1.86 | **0 条** ✅ |

**最好的一条**：`akaZMqW5` S=2.55 F=2.18 tS=1.98
`zscore(group_rank(vec_avg(accruals_analysis_factor_10), industry))`
（ai_equity_alpha 的 **VECTOR** 因子，需 `vec_avg`；`accruals_analysis_factor_10` alphaCount=45）
⇒ ★ **不能照抄**（已在生产池），但**"用应计分析因子做行业中性截面排序"这个想法是对的**，
可用 MATRIX 版 `accruals_intensity_score_2` 重新实现（alphaCount=4）。

#### M24-05 corr 的三层预筛（提交前就要做，不是提交后）

1. **数据集层**：池内占用 > 0 的高占比数据集直接放弃（fundamental6 48% / analyst4 111 条混集 / pv1）
2. **字段层**：平台 `alphaCount` 低的字段优先（用得少 ⇒ 生产池里同形状少 ⇒ PROD corr 低）
   —— 这条比"冷门数据集"更强：字段级才是 corr 的实际载体
3. **表达式层**：不照抄别人已提交的表达式（必然 corr≈1）；改实现方式（外壳/分组/窗口）即可错开

**★ 平台 corr 免费预检的边界（实测）**：
- `GET /alphas/{id}/check` **只对自己的 alpha 有效**；对他人 alpha 返空 body / PENDING
  （实测 `akaZMqW5` 解析失败、`MPYJEl99` 三轮 checks=0）
- `GET /alphas/{id}/correlations/prod` 与 `/self` **都返空 body**（与既往记录一致）
⇒ **corr 只能在模拟出自己的 alpha 之后查**（本地 `corr_gate.py` 与平台差 0.007，可先本地筛）
⇒ ⇒ **流程必须是：先按上面三层预筛 → 模拟 → 再查 corr**

---

### M25/M26（1116 17:58~）★★★ 突破：实现别人的想法 + 换科目/换度量 = 今日首个过门族

**起点（别人已验证）**：`kqa5NXq6` S=1.80 F=2.02
`group_rank(ts_std_dev(vec_avg(actual_value_eps_annual12),60) - ts_std_dev(vec_avg(actual_value_fxadj_eps_annual12),60), sector)`
（数据集 `analyst_consensus`，池内 **0 条**；`actual_value_fxadj_eps_annual12` 的 alphaCount=**0**）

**机制（idea）**：原始报表口径 EPS 与**汇率调整口径** EPS 的差异 = 该股的**外汇敞口** ⇒
汇率波动放大盈利波动 ⇒ 定价错误 ⇒ 下期收益。池内 0 条用过，全网用得也少 ⇒ corr 天然低。

#### M25-01 ★ 微调轴（合法轴 = 改参数，不改 idea）
| 轴 | 取值 | 实测效果 |
|---|---|---|
| 科目 | EPS 年度 / EPS 季度 / EBIT 年度 / EBI 年度 / EBI 季度 | 季度 EPS 最高 S=1.94 |
| 窗口 | 20 / 60 / 120 | **越长 corr 越低**（w20→0.74, w60→0.67, w120→?）|
| 分组 | industry / subindustry / sector / **market** | **market 最低 corr（0.6403）** |
| 度量 | ts_std_dev / **ts_av_diff** / ts_delta / ts_mean | **ts_av_diff 降 corr 最多（0.6767）** |
| universe | TOP3000 / TOP2000 / TOP1000 / TOP500 | TOP3000→TOP500 是唯一实测能独立降 corr 的杠杆 |

#### M25-02 ★★ 实测结果（第一批 S≥1.58 且 checks 无 FAIL 的族）
| cid | 形状 | S | F | tS | TO | FAIL | maxCorr |
|---|---|---|---|---|---|---|---|
| M25_eps_quarter_w20_sector | 季度EPS·std_dev差·sector | 1.85 | 1.88 | 0.72 | 0.022 | **0** | 0.7178 |
| M25_eps_annual_w20_market | 年度EPS·std_dev差·market | 1.89 | 2.05 | 1.79 | 0.026 | **0** | 0.7434 |
| M25_eps_annual_w20_industry | 年度EPS·std_dev差·industry | 1.85 | 2.04 | 1.86 | 0.024 | **0** | 0.7497 |
| M25_eps_annual_w60_industry | 同上 w60 | 1.81 | 1.94 | 1.09 | 0.020 | **0** | 0.7139 |
| M25_eps_annual_w60_subindustry | 同上 w60 | 1.83 | 1.80 | 1.09 | 0.023 | 1 | **0.6713** ✅ |
| M25_eps_annual_w60_sector | 同上 w60 | 1.79 | 2.00 | 1.27 | 0.017 | **0** | 0.7036 |
| **M25_eps_quarter_w20_market** | 季度EPS·market | 1.94 | 1.86 | 0.46 | 0.029 | 1 | **0.6403** ✅ |
| M25b_eps_annual_D1_industry | **ts_av_diff 差·industry** | 1.89 | 1.87 | 1.05 | 0.021 | **0** | 0.7070 |
| **M25b_eps_annual_D1_subindustry** | **ts_av_diff 差·subind** | 1.90 | 1.75 | 0.73 | 0.022 | 1 | **0.6767** ✅ |
| M25b_eps_annual_D2_subindustry | ts_delta 差·subind | 1.79 | 1.77 | 1.22 | 0.021 | **0** | 0.7448 |

#### M25-03 ★★ corr 墙的真实原因（诊断，不是猜）
`corr_top.py` 查 top-8 最像件 ⇒ **全部撞同一个池内件 `Vk08lZMb`**（0.64~0.76）：
`1.3*group_rank(ts_delta(cashflow_op,252)/cap, industry) + 1.1*group_rank(ts_delta(fnd6_mfma2_revt,252)/assets, industry) + 2.2*group_rank(-(ebit-cashflow_op)/assets, industry) + ...`
（fundamental6 五腿混集）
⇒ **撞的不是数据集，是共同的「低波动 + 盈利质量」因子**
⇒ 破局手段（实测有效）：**换度量方式**（std_dev → av_diff）+ **换分组**（→ market）+ **拉长窗口**
⇒ ⚠ **换数据集没用**（池内 fundamental6/pv1/option8 都有同族件）

#### M25-04 ★ 两个临界件各差一口气（下一步的靶）
| 件 | 过门项 | 卡住项 |
|---|---|---|
| `YPa2xM3l` M25_eps_quarter_w20_market | S=1.94 F=1.86 | LOW_SUB_UNIVERSE_SHARPE=0.80（限 0.84）**corr 0.6403 ✅** |
| `3q0ajb9Z` M25b_eps_annual_D1_subindustry | corr 0.6767 ✅ | LOW_SUB_UNIVERSE_SHARPE=0.81（限 0.82） |
| `1YWajJvk` M25_eps_quarter_w20_sector | FAIL=0 ✅ | corr 0.7178（最像 qM0E2Ee2） |
| `rK7Jen08` M25b_eps_annual_D1_industry | FAIL=0 ✅ | corr 0.7070（差 0.007） |

⇒ **分组轴（管 corr）与中性化轴（管 subuniverse_sharpe）相互独立**
⇒ M28 定向：分组 market/sector/subindustry × 中性化 MARKET/NONE/INDUSTRY × 窗口 20/30/45
   × universe TOP3000/TOP2000/TOP1000（110 条）

#### M25-05 ★★ 微调的合法轴 vs 非法轴（李工 17:58 的实证）
**合法（改参数）**：窗口 / 分组 / 归一 / 平滑 / 设置层 / **度量方式**
**非法（改想法）**：换字段族、换数据集
★ **反面教材（M24b）**：把别人验证的 VECTOR 字段 `accruals_analysis_factor_10`
  换成 MATRIX 变体 `accruals_intensity_score_2` ⇒ **S 从 2.55 掉到 0.63**
  ⇒ **微调 ≠ 换字段**
★ **另一个反面教材**：给已聚合的因子分加 `ts_delta` ⇒ 信号被抹平（S=0.46, TO=0.0116）
  ⇒ 时序层不是"复杂度"，加错层会直接毁信号

#### M25-06 ★★ corr 与 subuniverse_sharpe 的双约束（12 条过门件实测）
**当前 12 条 checks 无 FAIL 的件，corr 全部 0.70~0.76**（本地 corr_gate，与平台差 0.007）：
| id | 形状 | S | maxCorr | 卡在哪 |
|---|---|---|---|---|
| `zqdPbvbO` | 年度EPS·std_dev差·market | 1.89 | 0.7434 | corr |
| `rK7JR0a9` | 年度EPS·ts_rank差·industry | 1.90 | 0.7477 | corr |
| `GrmMOqpx` | 年度EPS·std_dev差·industry | 1.85 | 0.7497 | corr |
| `j2a9eRVe` | 年度EPS·ts_delta差·industry | 1.74 | 0.7606 | corr |
| `npaZANKE` | 年度EPS·ts_delta差·subind | 1.79 | 0.7448 | corr |
| `1YWajJvk` | 季度EPS·std_dev差·sector | 1.85 | 0.7178 | corr（最像 qM0E2Ee2）|
| `rK7Jen08` | 年度EPS·av_diff差·industry | 1.89 | 0.7070 | corr（差 0.007）|
| `xAvPrlrw` | — | 1.54 | 0.7091 | corr |
| `O0Wb8bq7` | 年度EPS·std_dev差·sector w60 | 1.79 | 0.7036 | corr |
| `ZYa2AA1d` | 年度EPS·std_dev差·industry w60 | 1.81 | 0.7139 | corr |
| `ZYa2Qb68` | — | 1.55 | 0.7422 | corr |
| `KPgXNELp` | 年度EPS·std_dev差·sector w20 | 1.80 | 0.7213 | corr |

**★ 第二道墙（同样重要）**：`LOW_SUB_UNIVERSE_SHARPE`
- 池内 341 条过门件的 subuniverse sharpe **中位 1.49~1.60**（最高 2.71）
- **我的件只有 0.73~0.81** ⇒ 差一个数量级的"域内一致性"
- 规律：**分组越粗 ⇒ subuniverse 越低**（market 分组 0.73 / industry 0.76 / sector 0.80 / subindustry 0.81）
- 规律：**中性化 SUBINDUSTRY 的池内件占 273/341** ⇒ 池子主流是细域中性化

**⇒ 双约束互相拉扯**：
| 想要 | 轴 | 代价 |
|---|---|---|
| corr < 0.70 | 分组粗（market）+ 度量换（av_diff/D4）+ 窗口长 | ⇒ subuniverse 掉到 0.73~0.81 ⇒ 撞 LOW_SUB_UNIVERSE_SHARPE |
| subuniverse 过线 | 分组细（subindustry）+ SUBINDUSTRY 中性化 | ⇒ corr 回升到 0.67~0.74（仍接近线）|

**⇒ M29 定向批（150 条）**：分组 {subindustry, industry} + 中性化 SUBINDUSTRY
+ universe {TOP3000, TOP2000, TOP1000, TOP500}（小 universe 提 subuniverse）
+ 度量 {D1 av_diff, D4 std_dev比, D6 ts_rank差, D7 比值差} + 窗口 {20,45,60,90,120}

#### M25-07 ★★ 换 idea 路线（避开同一因子）：option8 期权偏斜族
**他人库 197 条可用件按机制族**：期权波动率偏斜 **96 条**（S 中位 1.93）/ 盈利质量 38 / 估值比率 24 /
动量 17 / 风险波动 10 / 预期修正 6 / 其他 6。
★ **option8 池内只占 1 条**（QPK3n9Zw），但那一条已用 **90 日期限 + industry**
⇒ **换期限（10/20/45/150）+ 换度量（差/比/变化）+ 换分组** ⇒ 同想法不同实现 ⇒ corr 低
⇒ M30 批 90 条（3 度量 × 6 期限 × 4 分组 + 6 组期限结构对）
