# BRAIN Alpha 改进与顾问进阶指南

> 来源：WorldQuant BRAIN 必读文章《如何改进你的 Alpha🥉》+ MAPC Star 顾问入门指南 + D0 Alpha 简介 + 研究顾问流程
> 本文档覆盖：Alpha 优化方法论、顾问环境新测试、D0 Alpha 特性、成为顾问的完整路径。

---

## 一、一句话总结

Alpha 研究 = 创意（Idea）+ 数据（Data）+ 算子（Operator）+ 调参（Tuning）。
顾问进阶则在用户基础上多了两个硬门槛：**Production Correlation（生产相关性）** 和 **IS Ladder Sharpe（IS 阶梯夏普）**，且回测周期从 5 年变为 10 年。

---

## 二、Alpha 研究周期的 3 个阶段

1. **提出一个直观的 Alpha 思路**  
   量化研究是创造性思维与科学性思维的结合，没有唯一正确答案。
2. **使用可用的数据集和运算函数来实现它**  
   把思路翻译成 Fast Expression。
3. **优化 Alpha 的参数和中性化设置**  
   调整 Decay / Truncation / Neutralization 等参数，以最佳形式提交。

---

## 三、如何获得更高的 Sharpe

### 核心公式

信息比率（IR）：

```
IR = Return / standard_deviation(Return)
```

Sharpe 与 IR 的关系（年化）：

```
Sharpe ≈ √252 × IR ≈ 15.8 × IR
```

### 两条路径

| 路径 | 做法 | 风险 |
|---|---|---|
| **提高收益（Return）** | 用更多信息做更好的预测；可结合量价、新闻、分析师、基本面数据 | 复杂模型容易过拟合 |
| **降低波动（Volatility）** | 用中性化（Neutralization）降低对市场或高波动板块的暴露 | 过度中性化可能削弱信号 |

### 大白话

- Sharpe 高 = 单位风险带来的回报高。
- 要么你预测得更准（收益高），要么你赌得更稳（波动小）。
- 新手建议先花时间看 Brain 的 Learn 模块和社区论坛。

---

## 四、如何潜在地提高 Alpha 的收益

五条建议：

1. **提高换手率（Turnover）** — 交易越频繁，潜在收益越高（但成本也上升）。
2. **使用更低的 Decay 值** — 让信号更快反映最新数据。
3. **在流动性更好、更小的股票池（Universe）上工作**。
4. **在收益和回撤不变的前提下，适度提高 Alpha 波动率**，可能带来更高收益。
5. **尝试新闻（News）和分析师（Analyst）数据集**，这些常能产出高收益 Alpha。

---

## 五、如何降低 Alpha 的相关性

### 好消息

相关性高说明你的实现思路和原 Alpha 相似，大概率没做错。这个思路可以保留，做成变体。

### 降低相关性的 3 个方向

| 方法 | 示例 |
|---|---|
| **换数据字段** | 用 `high` / `low` / `open` 替代 `close` |
| **换运算函数** | 用功能相近但形式不同的算子替换 |
| **换分组方式** | 用 industry / subindustry / sector / country 等不同层级分组 |

### 注意事项

- 优先尝试**等价替换**，不要为了降相关而扭曲原思路。
- 不要纯粹为了降相关而造一个无意义的分组。
- 真正的降相关来自**跳出框架思考**。

---

## 六、如何降低换手率

### 事件驱动框架

概念：

```
if (事件发生) {
    赋予 Alpha 值;
} else {
    保持原 Alpha 值;
}
```

表达式：

```
trade_when(Event_condition, Alpha_expression, -1)
```

### 优点

- Alpha 覆盖度好
- 事件触发灵活
- 可在合适时机交易以增强信号
- 换手率低、成本低

### 缺点

- 不容易拿到高 Sharpe
- 不容易拿到高 Return

### 实践方法

1. **定义事件**：任何收益率、数据值、技术指标的异常 spike 都可以作为事件。
2. **赋予 Alpha**：寻找与事件异常方向一致的信号。
3. **注意覆盖度**：确保事件别太罕见，否则 coverage 太低。
4. **保持持仓可替换为线性或指数衰减**。

---

## 七、如何潜在地降低 PnL 波动

PnL 曲线突然跳变通常有 3 个原因：

| 原因 | 表现 | 解决方案 |
|---|---|---|
| Alpha 值在 NaN 与非 NaN 之间频繁切换 | 数据缺失导致仓位忽有忽无 | 使用 `backfill` 函数填充 |
| Alpha 值随时间快速变化 | 信号过于敏感 | 在公式中加入 `decay` 或移动平均 |
| 单只股票权重过大 | 个股跳变导致整体 PnL 跳变 | 在 Simulation Settings 中设置 Truncation，建议 < 0.1 |

---

## 八、如何建立对 Neutralization 的直觉

### 基础中性化

中性化是把原始 Alpha 拆成若干组，然后在每组内部减去均值（标准化）。

- **市场中性化（market）**：整个市场对半多空，多头金额 ≈ 空头金额。
- **行业中性化（industry）**：每个行业内对半多空。
- **子行业中性化（subindustry）**：更细粒度。
- **Sector**：Industry 的超集；Industry 又是 Subindustry 的超集。

例如：

```
Alpha = -ts_delta(close, 5)
```

设置 `Neutralization = market` 后：

```
Alpha = Alpha - mean(Alpha)
```

随后再做归一化和 booksize 缩放，组合即为多空中性。

### `group_neutralize(x, group)` vs Simulation Settings 中的 Neutralization

| 方式 | 用法 | 配套设置 |
|---|---|---|
| Simulation Settings 中设置 Neutralization | 最后一步统一做中性化 | 常规使用 |
| 表达式内使用 `group_neutralize(x, group)` | 需要更细粒度控制时使用 | Neutralization = None，Decay = 0，Truncation = 0 |

### 等价示例

```
alpha1 = -zscore(ebit/capex)   # Neutralization=industry, Decay=0, Truncation=0
alpha1 = group_neutralize(-zscore(ebit/capex), industry)   # Neutralization=None, Decay=0, Truncation=0
```

### 提示

- 始终为 Neutralization 选一个值；只有表达式里已手动做中性化时才选 None。
- 股票数量少但流动性高的池子：用更大的分组。
- 流动性差的池子：用更小的分组。
- EUR、ASI 区域：尝试 `country` 和 `exchange` 中性化。

### 按数据集推荐的中性化方法

![按数据集推荐的中性化方法](docs/images/neutralization_recommendation_table.png)

| 数据集类别 | 推荐中性化 | 备注 |
|---|---|---|
| 基本面数据 | industry / subindustry | 不同行业基本面差异大 |
| 分析师数据 | industry / subindustry | 预测未来基本面，行业差异大 |
| 模型数据 | market / sector / industry / subindustry | 子类别差异可能极大，需尝试 |
| 新闻数据 | subindustry | 同一事件对不同公司影响不同，Twitter 与苹果同属科技但子行业不同 |
| 期权数据 | market / industry | 期权对股价影响在广泛行业中近似 |
| 价格量数据 | industry / subindustry | 通用，但工业/子行业中性化可能降低表现 |
| 社交媒体 | industry / subindustry | 影响因子因行业而异 |
| 机构数据 | industry / subindustry | 取决于数据类型、提供者及影响 |
| 空头利率 | industry | 空头兴趣数据建议行业中性 |
| 内部数据 | industry / subindustry | 内部消息影响因行业而异 |
| 情绪数据 | industry / subindustry | 情绪影响因行业而异 |
| 收益数据 | industry / market | 类似基本面 |
| 宏观数据 | market / sector / industry | 宏观经济活动跨行业影响，子行业差异不大 |

---

## 九、如何避免过拟合

### 核心认知

- 拟合是 Alpha 创作的一部分，过拟合也是。
- 比过拟合更糟的是：**没有想法的随机数据挖掘**。
- 稳健的 Alpha 需要好想法 + 严格测试。

### 常用稳健性测试

| 测试 | 做法 |
|---|---|
| **Rank test** | 把 Alpha 转成排名 |
| **Binary test** | 把 Alpha 转成 -1 / 1 |
| **Sub / Super universe test** | 在子池/超池上测试 |

> 还有更多基于创造力的测试；随机回测因市场条件变化往往不太适用。

### 避免过拟合的 8 条技巧

1. 不要把权重集中在高波动股票上。
2. 降低对因子的暴露。
3. 不要选“最好”的参数，第二好的参数通常过拟合倾向更小。
4. 不要为了让测试通过而拟合测试。
5. 不要“选择”。例如 4 天还是 6 天 decay 犹豫时，直接用 5 天，或取 4 和 6 的平均。
6. 不要陷入“Excellent / Superior”陷阱。IS 表现好不是重点，重点是**能不能持续**。
7. 善待他人，分享想法和好的建议。
8. 使用 Simulation Settings 中的 **Test Period** 功能：把 IS 分成 Train / Test，Train 开发、Test 验证。

---

## 十、MAPC Star：顾问环境 Alpha 入门指南

### 顾问环境 vs 用户环境

| 维度 | 用户环境 | 顾问环境 |
|---|---|---|
| 回测周期 | 5 年 | 10 年 |
| 提交测试 | 基础测试 | 新增 Production Correlation、IS Ladder Sharpe |
| 可用数据集 | 有限 | 更多数据集、更多地区、更多设置 |

### 新增提交测试 1：Production Correlation（生产相关性）

- 你的 Alpha 会与**顾问池中所有现有 Alpha** 做相关测试，而不只是你自己的。
- 通过条件（满足其一即可）：
  - 与任意顾问 Alpha 的**最大相关性 < 0.7**；或
  - 对每个相关性 > 0.7 的 Alpha，你的 Sharpe 至少比它**高 10%**。

> 提示：默认回测时不自动运行。可点击结果面板中 Production Correlation 部分的刷新按钮手动跑一次，评估想法是否足够差异化。但别太频繁，顾问每小时可发起的相关性请求数量可能有限。

![Production Correlation 刷新按钮位置](docs/images/production_correlation_refresh.png)

### 新增提交测试 2：IS Ladder Sharpe（IS 阶梯式夏普）

- 在不同时间段上 Sharpe 需保持稳定，避免只在某一段表现好。

### 顾问起步建议

1. **从熟悉的领域开始**：用 10 年周期回测你过去的 Alpha，观察在新测试中的表现。
2. **替换同类数据字段**：把过去 Alpha 中的字段替换为同数据集类别下的其他字段。
3. **探索模型数据集**：模型数据集的字段通常已经预处理，更容易构造 Alpha。
4. **尝试新数据集类别**：增加 Alpha 池多样性。
   - 注意：向量字段需先转为矩阵字段。
   - 参考《6 种快速评估新数据集的方法》和《Weight Coverage 常见问题与建议》。

---

## 十一、D0 Alpha 简介

### D0 vs D1

| 特性 | D0 Alpha | D1 Alpha |
|---|---|---|
| 数据时点 | 盘中使用当日最新数据 | 使用前一日收盘数据 |
| 交易时间 | 收盘前一段时间 | 次日开盘 |
| 反应速度 | 更快 | 较慢 |
| 适用区域 | 仅限 USA / EUR / CHN | 更广 |
| 提交门槛 | 更高 | 相对较低 |

### D0 Alpha 的特点

- 能捕捉**隔夜收益（Overnight Returns）**：公司常在收盘后发布新闻/报告，盘后股价变化 D1 无法捕捉。
- D0 比 D1 更早进入交易，因此预期收益更高。
- 只有部分数据集提供 D0 数据字段。

### D0 研究技巧

1. 用 `trade_when` 捕捉事件溢价（并购、盈利发布、股票回购等）。
2. 在 CHN 等有涨跌停限制的区域，若股票触及涨跌停，Alpha 不应改变该股票仓位。
3. 初学者可先在 D0 设置中回测所有 D1 Alpha，或把 D1 字段换成 D0 等价字段。
4. D0 应在高流动性股票上构建（USA 用 TOP1000 或更高流动性组合）。

### D0 稳健性要求

- D0 通常换手率更高，需要更高 Sharpe 和更高收益来覆盖成本。
- 还需通过 CHN 子池测试、稳健组合测试等。
- 若字段在 D1 也可用，建议在 D1 中自查；好的 D0 Alpha 在 D1 中通常仍保留部分业绩（会下降）。

---

## 十二、成为研究顾问的流程

1. **在 BRAIN 上获得至少 10,000 分**（Challenge 金牌门槛）。
2. **提交符合测试标准的 Alphas** 即可获得积分。
3. **通常需在 5 个以上不同自然日提交 5–10 个 Alpha** 即可达到 10,000 分；单日积分上限 2000 分。
4. **通过背景调查**。
5. **签订咨询协议**等其他流程。
6. 完成后成为 BRAIN 研究顾问。

---

## 十三、考试速查卡

### Sharpe 提升

```
IR = Return / std(Return)
Sharpe ≈ 15.8 × IR
```

- 要么提高 Return（更好预测），要么降低 Volatility（更好中性化）。

### Return 提升 5 招

1. 提高 Turnover
2. 降低 Decay
3. 用更小流动性 Universe
4. 适度提高波动率
5. 用 News / Analyst 数据

### 相关性降低 3 招

1. 换字段（open/high/low 替代 close）
2. 换算子
3. 换分组

### 换手率降低

```
trade_when(Event_condition, Alpha_expression, -1)
```

### PnL 波动降低

| 问题 | 解法 |
|---|---|
| NaN 跳变 | `backfill` |
| 信号太快 | `decay` / 移动平均 |
| 单股权重过大 | Truncation < 0.1 |

### 过拟合防护

- Rank / Binary / Sub-universe 测试
- Test Period（Train / Test 划分）
- 不选最好参数，选第二好或平均
- 不为了通过测试而拟合测试

### 顾问新测试

| 测试 | 通过条件 |
|---|---|
| Production Correlation | max corr < 0.7 或 对相关 >0.7 的每个 Alpha Sharpe 高 10% |
| IS Ladder Sharpe | 不同时间段 Sharpe 稳定 |

### D0 Alpha

- 盘中交易，收盘前执行
- 仅 USA / EUR / CHN
- 捕捉隔夜收益
- 门槛更高

---

## 十四、易错点

1. **认为存在“标准答案”**：Alpha 研究是创意 + 科学，没有唯一正确答案。
2. **过度拟合测试**：测试是为了验证稳健性，不是为了让它通过。
3. **为了降相关而硬造分组**：分组必须有经济或业务含义。
4. **忽视 Truncation**：单股权重过大是 PnL 跳变的常见原因。
5. **D0 直接套用 D1 参数**：D0 换手率高、成本高、门槛高，需单独优化。
6. **频繁跑 Production Correlation**：顾问每小时请求次数有限，别浪费。
7. **Neutralization = None 时忘了表达式内已中性化**：只有手动做了中性化才选 None。

---

## 十五、关联文档

- `BRAIN_Alpha与回测原理完整教程.md` — Alpha 概念与回测 7 步
- `BRAIN_回测设置(Simulation_Settings)完全指南.md` — Neutralization / Decay / Truncation 详解
- `BRAIN_Alpha提交测试完整清单.md` — 六项提交测试 + 特殊 Alpha 类型
- `BRAIN_WorldQuant_Challenge_挑战赛规则.md` — Challenge 积分规则
- `BRAIN_FastExpression_官方操作符完整清单.md` — `trade_when`、`group_neutralize`、`backfill` 等算子
- `BRAIN_零基础学量化第二课_数据与算子.md` — 向量转矩阵、Weight Coverage
