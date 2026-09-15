# BRAIN 回测结果指标与 Alpha 状态

> 来源：BRAIN 官方结果页指标说明。掌握 Stats 标签页、IS Summary、评级、IR/Sharpe/Fitness、相关性、IS/OS 划分、Alpha 生命周期等核心概念。

---

## 一、Alpha 评级面板（Fitness Rating）

在 Simulation Results → Stats 标签页中，BRAIN 根据 Alpha 的 **Fitness** 给出评级：

![评级面板](docs/images/rating_panel.png)

![Fitness 评级阈值表](docs/images/fitness_rating_thresholds.png)

| 评级（中文） | 评级（英文） | Fitness for Delay 1 | Fitness for Delay 0 |
|---|---|---|---|
| **卓越** | Spectacular | > 2.5 | > 3.25 |
| 优秀 | Excellent | > 2.0 | > 2.6 |
| 良好 | Good | > 1.5 | > 1.95 |
| 平均 | Average | > 1.0 | > 1.3 |
| 需要改进 | Needs Improvement | <= 1.0 | <= 1.3 |

> 一句话理解：**Fitness 是连续数值，Average / Excellent 等是平台按数值区间贴的等级标签**，就像"90 分 = 优秀"。"至少达到 Average" = 数值必须跨过该档门槛：D0 > 1.3，D1 > 1.0。

> 考试重点：Delay 0 的阈值高于 Delay 1，因为 Delay 0 可用信息更及时、理应更难（同等级 D0 门槛约为 D1 的 1.3 倍）。

---

## 二、Return（收益）

Return 是某一时期内证券或投资组合的收益或亏损，由收入 + 资本利得构成。

在 BRAIN 中：

```
Return = 年化 PnL / (book size 的一半)
```

即：

```
Annual Return = 年化 PnL / (book size / 2)
```

> book size 固定为 2000 万美元；BRAIN 假设你有 1000 万美元本金，最多投资 2000 万美元资产（杠杆 = 2）。指标以 1000 万美元为基础计算。

---

## 三、IR 与 Sharpe

### 信息比率（IR）

IR 衡量模型的预测能力，定义为平均每日 PnL 与每日 PnL 波动率之比：

![IR 公式](docs/images/ir_formula.png)

![IR 公式截图](docs/images/ir_formula_2.png)

```
IR = mean(PnL) / stdev(PnL)
```

### Sharpe（夏普比率）

Sharpe 是 IR 的年化版本：

```
Sharpe = sqrt(252) * IR ≈ 15.8 * IR
```

其中 **252** 是美国一年平均交易日数量。

> IR/Sharpe 越高，Alpha 收益一致性越强。高 Sharpe 比单纯高收益更值得追求。
> 注意：BRAIN 中的 Sharpe/IR 定义可能与教科书略有不同。

---

## 四、Fitness（体能/质量分）

Fitness 是 Returns、Turnover 和 Sharpe 的综合函数：

![Fitness 公式](docs/images/fitness_formula.png)

![Fitness 公式截图](docs/images/fitness_formula_3.png)

```
Fitness = Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) )
```

- 好 Alpha 具有高 Fitness。
- 提升方式：**提高 Sharpe / Returns**，**降低 Turnover**。
- 改善一个因素往往会损害另一个因素，需要在优化中做权衡。

---

## 五、累计盈亏（PnL）图表

累计 PnL 图表显示 Alpha 在整个回测期间的表现。点击右上角下拉菜单可切换到 **Sharpe Ratio 图表**。

![PnL 与最大回撤](docs/images/pnl_drawdown_chart.png)

- 好的 PnL 图：持续上升、波动小、回撤小。
- 波动剧烈（Too many fluctuations）即使收益高，也会被认为不够好。
- **Max Drawdown**：从 PnL 最高点到最低点的最大回撤。

---

## 六、IS Summary 各项指标

![IS Summary](docs/images/is_summary_needs_improvement.png)

![IS Summary 完整年度表](docs/images/is_summary_full_table.png)

| 指标 | 含义 |
|---|---|
| **Year** | 回测年份；最后一行显示所有年份汇总 |
| **Long Count / Short Count** | 每日多头/空头持仓工具数量 |
| **Sharpe** | `IR * sqrt(252)` |
| **Fitness** | `Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) )` |
| **Returns** | `年化 PnL / (book size / 2)`，以百分比表示 |
| **Turnover** | 成交金额 / book size，衡量交易频率 |
| **Margin** | 每交易 1 美元产生的利润 = PnL / 总成交额 |
| **PnL** | 仓位和交易产生的盈亏（美元） |
| **Drawdown** | PnL 从最高点到最低点的最大回撤百分比 |

### PnL 计算细节

```
daily_PnL = 所有工具的 (仓位大小 * daily_return) 之和
daily_return = (今日收盘价 / 昨日收盘价) - 1.0
```

> 收益不会被再投资；亏损会通过向投资组合注资来弥补，因此 book size 在整个回测期间保持恒定。

---

## 七、Self Correlation（自相关性）

点击 Self Correlation 行的 **Down Arrow**，会生成一个表格，展示你提交的、符合 OS 测试资格的 **5 个相关性最高的 Alpha** 的统计信息。

![Self Correlation](docs/images/self_correlation.png)

![Self Correlation 表格](docs/images/self_correlation_table.png)

- 目的：帮助确保你的 Alpha 集合足够**多样化**。
- 如果 Highest Correlation 接近 1，说明这个 Alpha 与已有 Alpha 高度重复，提交价值低。
- 也可在 **Alphas** 页面点击某个 Alpha 访问相关性信息。

---

## 八、IS / Semi-OS / Real OS

![IS / Semi-OS / Real OS 时间线](docs/images/is_semi_os_real_os_timeline.png)

![IS / Semi-OS / Real OS 时间线说明](docs/images/is_semi_os_real_os_timeline_2.png)

| 区间 | 含义 |
|---|---|
| **In Sample（IS）** | 回测可见的历史数据，通常最近 5 年（顾问为 10 年） |
| **Training Period** | IS 内用于开发 Alpha / SuperAlpha 的部分 |
| **Validation Period** | IS 内用于验证 Alpha、检测过拟合的部分 |
| **Semi-OS** | 最近 2 年，隐藏起来用于评分和测试 |
| **Real OS** | 提交后到当前的真实样本外表现 |

- IS 期始于 7 年前，止于 2 年前（滚动更新）。
- 最近 2 年隐藏，可提高对 Alpha OS 表现的信心。
- **My Alphas → OS 标签页** 的统计数据会随每一天新数据可用而逐渐填充。

---

## 九、Alpha 状态生命周期

![Alpha 状态流转](docs/images/alpha_status_flow.png)

![Alpha 状态流转图](docs/images/alpha_status_flow_2.png)

| 状态 | 含义 |
|---|---|
| **UNSUBMITTED** | 回测成功但尚未提交 |
| **ACTIVE** | 已提交，符合 OS 测试资格，开始积累 Weight，可为季度报酬做贡献 |
| **DECOMMISSIONED** | 数据集停用，或 OS 长期表现不佳，被 WorldQuant 停用；不再累积 Weight |

状态流转：

```
Simulate alpha → UNSUBMITTED → Submit Alpha → ACTIVE → (数据停用 / OS 表现不佳) → DECOMMISSIONED
```

> 顾问的 ACTIVE Alpha 才能积累 Weight 并为季度报酬做贡献。

---

## 十、考试速查卡

| 考点 | 标准答案 |
|---|---|
| 评级最高档（英文） | Spectacular |
| Spectacular 阈值 Delay 1 | > 2.5 |
| Spectacular 阈值 Delay 0 | > 3.25 |
| Needs Improvement 阈值 Delay 1 | <= 1.0 |
| Needs Improvement 阈值 Delay 0 | <= 1.3 |
| Return 公式 | 年化 PnL / (book size / 2) |
| IR 公式 | mean(PnL) / stdev(PnL) |
| Sharpe 公式 | sqrt(252) * IR ≈ 15.8 * IR |
| Fitness 公式 | Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) ) |
| book size | 2000 万美元 |
| 本金假设 | 1000 万美元 |
| 杠杆 | 2 倍 |
| Turnover 含义 | 成交金额 / book size |
| Margin 含义 | PnL / 总成交额 |
| Self Correlation 目的 | 确保 Alpha 多样化，避免重复提交 |
| IS 长度 | 最近 5 年（顾问 10 年） |
| Semi-OS 长度 | 最近 2 年，隐藏 |
| ACTIVE 状态作用 | 积累 Weight、参与季度报酬 |
| DECOMMISSIONED 原因 | 数据集停用 / OS 长期表现不佳 |

---

## 十一、常见错误

1. **混淆 Return 和 PnL**：Return 是百分比；PnL 是美元金额。
2. **忽视 Fitness**：Fitness 综合了 Sharpe、Return、Turnover，比单一 Sharpe 更稳定。
3. **只看累计 PnL 不看回撤**：大回撤会让 Alpha 被评为 Needs Improvement。
4. **误以为高收益就是好**：高 Sharpe + 低换手 + 低回撤才是关键。
5. **提交高相关 Alpha**：Self Correlation 接近 1 的 Alpha 会被平台拒绝或视为冗余。
6. **分不清 IS / Semi-OS / Real OS**：提交后看的是 Semi-OS 和 Real OS，不是 IS。
