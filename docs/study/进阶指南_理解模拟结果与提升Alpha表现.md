# BRAIN 进阶指南：理解模拟结果与提升 Alpha 表现

> 来源：BRAIN 官方进阶教程（Advance Guide）。目标：加深对已模拟 Alpha 的理解，掌握常用算子，提升创造高性能 Alpha 的能力。
> 阅读前提：已了解 Simulation Settings 与 Fast Expression 基础语法。

---

## 一、理解你的模拟结果

### 1.1 累计 PnL 图表长什么样才合格？

下面三张图是官方给出的典型对比：

![PnL 对比：前两张波动大、有显著亏损期；第三张稳步上升、回撤小](./docs/images/pnl_comparison_good_bad.png)

- **左边两张（不合格）**：PnL 曲线上有多个显著亏损的时段，波动很大，意味着组合可能在一天内损失较大比例的价值。
- **下方一张（好 Alpha）**：曲线稳步上升，波动小、回撤小，是理想形态。

**一句话总结**：好的 Alpha 不是收益最高，而是收益曲线最稳、回撤最小。

---

## 二、IS 摘要六指标详解

回测完成后，IS Summary 会给出 6 项核心指标。下图为一个典型的 **Needs Improvement** 示例：

![IS Summary Needs Improvement 示例：Sharpe 1.55、Turnover 53.92%、Fitness 0.71、Returns 11.20%、Drawdown 2.58%、Margin 41.50‱](./docs/images/is_summary_needs_improvement_2.png)

| 指标 | 含义 | 通过门槛 | 优化方向 |
|---|---|---|---|
| **Sharpe Ratio** | 单位风险带来的超额收益，衡量一致性 | Delay 1 > 1.25；Delay 0 > 2.0 | 提高 PnL 均值，降低 PnL 标准差 |
| **Turnover** | 每日交易活跃度 = 交易金额 / book size | 1% ~ 70% 之间 | 过高用 decay、hump、时间序列平滑；过低说明信号太呆滞 |
| **Fitness** | Sharpe、Returns、Turnover 的综合函数 | Delay 1 > 1.0；Delay 0 > 1.5 | 提高 Sharpe/Returns，降低 Turnover |
| **Returns** | 年化收益占 book size 一半的百分比 | 越高越好（配合 Sharpe 看） | 增强信号强度 |
| **Drawdown** | 最大回撤百分比 | 越小越好 | 控制单只权重、加 rank/截断 |
| **Margin** | 每交易 1 美元产生的利润 | 越高越好 | 提升收益同时别过度交易 |

### 2.1 Sharpe Ratio

衡量 Alpha 每单位收益波动所带来的超额回报。它等于 PnL 均值除以 PnL 标准差。

![Sharpe = sqrt(252) * Mean(PnL) / Stdev(PnL)](./docs/images/sharpe_formula.png)

- Sharpe / IR 越高，Alpha 收益越稳定。
- **考试重点**：BRAIN 的 Sharpe 是 IR 的年化版本，不是传统意义上的无风险利率调整夏普。

### 2.2 Turnover（换手率）

衡量 Alpha 每天交易的频繁程度。

![Turnover = DollarTradingValue / Booksize](./docs/images/turnover_formula.png)

- 换手率高 = 交易频繁 = 成本高。
- 一般通过引入 decay、hump、ts_decay_linear 等算子降低 Turnover。
- 但 Turnover 也不能低于 1%，否则说明信号几乎不交易，缺乏活力。

### 2.3 Fitness（适应度）

Fitness 是 Returns、Turnover 和 Sharpe 的综合函数。

![Fitness = Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) )](./docs/images/fitness_formula_2.png)

- 分子是 Sharpe × |Returns|，分母是 Turnover（最小 0.125 防止除零）。
- 想提升 Fitness：**提高 Sharpe 或 Returns，同时降低 Turnover**。
- 改善一个因素往往会影响另一个因素，需要反复调试。

### 2.4 Returns（回报率）

特定期间内赚取或亏损的金额，以百分比表示。

![Annual Return = Annualized PnL / (0.5 * BookSize)](./docs/images/annual_return_formula.png)

- 注意：book size 固定 2000 万美元，所以分母是 1000 万美元。

### 2.5 Drawdown（回撤）

一段时间内 PnL 的最大减少幅度。

![Drawdown = LargestPeakToTroughGap / (0.5 * BookSize)](./docs/images/drawdown_formula.png)

- 回撤大说明曲线波动剧烈，抗风险能力差。
- 常见控制方法：truncation 0.05–0.1、rank 归一化、限制单只权重。

### 2.6 Margin（保证金）

每交易 1 美元所产生的利润。

![Margin = PnL / TotalDollarsTraded](./docs/images/margin_formula.png)

- Margin 越高，说明每次交易带来的净利润越多。
- 它和 Turnover 一起看：如果 Turnover 高但 Margin 低，说明在频繁交易中赚不到钱。

---

## 三、通过 IS 阶段与故障排查

### 3.1 最常见挑战：Sharpe 太低

下图为典型的 IS Testing Status 失败界面：

![IS Testing Status：2 FAIL（Sharpe 0.18 < 1.58；Fitness 0.06 < 1）+ 4 PASS](./docs/images/is_testing_status.png)

**症状**：Sharpe 低于最低门槛。

**解决思路**：
- 提高 Alpha 收益：增强信号强度、用更有预测力的数据字段。
- 降低波动率：加 rank/group_rank 归一化、用 decay 平滑、加中性化。

### 3.2 权重测试失败

**错误提示示例**：
- "单个工具的最大权重超过 10%"
- "权重过于集中"
- "被分配权重的工具过少"

**常见解决方案**：
1. 加 `rank` 等范围归一化函数，把原始值映射到 0–1 均匀分布。
2. 设置 **Truncation = 0.1**（单只股票最大权重 10%）。
3. 使用 `ts_backfill` 处理缺失值，提高覆盖率。
4. 多空数量不平衡时，用 `kth_element` 补齐。

### 3.3 子宇宙 Sharpe 未达标

子宇宙（Sub-universe）Sharpe 需要在不同股票子集里也都表现稳健。平台会按子宇宙规模动态降低门槛，但仍需超过阈值。

![Sub-universe Sharpe 阈值公式](./docs/images/subuniverse_sharpe_thresholds.png)

**解决思路**：
- 扩大 Universe，选择 **Top3000** 而非更小的池子，增加样本量。
- 让 Alpha 在不同 sector / industry 都有信号覆盖，避免只在少数股票上有效。
- 加 Market / Industry 中性化，降低行业集中度风险。

---

## 四、常见错误消息

### 4.1 "表达式中的语法错误"

- 检查数据字段和算子拼写是否正确。
- 确认表达式逻辑成立，括号匹配，参数数量正确。
- 参考 **Available Operators** 和 **Available Data** 页面。

### 4.2 "输入索引 0 的单位不兼容，预期为 Unit[]，实际为 Unit[CSPrice:1]"

- 这是**单位警告**，在简单情况下仅作参考，不会阻止提交。
- 典型触发：把不同单位的数据字段相加/相乘，例如 `close + cap`（close 是价格，cap 是价格×股数）。
- 如果你确认 Alpha 逻辑能正确处理单位，可以直接忽略。

---

## 五、大白话总结

1. **好 Alpha 的标准形态**：PnL 曲线像楼梯一样稳步往上走，而不是心电图一样大起大落。
2. **IS 六指标口诀**：夏普要高、换手要稳、Fitness 要过、收益要正、回撤要小、Margin 要高。
3. **Fitness 提升公式**：高 Sharpe + 高 Returns + 低 Turnover = 高 Fitness。
4. **失败三板斧**：
   - Sharpe 低 → 增强信号 / 降低波动。
   - 权重集中 → 加 rank / truncation / ts_backfill。
   - 子宇宙 Sharpe 低 → 扩大 Universe / 加强中性化。
5. **单位警告不等于错误**：只要逻辑自洽，可忽略。

---

## 六、考试速查卡

| 考点 | 标准答案 |
|---|---|
| IS 摘要包含哪 6 项指标？ | Sharpe、Turnover、Fitness、Returns、Drawdown、Margin |
| Delay 1 Alpha 的 Sharpe 通过门槛？ | > 1.25 |
| Delay 0 Alpha 的 Sharpe 通过门槛？ | > 2.0 |
| Turnover 合理区间？ | 1% ~ 70% |
| Fitness 公式核心？ | `Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) )` |
| 降低 Turnover 常用算子？ | `decay`、`hump`、`ts_decay_linear` |
| 控制权重集中常用方法？ | `rank`、`truncation=0.1`、`ts_backfill` |
| 子宇宙 Sharpe 不达标怎么办？ | 扩大 Universe 到 Top3000、加中性化 |
| 单位警告是否阻止提交？ | 不会，仅作参考 |
| Returns / Drawdown 分母为什么是 0.5*BookSize？ | BookSize=2000万，本金按1000万计算，杠杆2倍 |

---

## 七、配套图片清单

| 图片 | 说明 |
|---|---|
| `pnl_comparison_good_bad.png` | PnL 曲线好/差对比 |
| `is_summary_needs_improvement_2.png` | IS Summary 示例 |
| `sharpe_formula.png` | Sharpe 公式 |
| `turnover_formula.png` | Turnover 公式 |
| `fitness_formula_2.png` | Fitness 公式 |
| `annual_return_formula.png` | Annual Return 公式 |
| `drawdown_formula.png` | Drawdown 公式 |
| `margin_formula.png` | Margin 公式 |
| `is_testing_status.png` | IS Testing Status 失败示例 |
| `subuniverse_sharpe_thresholds.png` | 子宇宙 Sharpe 阈值公式 |
