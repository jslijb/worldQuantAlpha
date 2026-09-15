# BRAIN Alpha 提交测试完整清单

> 来源：WorldQuant BRAIN 官方提交测试说明。所有测试在**样本内（IS）期**运行，提交按钮位于 Simulation Result 面板中的 **Submission 标签页**，只有满足性能和相关性阈值的 Alpha 才会启动**样本外（OS）测试**。

---

## 一、提交流程总览

1. 在 Simulate 页面回测 Alpha。
2. 回测成功后 Alpha 状态为 **"UNSUBMITTED"**。
3. 点击 **"Submit Alpha"** 按钮，平台检查是否通过所有提交测试。
4. 通过的 Alpha 进入 **OS（Out-of-Sample）测试**，状态变为 **"ACTIVE"**。
5. 只有已提交的 Alpha 才会被纳入评分，并显示在 **Alphas 页面的 Out-of-Sample 标签页**。

---

## 二、Alpha 提交测试清单

| 提交标准 | 面向用户的阈值 | 说明 |
|---|---|---|
| **Fitness** | 至少为 "Average"：Delay-0 > 1.3，或 Delay-1 > 1.0 | Fitness 是 Returns、Turnover、Sharpe 的综合函数 |
| **Sharpe** | Delay-0 Alpha > 2.0，或 Delay-1 Alpha > 1.25 | 衡量 Alpha 收益的一致性和风险调整后收益 |
| **换手率（Turnover）** | **1% < Turnover < 70%** | 过低意味着几乎不交易，过高意味着交易成本大 |
| **权重测试（Weight Test）** | 任何股票的最大权重 < **10%** | 衡量资本集中度。需要在足够多天里对足够多股票分配权重 |
| **子股票池测试（Sub-universe Test）** | 子股票池中的 Sharpe 必须高于按规模缩放的阈值 | 确保 Alpha 在更小/更流动的股票池中仍有效 |
| **自相关性（Self Correlation）** | PnL 相关性 < **0.7**；或 Sharpe 比相关 Alpha 高 10% | 避免提交过度相似的 Alpha |

---

## 三、各测试详解

### 3.1 Fitness 测试

**公式：**

```
Fitness = Sharpe * sqrt( abs(Returns) / max(Turnover, 0.125) )
```

**通过门槛：**

| Fitness 评级 | Delay 1 | Delay 0 |
|---|---|---|
| Spectacular | > 2.5 | > 3.25 |
| Excellent | > 2.0 | > 2.6 |
| Good | > 1.5 | > 1.95 |
| Average | > 1.0 | > 1.3 |
| Needs Improvement | ≤ 1.0 | ≤ 1.3 |

- **提交最低要求**：达到 **Average** 级别，即 Delay-1 > 1.0 或 Delay-0 > 1.3。
- 提升 Fitness 的方法：**提高 Sharpe 或 Returns，降低 Turnover**。

---

### 3.2 Sharpe 测试

**公式：**

```
IR = mean(PnL) / stdev(PnL)
Sharpe = sqrt(252) * IR ≈ 15.8 * IR
```

**通过门槛：**

| 延迟 | Sharpe 最低要求 |
|---|---|
| Delay 0 | > 2.0 |
| Delay 1 | > 1.25 |

> Sharpe 衡量 Alpha 的收益一致性，高 Sharpe 比单纯高 Return 更有价值。

---

### 3.3 换手率（Turnover）测试

**定义：** 每日交易金额与 book size（2000 万美元）的比率。

**通过区间：**

```
1% < Turnover < 70%
```

- **Turnover < 1%**：交易太少，几乎不换手，平台认为没有实际交易价值。
- **Turnover > 70%**：交易成本过高，难以实盘盈利。
- **降低 Turnover 的方法**：使用 `decay`、`ts_decay_linear`、`hump`、`trade_when`、`rank` 等算子。

---

### 3.4 权重测试（Weight Test）

**核心目的：** 限制单只股票的资本集中度，降低回撤风险，尤其在 OS 期间。

**失败常见原因：**

1. **覆盖度低**：某天长/空头股票数量过少（如多头 < 10 只或总股票 < 20 只）。
2. **多空不平衡**：多头或空头股票数量严重失衡。
3. **异常值/数据分布问题**：数据中有极端值导致权重过度集中。
4. **单只股票权重过高**：如某只股票占 Alpha 总权重的 30%。

**解决方案：**

| 问题 | 解决方法 |
|---|---|
| 覆盖度低 | `ts_backfill(a, 2)`、`ts_backfill(a, 60)`、`kth_element`、`group_backfill` |
| 权重集中 | `rank`、`group_rank`、`log`、`scale`、`zscore` 等归一化 |
| 单只权重 > 10% | 设置 `Truncation = 0.1` |
| 异常值 | `winsorize`、取对数、用 `rank` 转换分布 |

**推荐操作：**

```
rank(-ts_delta(close, 2))
```

> `rank` 本身也是 robust test 的一部分，使用 rank 的 Alpha 更容易通过 rank test。

**如果所有方法都失败，建议换思路。**

---

### 3.5 子股票池测试（Sub-universe Test）

**核心目的：** 确保 Alpha 不仅在目标股票池中表现好，在**更小、更流动**的股票池（如 TOP3000 → TOP1000）中也有效。

**通过阈值公式：**

```
subuniverse_sharpe >= 0.75 * sqrt(subuniverse_size / alpha_universe_size) * alpha_sharpe
```

**计算 Sub-universe Sharpe 的流程：**

1. **Pasteurize** 到目标子股票池：对不在子股票池中的股票赋值为 NaN。
2. 应用中**市场性化**（每个值减去所有值的均值）。
3. 将 Alpha 缩放回原大小。
4. 用处理后的 Alpha 值计算 PnL。

**提升通过率的技巧：**

| 技巧 | 说明 |
|---|---|
| 避免市值相关乘数 | 如 `rank(-assets)`、`1 - rank(cap)` 会偏向大/小市值股票，影响子股票池表现 |
| 分别对高/低流动性部分衰减 | `ts_decay_linear(signal, 5) * rank(volume*close) + ts_decay_linear(signal, 10) * (1 - rank(volume*close))` |
| 逐步检查改进 | 某个改进可能提升统计指标但导致子股票池测试失败 |
| 提升整体 Sharpe | 整体 Sharpe 提高，子股票池 Sharpe 也更容易达标 |
| 接受失败 | 有些信号本身就不够稳健，放弃它是正确的 |

---

### 3.6 自相关性测试（Self Correlation Test）

**核心目的：** 确保用户提交的 Alpha 足够多样化，避免大量重复/高度相似的 Alpha。

**通过标准：**

1. **PnL 相关性 < 0.7**。
2. 或者，如果 Alpha 与已有 Alpha 高度相关（≥ 0.7），则当前 Alpha 的 **Sharpe 至少比相关 Alpha 高 10%**。

**例外规则示例：**

- 你之前提交的 Alpha X 的 Sharpe = 3.18。
- 如果新 Alpha Y 与 X 高度相关，但 Sharpe ≥ **3.18 * 1.1 = 3.50**，仍然可以提交。
- 这个机制允许你对现有 Alpha 进行**实质性改进**后再次提交。

**计算窗口：**

- 自相关性在 **4 年窗口** 上运作。
- 内在相关性基于所选 Alpha 的 PnL 时间周期交集计算。

**查看位置：** 模拟结果页面的 **Correlation Summary Table**。

---

## 四、特殊 Alpha 类型

### 4.1 ATOM Alpha

**定义：** 仅使用**一个数据集字段**的 Alpha。

**特殊规则：**

- 以下分组字段**不会**使 Alpha 失去 ATOM 资格：currency、country、exchange、industry、subindustry、market。
- 使用 `inst_pnl` 算子会被计为使用了 **pv1 数据集**。因此 `inst_pnl(<来自非 pv1 数据集字段>)` **不具备 ATOM 资格**。
- ATOM Alpha **跳过 IS 阶梯 Sharpe 测试**，但仍需通过常规 IS 测试和 **2Y Sharpe 测试**。

---

### 4.2 金字塔 Alpha（Pyramid Alphas）

**定义：** 金字塔 = 区域（Region）+ 延迟（Delay）+ 数据集类别（Dataset Category）的组合。

**示例：** `USA-D1-analyst` 代表 USA 区域、Delay-1、analyst 数据集类别。

**规则：**

- 一个 Alpha 使用多个不同类别的数据字段，可以属于多个金字塔。
- **金字塔 Alpha**：最多贡献 **2 个金字塔**的 Alpha。
- 以下分组字段不计入金字塔数量：currency、country、exchange、industry、subindustry、market。
- 示例：一个 Alpha 使用两个金字塔 + 中性化字段，仍只算贡献 2 个金字塔，仍具备金字塔 Alpha 资格。

---

### 4.3 Power Pool Alpha

**标准：**

| 条件 | 阈值 |
|---|---|
| Sharpe | ≥ 1.0 |
| 唯一算子数量 | ≤ 8 |
| 唯一数据字段数量（不含分组字段） | ≤ 3 |
| 换手率 | 1%–70%（含端点） |
| 自相关性 | ≤ 0.5（仅 Power Pool Alpha 之间的相关性） |
| 区域/延迟/类型 | USA Delay 1 |

**分组字段定义：** country、industry、subindustry、currency、market、sector、exchange。

**注意：**

- 一旦将 Alpha 标记为 Power Pool，即使之后取消标记，它**仍会保留在自相关性池**中。
- Power Pool 只与自己的 Alpha 计算相关性，而不是与所有 Alpha。

---

## 五、提交测试速查表

| 测试 | 阈值 | 提升方法 |
|---|---|---|
| Fitness | D0 > 1.3，D1 > 1.0 | 提高 Sharpe/Returns，降低 Turnover |
| Sharpe | D0 > 2.0，D1 > 1.25 | 提高收益一致性，降低波动 |
| Turnover | 1% < T < 70% | 用 decay、hump、trade_when |
| Weight Test | 单只 < 10% | rank、truncation、ts_backfill |
| Sub-universe | 缩放 Sharpe 阈值 | 避免市值乘数、分别衰减、提高整体 Sharpe |
| Self Correlation | < 0.7 或 Sharpe 高 10% | 多样化思路、不同数据集 |

---

## 六、考试常见考点

1. **提交按钮在哪里？** → Simulation Result 面板的 **Submission 标签页**。
2. **只有什么状态才能累积 Weight？** → **ACTIVE**。
3. **Delay-1 Sharpe 最低多少能提交？** → **> 1.25**。
4. **Turnover 通过区间？** → **1% 到 70%**。
5. **单只股票最大权重限制？** → **< 10%**。
6. **自相关性通过门槛？** → **PnL 相关性 < 0.7** 或 Sharpe 高 10%。
7. **ATOM Alpha 跳过了哪个测试？** → **IS 阶梯 Sharpe 测试**。
8. **Power Pool 最多几个唯一算子？** → **8 个**。
9. **Challenge 金牌多少分？** → **10,000 分**。
