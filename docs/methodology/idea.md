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

统计：已跑 221（1011 腿库线 58 条 + lc19z 9 条 + lc20m 26 条 + lc20n T500 8 条并入）

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

**本轮结论（写死，不再重复踩）**

1. **母件设定必须原样继承**（见 atoms.md D-34）。套 MARKET+decay40 会把 SF 6.19 打成 1.93。
2. **decay 4 是本族甜点**：tS 从 1.48 抬到 2.01，SF 只掉 0.3，TO 仍在 16% 内。
3. **死因是 S 不是 corr**：need 被池里 S=3.45 的 `0mR2K6lr` 顶到 3.795，本批 S 封顶 3.11。**先量 need 再提 S**。
4. **经济新腿本身不是主腿**：`systematic_risk_*` / `fscore_bfl_*` / `composite_factor_score_derivative` 裸信号 SF≤2.9，只能当佐腿（权重 0.6）。这条 1009 已实测确认。
5. **最优先复活项**：`QPKOlw8X`（f15b_d14_27）只差 0.248，且超 0.66 对手仅 8 个——池子一变就能过。
