# WorldQuant BRAIN：快速表达式、IQC 提示与 Alpha 示例题库

> 来源：WorldQuant BRAIN 官方零基础教程 / IQC 提示 / Alpha 示例（含《IQC技巧与示例》PDF）
> 整理时间：2026-09-05（2026-09-06 合并原《BRAIN_IQC技巧与Alpha示例集.md》，该文档已删除）
> 说明：本题库为 BRAIN 研究能力笔试/面试的重要出题来源，建议连同《BRAIN_Alpha与回测原理完整教程.md》一起复习。
> 操作符全集请查《BRAIN_FastExpression_官方操作符完整清单.md》（官方 operators.pdf 全量归档）。

---

## 一、快速表达式（Fast Expression）基础

快速表达式由三类元素组成：

| 元素 | 说明 | 示例 |
|---|---|---|
| **数据字段** | 有名称的数据集合 | `open`（开盘价）、`close`（收盘价）、`volume`（成交量）、`vwap`（成交量加权均价） |
| **算子（Operator）** | 实现 Alpha 思路的数学/统计技术 | `rank`、`ts_delta`、`ts_sum`、`group_rank`、`ts_regression` |
| **数值** | 常量 | `2`、`30`、`0.1`、`20` |

### 注释与分号规则

- **多行注释**：用 `/**/` 包裹。
- **分号 `;`**：每一行代码结尾加分号，**最后一行不需要分号**。

```fastexpr
/* 这是一个多行注释示例 */
rank(ts_delta(close, 2));      /* 第一行，加分号 */
rank(-returns)                  /* 最后一行，不需要分号 */
```

---

## 二、IQC 提示（官方实战建议）

### 1. 股票池与中性化

- **多换 universe 回测**，不要只盯一个股票池。
- **多尝试中性化设置**（market / sector / industry / subindustry）。
- **权重上限**：单个股票最大权重建议 <= **0.1（10%）**。
- 两种中性化方式：
  - **Simulation Settings 面板**：左上角直接选。
  - **代码中用 `group_neutralize`**：使用这种方式时，Simulation Settings 里要选 **Neutralization=None**。
  - `group_neutralize` 的好处：可以灵活按 sector 划分，也可以自定义分组。

### 2. 常用算子尝试

- `rank`：横截面排名（0~1 均匀分布）。
- `group_rank`：组内排名。
- `ts_rank`：时间序列排名。
- `ts_sum`、`ts_max`、`ts_median`、`ts_decay_exp_window`、`ts_decay_linear`：降低换手率。
- `ts_corr`、`ts_regression`：时序相关性与回归。

### 3. 数据与覆盖度

- `sentiment`、`news data` 等数据集 **coverage 较低**（覆盖股票少）。
- 使用 `kth_element` 可以提高 alpha 的 **long-short count**（多空股票数量）。
- 只交易少数几只股票很难获得好表现，所以覆盖度很重要。

### 4. 分散化

- 使用不同算子：rank、ts_rank、ts_corr、ts_regression。
- 结合不同类型数据：price/volume、fundamental、sentiment、relationship data。
- 目的：**降低 Alpha 之间的相关性**，构建更稳健的 Alpha 池。

### 5. 中性化粒度选择

| Alpha 特征 | 推荐中性化粒度 |
|---|---|
| **高换手率** | 更细的分组，例如 **subindustry** |
| **低换手率** | 更宽泛的分组，例如 **sector** 或 **industry** |

### 6. 学习资源

- Investopedia、StockCharts：学习技术指标和基本面比率。
- Learn 模块里的推荐阅读：论文不会直接给代码，但正确实现思路往往是好 Alpha 的基础。
- **分组粒度选择还需结合流动性与股票数量**（原 IQC 技巧 #9）。
- **持续实验，从社区和论坛获取经验**（原 IQC 技巧 #10）。

---

## 三、IQC 评分指南

团队得分基于成员提交 alphas 的 **Merged PnL** 的各项参数：

| 参数 | 对得分的影响 |
|---|---|
| **Merged PnL Sharpe Ratio** | 越大越好 |
| **Merged PnL return/dd（收益回撤比）** | 越大越差 |
| **Merged PnL Turnover（换手率）** | 越大越差 |

> 提示：IQC 不是单纯比谁收益高，而是比 **夏普高、回撤小、换手低** 的综合表现。

---

## 四、Alpha 示例 1-13（附模拟设置截图）

下面 13 个示例来自官方教程，覆盖均值回归、价值、动量、成交量、事件驱动、SMA、trade_when 等常见思路。**考试时很可能要求解释代码含义、判断属于什么因子类型、或根据截图反推设置。**

---

### 示例 1：成交量加权的均值回归

**思路**：`-ts_delta(close, 2)` 是均值回归想法；成交量较高时，该信号的权重降低。

**代码**：

```fastexpr
-rank(ts_delta(close, 2)) * (1 - rank(ts_decay_linear(volume / sum(volume, 30), 10)))
```

**模拟设置**：

![示例1 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-081Z-802ae2cd.png)

> 记忆点：反转因子 + 成交量抑制；decay=6，中性化=subindustry。

---

### 示例 2：资产周转效率

**思路**：每单位资产能产生更高收入的公司，给予更高权重。

**代码**：

```fastexpr
rank(sales / assets)
```

**模拟设置**：

![示例2 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-085Z-a481f9e2.png)

> 记忆点：基本面因子 sales/assets；decay=20，中性化=subindustry。

---

### 示例 3：低市盈率（P/E）价值因子

**思路**：市盈率越低，公司越被低估，给予更高权重。

**代码**：

```fastexpr
group_rank(eps / close, subindustry)
```

**模拟设置**：

![示例3 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-087Z-1dd6ed14.png)

> 记忆点：子行业内排名；eps/close 是市盈率的倒数（E/P）；decay=0，中性化=market。

---

### 示例 4：净利润预测相对规模

**思路**：按公司规模调整后，净利润预测更高的公司给予更高权重。

**代码**：

```fastexpr
group_rank(est_netprofit / cap, subindustry)
```

**模拟设置**：

![示例4 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-089Z-b14aaf15.png)

> 记忆点：子行业内 group_rank；est_netprofit/cap 是预测净利润相对市值；decay=5，中性化=market。

---

### 示例 5：基础反转信号

**思路**：过去 2 天涨幅越大，越可能反转下跌，做空；跌幅越大，越可能反弹，做多。

**代码**：

```fastexpr
rank(-ts_delta(close, 2))
```

**模拟设置**：

![示例5 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-091Z-9afdf44d.png)

> 记忆点：最经典的短周期反转；decay=5，中性化=industry。

---

### 示例 6：收盘价 vs VWAP 回归残差

**思路**：对过去 60 天收盘价与 vwap 做回归，取回归估计的 close 值；再用延迟 2 天的 close 减去它，得到偏离度信号。

**代码**：

```fastexpr
rank(ts_delay(close, 2) - ts_regression(close, vwap, 60, rettype=3))
```

**模拟设置**：

![示例6 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-093Z-83c20874.png)

> 记忆点：`rettype=3` 表示返回回归估计值；decay=5，中性化=subindustry。

---

### 示例 7：月度尺度均值回归（涨跌天数比）

**思路**：比较 20 天内下跌天数与上涨天数的比例，再与年度（252 天）比例比较。

**代码**：

```fastexpr
a = ts_sum(open > close, 20) / ts_sum(open < close, 20);
b = ts_sum(open > close, 252) / ts_sum(open < close, 252);
rank(a / b)
```

**模拟设置**：

![示例7 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-095Z-8ca8500a.png)

> 记忆点：open>close 表示阴线（跌）；用月度比值 / 年度比值；decay=130，中性化=subindustry。

---

### 示例 8：成交量放大时的增强反转

**思路**：如果成交量大于 20 日平均成交量（adv20），则对反转信号加倍下注。

**代码**：

```fastexpr
volume > adv20 ? 2 * rank(-ts_delta(close, 2)) : rank(-ts_delta(close, 2))
```

**模拟设置**：

![示例8 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-098Z-481c6faa.png)

> 记忆点：条件运算符 `? :`；放量时放大反转仓位；decay=5，中性化=industry。

---

### 示例 9：连续下跌止损信号

**思路**：如果收盘价连续 4 天下降，则降低权重或做空；否则使用基础反转信号。

**代码**：

```fastexpr
ts_sum(sign(ts_delta(close, 1)), 4) == -4 ? 0 : rank(-ts_delta(close, 2))
```

**模拟设置**：

![示例9 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-100Z-85b590f2.png)

> 记忆点：`sign()` 返回涨跌方向；连续 4 天跌则权重为 0；decay=5，中性化=subindustry。

---

### 示例 10：使用 trade_when 操作符

**思路**：只在成交量大于 adv20 时，对 -returns 信号进行交易；其他时间用 -1 占位（或不交易）。

**代码**：

```fastexpr
rank(trade_when(volume > adv20, -returns, -1))
```

**模拟设置**：

![示例10 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-102Z-b1d2497f.png)

> 记忆点：`trade_when(condition, value, otherwise)`；只在条件满足时交易；decay=5，中性化=industry。

---

### 示例 11：简单移动平均线（SMA20）趋势增强

**思路**：收盘价高于 20 日简单移动平均线时，对反转信号赋予更高权重。

**代码**：

```fastexpr
close > ts_sum(close, 20) / 20 ? 1.6 * rank(-ts_delta(close, 2)) : rank(-ts_delta(close, 2))
```

**模拟设置**：

![示例11 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-103Z-5030d820.png)

> 记忆点：SMA20 = `ts_sum(close,20)/20`；价格上穿均线时放大反转仓位；decay=0，中性化=subindustry。

---

### 示例 12：Morning Gap 事件驱动 + 趋势跟踪

**思路**：当开盘缺口（昨收与今开差距）的 Z-score 超过 3.5 时触发事件；沿价格方向建仓；当价格相对事件时收盘价变动 10% 时退出；用 5 期线性衰减平滑。

**代码**：

```fastexpr
event = abs(ts_zscore(ts_delay(close, 1) - open, 20)) > 3.5;
alpha = ts_delta(close, 5) / ts_stddev(close, 252);
close_at_event = trade_when(event, close, -1);
end = abs(close_at_event - close) / close_at_event > 0.1;
ts_decay_linear(trade_when(event, alpha, end), 5)
```

**模拟设置**：

![示例12 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-105Z-ecff8e0f.png)

> 记忆点：事件驱动 + 退出条件 + decay 平滑；NAN HANDLING=ON 提高 universe 覆盖率；decay=20，中性化=subindustry。

---

### 示例 13：月度尺度均值回归（涨跌幅度比）

**思路**：比较每日上涨和下跌的平均幅度（用 bar = (open-close)/(high-low) 标准化），再除以年度表现。

**代码**：

```fastexpr
bar = (open - close) / (high - low);
a = ts_sum((open > close) * bar, 20) / ts_sum((open < close) * (-bar), 20);
b = ts_sum((open > close) * bar, 252) / ts_sum((open < close) * (-bar), 252);
rank(a / b)
```

**模拟设置**：

![示例13 模拟设置](C:/Users/jslij/.workbuddy/clipboard-images/clipboard-2026-09-05T13-59-15-106Z-431bb379.png)

> 记忆点：用 (开-收)/(高-低) 标准化 K 线实体；月度跌幅幅度 / 年度跌幅幅度；decay=20，中性化=subindustry。

---

## 五、13 个示例速查卡

| 示例 | 因子类型 | 核心算子 | 核心思路 | Decay | 中性化 |
|---|---|---|---|---|---|
| 1 | 均值回归 + 成交量 | `ts_delta`、`ts_decay_linear` | 反转，放量时降权 | 6 | subindustry |
| 2 | 基本面 | `rank` | sales/assets 越高越好 | 20 | subindustry |
| 3 | 价值 | `group_rank` | 子行业内低 P/E（高 E/P） | 0 | market |
| 4 | 基本面预期 | `group_rank` | 子行业内预测净利润/市值 | 5 | market |
| 5 | 均值反转 | `ts_delta`、`rank` | 2 日反转 | 5 | industry |
| 6 | 统计套利 | `ts_regression` | close 相对 vwap 回归残差 | 5 | subindustry |
| 7 | 月度反转 | `ts_sum` | 月度阴线/阳线天数比 vs 年度 | 130 | subindustry |
| 8 | 反转 + 成交量 | `? :` | 放量时放大反转仓位 | 5 | industry |
| 9 | 反转 + 止损 | `ts_sum`、`sign` | 连续 4 天下跌则空仓 | 5 | subindustry |
| 10 | 事件过滤 | `trade_when` | 仅放量时交易 -returns | 5 | industry |
| 11 | 反转 + 趋势 | `? :`、`ts_sum` | 收盘价 > SMA20 时放大反转 | 0 | subindustry |
| 12 | 事件驱动 | `ts_zscore`、`trade_when`、`ts_decay_linear` | Morning Gap 触发，趋势跟随，10% 退出 | 20 | subindustry |
| 13 | 月度反转 | `ts_sum` | 月度涨跌幅度比 vs 年度 | 20 | subindustry |

---

## 六、常考代码符号与算子清单

| 符号/算子 | 含义 | 考试重点 |
|---|---|---|
| `rank(x)` | 横截面排名，0~1 | 消除量纲，常用在最后一层 |
| `group_rank(x, group)` | 组内排名 | 避免组间不可比，如 subindustry |
| `ts_rank(x, d)` | 时间序列排名 | 看过去 d 天内的相对位置 |
| `ts_delta(x, d)` | d 天变化量 | x(t) - x(t-d)，反转常用 |
| `ts_sum(x, d)` | d 天求和 | 累计指标 |
| `ts_mean(x, d)` | d 天均值 | SMA |
| `ts_max / ts_min / ts_median` | 最大/最小/中位数 | 稳健统计 |
| `ts_corr(x, y, d)` | 时序相关性 | 两个序列过去 d 天的相关 |
| `ts_regression(x, y, d, rettype=3)` | 时序回归 | rettype=3 返回估计值 |
| `ts_decay_linear(x, d)` | d 期线性衰减 | 平滑，降换手 |
| `ts_decay_exp_window(x, d)` | 指数衰减 | 更重视近期 |
| `ts_zscore(x, d)` | Z-score 标准化 | 事件触发常用 |
| `ts_stddev(x, d)` | d 天标准差 | 波动率/分母 |
| `ts_delay(x, d)` | d 天延迟 | x(t-d)，避免未来函数 |
| `trade_when(cond, val, otherwise)` | 条件交易 | 只在 cond 满足时取 val |
| `? :` | 条件运算符 | if-then-else |
| `sign(x)` | 符号函数 | 1 / 0 / -1 |
| `sum(x, d)` | 截面求和（非时序） | 注意与 `ts_sum` 区分 |
| `adv20` | 20 日平均成交量 | 成交量放大判断 |
| `>` `<` `==` | 比较运算符 | 可生成 0/1 掩码 |

---

## 七、考试易错点提醒

1. **注释用 `/**/`**，不是 `#` 或 `//`。
2. **每行结尾加分号，最后一行不加**。
3. **`ts_sum` vs `sum`**：`ts_sum` 是时间序列求和（对一只股票过去 d 天）；`sum` 是截面求和（对当天多只股票）。
4. **`rank` vs `group_rank` vs `ts_rank`**：分别对应截面、组内、时序排名。
5. **中性化设置**：如果用 `group_neutralize` 代码算子，Simulation Settings 里要选 **Neutralization=None**。
6. **Decay 作用**：平滑权重、降低换手率、减少交易成本。
7. **权重上限**：IQC 提示建议单个股票最大权重 <= 0.1（10%）。
8. **IQC 评分**：Sharpe 越高越好；return/dd 越高越差；Turnover 越高越差。
