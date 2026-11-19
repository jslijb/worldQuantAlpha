# 面试复习 · 数据篇 + Alpha 回测原理

> **用途**：研究顾问面试备考。照这一份看即可,正文每节都标了对应的官方 Learn 页面 id(如 `data`、`how-brain-platform-works`),
> 需要回原文或看配图时,到 `docs/study/learn/docs/` 下对应文件即可。
> 所有口径均来自平台官方 tutorial-pages 接口原文,未掺外部知识。
> 生成日期 2026-09-16。

---

# 第一部分：数据(Data)

> 对应官方课程 `Data`(5 页):`data` / `how-use-data-explorer` / `vector-datafields` / `group-data-fields` / `getting-started-option6-implied-volatility-iv`
> 另:考纲点名的"字段分类"在 `data` 页,`group-data-fields` 讲分组字段与 `group_*` 算子。

## 1.1 最基础的概念(必须先讲明白)

| 概念 | 官方定义(要点) | 通俗理解 |
|---|---|---|
| **Data Field(字段)** | 一个有固定类型和业务含义的数据集合。如 `close`(收盘价)类型是数值,业务含义是"交易时段开始时证券的价格";`open` 类型相同但业务含义不同,所以是不同字段 | 一列数据,比如"每天每只股票的收盘价" |
| **Dataset(数据集)** | 若干 Data Field 的集合。用名称(长文本)或 dataset ID(短字母数字)标识 | 一张"表",里面有很多字段 |
| **Matrix(矩阵字段)** | 每个日期、每个标的只有一个值。如 `close`、`returns`、`cap`。**模拟里无需特殊语法** | 常规字段,一天一只股票一个值 |
| **Vector(向量字段)** | 每个日期、每个标的**可能多个值**(如一天内多条新闻)。必须先用 `vec_*` 算子转成 matrix 才能和别的算子/字段一起用,否则报错 | 一天一只股票可能有 N 个值,得先"聚合成一个值" |

> ⚠️ **面试高频点**:Vector 字段不能直接进 Alpha 表达式。所有平台算子的输入都是 matrix,所以向量字段要先 `vec_avg / vec_count / vec_sum ...` 聚合成 matrix。
> 官方原文:"all the operators on platform are made for matrix input, hence use the matrix operator only after using the vec_ operators"。

## 1.2 三类字段结构(考纲明确点名)

1. **Matrix 字段**——一天一值(`close`、`returns`、`cap`)。
2. **Vector 字段**——一天多值,需 `vec_*` 聚合。常用 `vec_*` 算子:`vec_avg`、`vec_count`、`vec_sum`、`vec_max`、`vec_min`、`vec_stddev`、`vec_ir`、`vec_rank` 等。
   - 实例:`nws12_afterhsz_1_minute`(新闻发布后 1 分钟价格变动百分比)——不同股票一天内新闻数不同,要用 `vec_count(...)` 取"新闻条数"作为动量/反转信号;`scl15_d1_sentiment`(情绪分)一天多条 → `vec_avg(...)` 取当日均值。
   - 原文提醒:向量字段原始换手极高(可触 200%),**通常要配合 `ts_rank` / `ts_decay` 降换手**再组合。
3. **Group 字段**——描述"股票属于哪个分组"的字段,作为 `group_*` 算子的输入。如 `industry`、`subindustry`、`sector`、`exchange`。
   - **Group 算子**是更细粒度的横截面算子:在组**内**做比较,而非全市场。例:`group_rank(x, subindustry)` 在子行业内排名,`rank(x)` 在全市场排名。

> 还能用 `bucket()` 自己造分组:`asset_group = bucket(rank(assets), range="0.1, 1, 0.1")` 按市值分 10 桶;
> 再 `group_zscore(alpha, densify(asset_group))`。官方建议对分组先 `densify()` 去掉空组、提升表现。

## 1.3 Data Explorer:怎么找到想要的字段

> 对应 `how-use-data-explorer`。

- 本质:一个带 NLP 的字段搜索引擎,帮你在成千上万个字段里定位你想法要用到的那个。
- **用法三招**:
  1. **按想法搜**(如"market sentiment")——注意要先定好 region / delay / universe,因为有些字段只在特定区域和 delay 存在。
  2. **按条件筛**——按 coverage、type、已提交 Alpha 数、用户数过滤。例:在 CHN 区 `Company Fundamental Data` 里筛"coverage 高、且被用于至少 5 个已提交 Alpha"的字段,再按 Alpha 数排序看哪些**用得少(不拥挤)**。
  3. **搜数据集**——按 category 或名称搜,再按 coverage / value score / 拥挤度(Alpha 数、用户数)过滤。
- **3Ss 法则**:搜索要 short、simple、straightforward;用专业术语提高命中率。
- **最大化结果**:知名概念同时搜"全称 + 缩写",如 "earnings per share" 和 "eps"、"implied volatility" 和 "IV"。

## 1.4 拿到一个新字段,怎么快速理解它(6 个技巧)

> 对应 `data` 页 "Tips on working with new data"。**这套是面试能讲出细节的干货**。
> 方法:在 `None` 中性化 + `decay 0` 设置下模拟下面这些表达式,用结果里的 **Long Count / Short Count** 反推字段性质。

| # | 表达式 | 能看出的 insight |
|---|---|---|
| 1 | `datafield` | 覆盖率 ≈ (Long Count + Short Count) / (Universe Size) |
| 2 | `datafield != 0 ? 1 : 0` | 覆盖率;Long Count 是"日均非零值"数量 |
| 3 | `ts_std_dev(datafield, N) != 0 ? 1 : 0` | 数据更新频率(日/周/季)。季度更新字段 N=66 时 Long+Short Count 接近真实覆盖率;N=22(月)约 1/3;N=5(周)更低 |
| 4 | `abs(datafield) > X` | 数据边界。变 X 看 Long Count,判断字段是否被归一化到 [-1, 1] |
| 5 | `ts_median(datafield, 1000) > X` | 5 年中位数,变 X 看分布中心(均值同理) |
| 6 | `X < scale_down(datafield) && scale_down(datafield) < Y` | 分布形状。`scale_down` 类似 MinMaxScaler,保留原分布;X、Y 在 0~1 之间扫一遍看字段在值域内怎么分布 |

> 例:模拟 `[close <= 0]`,Long/Short Count 都是 0 → 说明收盘价恒为正(符合预期)。

## 1.5 两个补充概念

- **Coverage(覆盖率)**:字段在 universe 内有定义值的标的比例。低覆盖字段可用回填算子处理(`ts_backfill`、`kth_element`、`group_backfill`)。可用可视化功能看覆盖。
- **Dataset Value Score(顾问专属)**:衡量数据集"未被充分利用"的程度。顾问应优先用 value score 高的数据集做 Alpha(别和 Value Factor 混淆)。
- **Option6 IV**(期权隐含波动率):`getting-started-option6-implied-volatility-iv` 专讲。这是期权类数据的入门,涉及 `implied volatility` 字段与期权dataset 的用法。

---

# 第二部分:Alpha 回测原理

> 按你要的四个问题组织:**① 如何找到 Alpha → ② 如何回测 → ③ 如何提升质量 → ④ 如何通过提交**。
> 核心官方页:`how-brain-platform-works`(七步机制)、`simulation-settings`、`test-period`、`running-your-first-alpha`、`parameters-simulation-results`、`intermediate-pack-part-1`(六大指标)、`alpha-submission`(提交测试)、`neut-cons`(中性化)。

## 2.0 先建立一个总图景

Alpha 研究循环(官方 `list-must-read-posts-how-improve-your-alphas-are-submitted` 原文)就三步,但贯穿始终:

1. **想出一个有直觉支撑的 Alpha 想法**(hypothesis);
2. **用现有数据集和算子把它实现**成表达式;
3. **优化参数与中性化设置**,让它以最好形态通过提交。

> 官方原话:"quant research is a mixture of creative and scientific thinking"——既要有市场直觉(为什么这个因子该赚钱),又要用科学方法验证(回测、相关性、鲁棒性)。

---

## 2.1 如何找到 Alpha(产生想法)

> 不是"随机试表达式",而是 **hypothesis-driven(假设驱动)**。每个 Alpha 都从"我对市场某个低效率的直觉"出发。

**官方示例的结构(必学)**——以 `19-alpha-examples` 里的例子为例,每个都分三段:

| 例子 | Hypothesis(假设/直觉) | Implementation(实现) | 表达式 |
|---|---|---|---|
| Operating Earnings Yield | 公司 operating income 高于过去 1 年,则买;反之卖 | 用 `ts_rank` 比当前值与自身历史,基础字段 `operating_income` | `ts_rank(operating_income, 252)` |
| Appreciation of liabilities | 公允负债价值一年内上升 → 财务健康恶化 → 卖 | 负债上升做空、下降做多 | `-ts_rank(fn_liab_fair_val_l1_a, 252)` |
| Power of leverage | 高负债率(剔除财务差的公司)善用杠杆扩张 → 可能超额收益 | 用 `liabilities/assets` 造比率 | `liabilities/assets` |
| Earnings Yield Momentum | 盈利收益率近期高频高于历史 → 低估 → 买 | EPS/price 作盈利收益率代理,行业内比 | `group_rank(ts_rank(est_eps/close, 60), industry)` |
| Short-Term Sentiment Volume Stability | 10 日情绪量的高波动 = 注意力不稳 = 噪声 → 之后跑输 | 取 `scl12_buzz` 的 10 日标准差并取负 | `-ts_std_dev(scl12_buzz, 10)` |

**逐个例子中文拆解（面试口述用，英文术语全配中文）**

▍Appreciation of liabilities（负债公允价值升值）
- `Hypothesis(假设)`：一只股票的**公允负债价值（fair value of liabilities，即按市场价重估后的负债）**在一年内上升 → 说明它欠的钱变多了、财务健康在恶化 → 应该**做空（卖）**。
- `Implementation(实现)`：把"负债上升→恶化→做空"翻译成信号——负债相对自身历史越高越做空、越低越做多。
- 表达式 `-ts_rank(fn_liab_fair_val_l1_a, 252)` 逐词拆：
  - `fn_liab_fair_val_l1_a` = 公允负债价值字段；`L1` = 第一层级公允值（活跃市场可观测、最可靠的负债重估口径），`a` = 数据集/变体标识；
  - `ts_rank(x, 252)` = **时序排名（time-series rank）**：取 x 在"今天"这个值，在它自己过去 252 个交易日（约 1 年）的序列里从小到大排第几（归一化 0~1）。今天排得越靠近 1 = 负债处于年内高位 = 相对一年前上升了；排得越靠近 0 = 处于年内低位 = 下降了；
  - 前面加 `-`（负号）= 翻转方向：负债处于高位（排 1）得到最负值 → 被做空；负债处于低位（排 0）得到最正值 → 被做多。正好匹配"负债上升→做空"的假设。
- **为什么是这个表达式（而不是别的）**：假设核心是"一年内上升→恶化"，`ts_rank(..., 252)` 用一年窗口捕捉"当前负债在其自身历史里是不是处于高位"，高位即代表这一年持续走高；负号把"高负债"翻成"做空信号"。不用 `ts_delta(x, 252)`（当前减一年前差值）是因为排名对量纲不敏感、输出天然 0~1 分位，可直接当持仓权重，更稳健。
- **`ts_rank` 的语义边界（面试官可能揪）**：它只描述"当前值在自己历史里的相对位置"——谁在高位、谁在低位；**不区分"上升快"和"一直高"**（负债一直稳定很高、与从低突然拉高，ts_rank 都给接近 1），也**不直接量化"上升了多少"**。要区分变化速度/幅度得用 `ts_delta(x, d)`（当前减 d 天前）或 `ts_av_diff(x, d)`（当前减 d 天均值）。本例假设"财务恶化"是持续性状态，用"处于年内高位"作代理已够用，不必区分慢慢爬还是一直高。

**找 Alpha 的来源维度(面试能展开讲)**:
- **价值/质量类**:盈利收益率、负债结构、现金流(`operating_income`、`est_eps`、`liabilities/assets`)——基本面字段,通常配 industry/subindustry 中性化。
- **动量/反转类**:`ts_rank(x, N)`、`-ts_delta(close, 5)`、新闻/情绪强度。
- **情绪/新闻类**:向量字段(`scl12_buzz`、`nws12_*`)先 `vec_*` 聚合。
- **微观结构类**:量价(`volume*close` / `volume*vwap` 作流动性代理)、Amihud 类流动性因子。

**官方给的"实现提示"套路**:
- 能不能把"直接比数值"改成"含股价变动的比率",信号更干净?
- 观察更短窗口会不会更准?
- 这个比率在不同行业差异大 → 要不要换中性化设置(group)?

> 关键点:**想法要有经济逻辑(economic rationale)**。这是面试最看重的一点——你能讲清"为什么这个因子该赚钱",比表达式长得好看重要得多。提交时 Power Pool 还要求描述里写清 Idea、数据理由、算子理由。

---

## 2.2 如何回测(平台到底在算什么)

> 对应 `how-brain-platform-works`(七步机制)。**这是原理性问题的核心,必须讲明白**。
> 官方原话:你永远不需要手算这些,但"developing an intuition for them will help you in the Alpha making process"。

### 2.2.1 七步机制(以 `rank(-returns)`、Market 中性化、Delay 1、Decay 0 为例)

把市场数据想成一个**矩阵**:每行一个日期,每列一只股票。模拟就是把表达式对 5 年历史上每个日期都算一遍,得到每天的持仓,生成 PnL 曲线。

| 步 | 操作 | 说明 |
|---|---|---|
| **Step 1** | 对每只股票算表达式 → 生成 Alpha 向量 | 例:`rank(-returns)`。Delay 1 表示用 T-1 数据生成 T 日向量。`rank` 输出 0~1 均匀分布 |
| **Step 2** | 组内每个值减去组均值(中性化),使向量和为 0 | Market 中性化:`Alpha = Alpha - mean(Alpha)`。组也可以是 sector/industry/subindustry |
| **Step 3** | 缩放/归一化:使 Alpha 向量绝对值之和 = 1 | 得到"归一化权重",代表每只股票的相对仓位 |
| **Step 4** | 用归一化权重,从**虚拟 2000 万美元账本**给每只股票分配资金,建组合 | 权重为负 = 做空;正 = 做多。这就是**多空市场中性**——策略不依赖市场方向也能赚钱 |
| **Step 5** | 用次日实际收益,算当天每只股票的 PnL,加总 | PnL = 持仓规模 × 当日收益。当天盈亏 = 所有股票 PnL 之和 |
| **Step 6** | 对 IS 期内**每一天**重复 Step 1~5,得到每日 PnL | 表达式每天"看到"截至当天的全部数据,矩阵每天长一行 |
| **Step 7** | 把每日 PnL 累加,得到 Alpha 的累计 PnL 曲线 | 这就是模拟结果页的图 |

### 2.2.2 几个必须讲清的机制点

- **权重 vs 仓位**:Alpha 权重(中性化+缩放后)不是"买多少",而是"今天要到达的仓位比例";乘账本规模 = 美元持仓。某天和昨天的权重差 = 当天交易量。
- **Turnover(换手)怎么来**:`每日交易量 / 账本规模`。报的是模拟期平均日换手。
- **Decay(衰减)的额外一步**:若设 `decay=n`,最终权重 = 今天值与前几天衰减值的加权平均(见公式)。**越近期权重越大**。Decay 把前几天信息融进来,让 Alpha 不那么"反应过度",从而降低交易成本/换手。
- **IS（样本内）/ Semi-OS（半样本外）/ OS（样本外）(为什么分三段)**——对应 `parameters-simulation-results`:
  - **IS(样本内)**:滚动 5 年(顾问 10 年),从约 7 年前到约 2 年前,每日更新。你看到的回测都在这段。
  - **Semi-OS（半样本外）**:最近 2 年,**对评分和测试隐藏**。
  - **OS(样本外)**:提交后才跑,检验真实泛化能力。
  - 把最后 2 年藏起来 → 对 OS 表现和分数更有信心。
- **Test Period(防过拟合)**——对应 `test-period`:可在 IS 内再切出 Train / Test。用 Train 开发,在 Test 验证;两段都好才是强候选。**注意:必须点 "Show test period" 才能提交**(图上橙色线 = Test 期)。

### 2.2.3 模拟设置(Simulation Settings)逐项含义

> 对应 `simulation-settings`。面试常问"这些设置分别干嘛"。

| 设置 | 含义 | 要点 |
|---|---|---|
| **Region/Universe** | 区域与股票池。目前所有用户仅 USA 可用;EUR/ASI 仅顾问 | `US: TOP3000` = 美国流动性前 3000(按日均美元成交额) |
| **Delay** | 数据相对决策时间的可得性(假设何时能交易) | Delay 0 = 当天数据当天交易(激进);Delay 1 = 用今天数据明天交易(保守,自动应用,表达式不用写) |
| **Decay** | 过去 n 天线性衰减,融合近期与历史 | 公式见下。降换手但过大削弱信号 |
| **Truncation** | 单只股票最大权重。`0` = 不限制 | 合法 0~1;建议 0.05~0.1(5%~10%),防单股暴露过重 |
| **Neutralization** | 让策略市场/行业/子行业中性 | Market:`Alpha = Alpha - mean(Alpha)`,使多空抵消 |
| **Pasteurize** | 把非股票池内标的输入置空（池外置 NaN） | 默认 **On = 全局生效**（整个表达式所有输入一起过滤）；要关成 **Off** 才有意义——关掉后用 `pasteurize(x)` 只对指定的那一个字段手动过滤，其余字段不过滤 |
| **NaN Handling** | NaN 怎么处理 | On:时序算子全 NaN 返 0,组算子返组值(增覆盖但引入歧义);Off:保留 NaN,需手动处理 |
| **Unit Handling** | 单位不兼容时报警(如 price + volume)| 警告不阻断提交 |

**Decay 公式**:
```
Decay_linear(x, n) = (x[date]*n + x[date-1]*(n-1) + ... + x[date-n-1]) / (n + (n-1) + ... + 1)
```

---

## 2.3 如何提升 Alpha 的质量(读懂指标 + 对症下药)

> 对应 `intermediate-pack-part-1`(六大指标原文)、`parameters-simulation-results`、`neut-cons`、`alpha-submission`(子池/权重测试)、`list-must-read-posts-...`(七篇必读)。

### 2.3.1 六大指标(面试必背公式与口径)

> 来源 `intermediate-pack-part-1` 与 `parameters-simulation-results`,两处公式一致。

| 指标 | 公式 | 含义 / 门槛 |
|---|---|---|
| **Sharpe** | `√252 × Mean(PnL)/Stdev(PnL)` ≈ `15.8 × IR` | 收益一致性。提交门槛:Delay0 > 2.0,Delay1 > 1.25 |
| **IR** | `Mean(PnL) / Stdev(PnL)` | 预测能力;越高越一致 |
| **Turnover** | `Dollar Trading Value / Booksize` | 交易频率。门槛:1% < T < 70%。越低交易成本越低 |
| **Fitness** | `Sharpe × √(|Returns| / max(Turnover, 0.125))` | 综合质量。门槛:Delay0 > 1.3,Delay1 > 1.0 |
| **Returns** | `Annual Return = Annualized PnL / (0.5 × BookSize)` | 资本回报(%)。账本恒 2000 万,杠杆基准 1000 万 |
| **Drawdown** | `最大峰谷回撤金额 / (0.5 × BookSize)` | 最大回撤(%)。越低越好 |
| **Margin** | `PnL / Total Dollars Traded` | 每交易 1 美元赚多少 |

**Fitness 是关键优化目标**:`提高 Sharpe(或 Returns)、降低 Turnover` 都能提 Fitness;但两者常此消彼长。改完看 Fitness 是否升,就知道改动是否正向。

**Fitness 评级对照(IS Summary 里的 Spectacular/Excellent/...)**:

| 评级 | Delay 1 Fitness | Delay 0 Fitness |
|---|---|---|
| Spectacular | > 2.5 | > 3.25 |
| Excellent | > 2.0 | > 2.6 |
| Good | > 1.5 | > 1.95 |
| Average | > 1.0 | > 1.3 |
| Needs Improvement | ≤ 1 | ≤ 1.3 |

### 2.3.2 三大常见坑(官方"Troubleshooting")

> 来自 `intermediate-pack-part-1`。这是"提升质量"的实操抓手。

1. **Low Sharpe**(最常见):要么**提高 Alpha 收益**,要么**降低波动**。官方指向论坛帖 "How to get a higher Sharpe"。
2. **Weight test 不过**(资金过度集中):报错三种——"单股最大权重 > 10%"/"权重过集中"/"太少股票分到权重"。官方修法:加 `rank` 这类区间归一化函数、把 truncation 设 0.1、用 `ts_backfill` 提覆盖。
3. **Sub-Universe Sharpe 不过**:子池 Sharpe 必须高于阈值(阈值随子池规模缩小)。可**扩大 universe**(如选 TOP3000)来提升子池 Sharpe。

### 2.3.3 中性化:为什么是提升质量的杠杆

> 对应 `neut-cons`。这是原理题高频。

- **本质**:把原始 Alpha 值分组,组内做"减均值"归一化。结果组合半多半空,抵御市场/行业冲击。
- **层级**:sector ⊃ industry ⊃ subindustry。例: Industrials 板块 ⊃ Machinery 行业 ⊃ Agricultural & Farm Machinery 子行业。
- **`Neutralization` 设置 与 `group_neutralize(x, group)` 等价**。若用 `group_neutralize` 作最后算子,设置里 Neutralization 设 `None`、Decay/Truncation 设 0,把衰减/截断直接写进表达式。
- **按数据集类别选中性化(官方推荐表,挑重点)**:
  - Fundamental / Analyst / Earnings / Short Interest / Insider / Sentiment → **Industry**(基本面按行业影响不同)
  - News / Social Media → **Subindustry**(同类新闻对同行业不同公司影响也不同,如 CEO 变动对 Twitter vs Apple)
  - Option → **Market 或 Sector**(期权对股价影响跨行业相似)
  - Price Volume → **Market**(通用量价逻辑全市场适用,过度行业中性化反而掉表现)
  - Model → 四种都试,看子类
- **Tips**:永远给中性化选个值;流动性好的大 universe 用大分组(股票多),不流动的用小分组;EUR/ASI 用 country/exchange 中性化。

### 2.3.4 降换手 / 降相关 的通用手法(七篇必读)

> 来自 `list-must-read-posts-how-improve-your-alphas-are-submitted`,这是官方给的"质量提升方法论清单":

| 目标 | 官方推荐帖 |
|---|---|
| 提 Sharpe | How to get a higher Sharpe |
| 提 Returns | 5 ways to potentially increase returns |
| **降 Correlation** | How to reduce correlation of a good alpha |
| **降 Turnover** | Using trade_when for Event/Low-Turnover Alphas |
| 降 PnL 波动 | How to smooth the PnL curve |
| 中性化直觉 | Neutralization 专题(`neut-cons`)|
| **防过拟合** | How to avoid overfitting |

> 结合你项目里的实战经验(可作面试素材):
> - **降换手**:`trade_when` 门控、`ts_decay_linear` 平滑、给权重加 0.5 系数。
> - **降相关(真正的瓶颈)**:同构候选严禁扎堆;换"独有成分腿"、换分组粒度(subindustry→industry)、中性化投影(只救 corr 0.70~0.72 的近门槛,一个几何进 1~2 条就饱和)、`/cap` 缩放破墙。相关是动态的——提交后要对剩余池重检。
> - **防过拟合**:用 Test Period 切 Train/Test;IS 好但 OS 差的要警惕。

### 2.3.5 Sub-Universe 测试怎么过(鲁棒性)

> 对应 `how-pass-sub-universe-test` 与 `alpha-submission`。

- **目的**:确保你的 Alpha 不只在大 universe 赚钱,在"下一个更流动的(更小的)universe"也大体有效。例:在 TOP3000 提交,平台还会查 TOP1000。若利润主要来自不流动的小票 → 不鲁棒 → 不准提交。
- **阈值公式**:`subuniverse_sharpe ≥ 0.75 × √(sub_size / alpha_size) × alpha_sharpe`
  - 例:TOP3000、alpha_sharpe=2.73 →  cutoff = 0.75 × √(1000/3000) × 2.73 = **1.18**;若 TOP1000 实测 Sharpe 跌到 1.17(<1.18)→ 不过。
- **官方改进建议**:
  - 避免用公司规模类乘子(如 `rank(-assets)`、`1 - rank(cap)`),会把权重偏向流动/不流动一侧。
  - 对信号里"流动/不流动"两部分**分别 decay**:如 `ts_decay_linear(signal,5)*rank(volume*close) + ts_decay_linear(signal,10)*(1-rank(volume*close))`。
  - 一步步查改进,看是不是某次改动让子池变差。
  - 实在过不了 → 可能信号本就不鲁棒,丢掉反而躲开一个坏 Alpha(IS 好 ≠ OS 好)。

#### 官方那两条式子逐段拆解(面试被问到要能拆开讲)

| 片段 | 是哪个字段/算子 | 人话 |
|---|---|---|
| `assets` | 字段 = **总资产**(资产负债表科目) | 公司手上总资产有多少 |
| `cap` | 字段 = **市值**(`market capitalization` 缩写) = 股价 × 总股本,量纲是 price×股数 | 公司值多少钱 |
| `rank(-assets)` | 横截面排名取负 | 资产越大排名越靠前(0~1,大→1),取负后变成"越小排名越靠前" |
| `1 - rank(cap)` | 市值排名取 `1 -` | 大盘子→接近 0、小盘子→接近 1,等于把小盘权重放大 |
| `volume*close` | 成交量 × 收盘价 | 官方给的"流动性近似":成交额越大越好买卖。**注意收盘价 ≠ 当天成交均价**,真实成交额 = `volume * vwap`(vwap 是成交量加权均价,平台 pv1 字段,见下方订正) |
| `rank(volume*close)` | 成交额横截面排名 | 池子里按成交额从低到高排,0~1 |
| `ts_decay_linear(signal, 5)` | 时序算子:过去 5 天**线性衰减加权平均**(近重远轻,权重和 = 5×6/2 = 15) | 平滑一下、偏重最近几天 |
| `ts_decay_linear(signal, 10)` | 同上但看 10 天 | 更钝、更平滑、换手更低 |
| 整个式子 | 两者的**加权平均** | 权重的和 = rank + (1−rank) = **1**,所以是加权平均、不会整体放大幅度 |

**为什么这么写比原来强**(官方原文只说"try",没给理由,以下是按结构推的):

1. 原来 `ts_decay_linear(signal,10)` 一刀切,流动性好的烂票一视同仁 → 便宜的票信号被磨钝了、贵的票摩擦又没压住。
2. 分开之后:流动性好(成交额排名高)的票,decay 5 的权重 = r、decay 10 的权重 = 1−r → **短 decay 占多,信号更贴当前**;流动性差(排名低)的票 → **长 decay 占多,更少调仓**。
3. 一句话:**好买卖的让它新鲜点,难买卖的让它少动点。** 两头都占,比统一取中间值好。

**面试能讲的诚实边界**(别把官方的话说成铁律):

- 官方没保证换手一定降。`rank(volume*close)` 本身每天会动(大市成交额天天变),权重天天重排,**有可能反而抬换手**,必须实测。
- decay 短了信号强度会掉(S↔TO 跷跷板),我们实测「decay 拉大」已判死,这条也是对 decay 轴动手,**要一次只改一条、交前跑三道体检**,别批量套全池。
- 官方第三句"一步步查"就是防这个:某次改动 IS 变好、子池反而挂了。

#### 我们池子实测:这两条对我们哪条对口(1004 核)

> 数据:`data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv`,456 条未提交合格候选。

| 检查项 | 实测 | 结论 |
|---|---|---|
| 是否用了官方点名的规模**乘子**( `rank(-assets)` / `1-rank(cap)` ) | **0 条**。表达式里带 `cap` 的 21 条全都是 `bucket(rank(cap),range=...)` 当**分桶分组依据**(在市值分片内做组内排名),不是乘子 | 第一条对我们**不适用,已合规**,不用改 |
| 456 条里做过"多 decay 混合"的 | **0 条**(整池只有 3 条含过一次 `ts_decay_linear`,无一条含两个以上) | 第二条**全新路径,没走过** |
| 换手超我们门槛(TO>20%)的 | **228 条**(SF 全部 ≥4.0,中位 4.57;302 条 SF≥4.4) | 有对口改造对象,但 SF 全在中位 4.57 的**高位区**,decay 轴边际空间很可能已见顶(我们实测 decay 在 SF 峰值区 3.95→3.99 就封顶) |
| 子股票池测试失败(LOW_SUB_UNIVERSE_SHARPE)记录 | 表里 `fails` 列**全空**(456/456) | 这表只收"无 FAIL"的合格品,**子池测试挂没挂要看判决书/Submission 页**,不能拿这张表当子池结论 |

**所以:值得一试,但只对换手高的那 228 条里挑几条做试点,不是全池铺开。**

#### 再往下挖一层:真正卡子池的那 89 条,官方这两条救不了

> 数据:`candidates_all.csv` 全表 1098 条,按 `fails` 里有没有 `LOW_SUB_UNIVERSE_SHARPE` 筛出 89 条。

- **FAIL 分布**(全表):`LOW_FITNESS` 281 / `LOW_SHARPE` 242 / **`LOW_SUB_UNIVERSE_SHARPE` 89** / `CONCENTRATED_WEIGHT` 32 / `LOW_TURNOVER` 20 / `HIGH_TURNOVER` 10。
- **这 89 条的真实状态**:**S 中位 0.42、均值 0.50、最小 −1.01**,**62 条连 S<1.0 都够不着**,**其中 71 条同时挂着 `LOW_SHARPE + LOW_FITNESS + LOW_SUB_UNIVERSE_SHARPE` 三连 FAIL**。
- 对照那 456 条已达标的:**S 均值 2.67、最小 2.12** —— 差了 4 倍多。
- 这 89 条里 **0 条**含官方点名的规模乘子、**0 条**用 `rank(cap)`;decay 集中在 4/8/3/2(小值),universe 86 条在 TOP3000。

**结论(面试可以这么讲,是数据说话)**:

> 卡子股票池测试的 89 条,大部分不是"流动性分布歪了",是**信号本身就没劲**——S 中位才 0.42,三连 FAIL。官方那两条(去掉规模乘子、按流动性分别 decay)治的是"权重偏向某一侧导致小池子里失效",**对症的是"信号在池内有效、只是换 subgroup 就塌"的情况**;我们这 89 条连原池 Sharpe 都不及格,属于官方自己说的 "don't get upset... Most likely, you just dodged a bad alpha",**该丢就丢**。

**真正值得动手的仍然只有那 228 条换手超标的**,而且它们卡的是我们自己定的 `TO≤20%` 门槛,不是子池测试。

---

#### 2.3.6 这两条建议能不能落到后续出量上(李工 1004 问"是否有用、能否保证应用到提升")

**(1) `volume*close` 里的 `close` 应该换成 `vwap`(口径订正)**

- **李工的质疑成立**:一天中价格从开盘到收盘一直在动,收盘价只是当天最后一个成交价,`volume * close` 算出来的不是真实成交额。真实成交额 = 成交量 × **当天成交均价**,平台 pv1 数据集里就有这个字段 = **`vwap`(Volume Weighted Average Price,成交量加权均价)**。
- **为什么影响不大(但也不是零)**:我们池子里这 33 条全是先 `rank(ts_mean(volume*close,20))` **排完名再用的**。rank 只对排序敏感、对绝对值不敏感,而"收盘价偏高还是偏低"在横截面上是**随机噪声**(有的票当天涨、有的跌),噪声在大量平均后排序基本不变。
- **真正有偏的地方**:长期单边上涨的票,收盘价会系统性高于均价 → 它的成交额被**持续高估** → 分桶边界会往"活跃"一侧偏。所以是**小偏、但有方向**,不是无害。
- **改进写法(零成本、不新增数据集)**:`volume*close` → `volume*vwap`。`volume` 和 `vwap` **同在 pv1 数据集**,换完不会多占一个数据集、不伤 ATOM 资格(对比:`cap` 在 MATRIX 数据集,乱加会多占一个)。
- **我们池子实测**(`candidates_all.csv` 1098 条):含 `volume*close` 的 **33 条**(31 条无 FAIL),含 `vwap` 的只有 29 条且**全是当反转腿用**(`rank(-ts_delta(vwap,2))`),**没有一条**拿 `volume*vwap` 当流动性/分桶依据 → 这块是空的,可以直接改。
- **可直接改的达标候选 4 条**(TO≤20% 且 tS≥1.25 且无 FAIL):`j23kkkKj`(S2.64/F2.02/SF4.66)、`d5OJJb2g`(SF4.04)、`j23kKP5Z`(SF3.95)、`zqY7nQ5G`(SF3.58)。改造方式就是表达式里 `volume*close` → `volume*vwap`,**改完必须重跑,不保证 S/F 一定涨**(分桶边界会动)。

**(2) 官方那条"按流动性分别 decay"——我的判断:能当工具用,不能当通用配方**

| 判断项 | 结论 | 依据 |
|---|---|---|
| 官方第一条(别用规模乘子) | **用不上** | 全表 1098 条 0 条违规,我们 21 条带 `cap` 全是 `bucket(rank(cap),...)` 当分桶依据,是中性化动作不是乘子 |
| 官方第二条(多 decay 混合) | **只在压换手时试点** | 全池 0 条含 ≥2 个 `ts_decay_linear`,从没走过,属新轴 |
| 为什么不能全池铺 | **decay 轴在峰值区已封顶** | 456 条达标候选 SF 中位 4.57、302 条 ≥4.4(峰值区);实测配方三 decay 轴 3.95→3.99 就卡线,atoms 里「decay 拉大」早已判死 |
| 对口对象 | **换手超标的 24~228 条**,不是子池那 89 条 | 89 条 S 中位 0.42 原池就不及格,救不了 |

- **落地路径(一次只动一条,守单变量控制铁律)**:① 先做 (1) 的 `volume*vwap` 正确化(零成本、不改结构);② 在 TO>20% 那批里挑 2~3 条试多 decay 混合写法,交前跑 check_fail_hist / one_corr / pair_now 三道体检;③ 只统计改完的换手和 SF,**涨了再谈配方化,没涨就当这条轴走不通、记进判死清单**。
- **面试诚实口径**:官方原文写的是 `volume*close`,这是官方的近似写法;严格来说应该用 `volume*vwap`。作为流动性代理(后面套了 rank)影响很小,但**别把它讲成精确成交额**。


---

## 2.4 如何通过提交(过哪几道关)

> 对应 `alpha-submission`。**只有提交了的 Alpha 才计分**(ACTIVE 状态,出现在 OS 标签页)。提交按钮在结果页 Submission 标签。

### 2.4.1 提交前必过的 6 项测试(Submission Criteria)

| 测试 | 用户门槛 | 说明 |
|---|---|---|
| **Fitness** | Delay0 > 1.3 / Delay1 > 1.0(Average 以上) | 综合质量门槛 |
| **Sharpe** | Delay0 > 2.0 / Delay1 > 1.25 | 一致性门槛 |
| **Turnover** | 1% < T < 70% | 太低(<1%)也不行 |
| **Weight** | 任何股票最大权重 < 10%;每年足够多天有足够多股票分到权重 | 防过度集中 / 防太少股票 |
| **Sub-universe** | 子池 Sharpe 高于阈值(随规模缩放) | 鲁棒性,见 2.3.5 |
| **Self-Correlation** | PnL 自相关 < 0.7;**或** Sharpe 比所有相关 Alpha 高至少 10% | 防扎堆同构 |

> **Self-Correlation 细则**(面试易考):
> - 自相关窗口 4 年;inner correlation 取 PnL 时间交集。
> - 即使 corr ≥ 0.7,只要你的 Sharpe 比所有相关 Alpha **高 ≥10%** 也能提交——允许在已有 Alpha 上改进。例:旧 Alpha Sharpe 3.18,新 Alpha Sharpe ≥ 3.5 即可提交。对比用的 Sharpe 在 correlation summary 表里可见。

### 2.4.2 测试顺序与报错信息

> 来自 `alpha-submission` "Interpreting Status Messages"。**按这个顺序跑,挂在第一道就停**。

| # | 失败项 | 提示 |
|---|---|---|
| 1 | Weight | Maximum weight > 10% / 权重过集中 / 太少股票分到权重 |
| 2 | Correlation | Reduce max correlation |
| 3 | Fitness | Improve fitness |
| 4 | Delay0 但 checkDelay1Sharpe 不过 | Alpha better suited for Delay 1 |
| 5 | SubUniverse | Improve Sharpe in SubUniverse |

> 例:过了 1/2/3 但挂 4 → 建议 "Improve Sharpe or reduce turnover"。

### 2.4.3 提交策略(官方原话,面试能引用)

- **别一过线就提交**:把想法改到"性能和相关性都最好"的版本再交。
- **但也别在单个想法上耗太久**:通常**试低相关的新想法,比打磨高相关的老想法更值**。
- **低相关比小幅提性能更重要**:略差性能但低很多相关的 Alpha,优于略好性能但高相关的 Alpha。

### 2.4.4 Alpha 生命周期与状态

> 来自 `parameters-simulation-results` "Alpha Statuses"。

- `UNSUBMITTED` → 模拟完未提交。
- `ACTIVE` → 提交后。顾问的 ACTIVE Alpha 可累积权重、参与季度付款,直到依赖数据集停用或平台停用。
- `DECOMMISSIONED` → 数据集不可用或 OS 长期表现差。不再累积权重、不参与付款。

### 2.4.5 特殊 Alpha 类型(了解一下,面试可能问)

- **ATOM**:字段只来自 1 个 dataset(分组字段不计数) —— **dataset 只有 1 个,字段可以随便多个**,同 dataset 的 10 个字段照样是 ATOM。可跳过 IS Ladder Sharpe 测试,但必须过常规 IS 测试 + 2Y Sharpe 测试。
- **Pyramid**:region+delay+dataset category 的组合(如 USA-D1-analyst)。单 Alpha 最多贡献 2 个 pyramid。
- **Power Pool**:Sharpe ≥ 1.0、算子数 ≤ 8、唯一字段 ≤ 3、Power Pool 相关 < 0.5(超了要 Sharpe 高 10%)、过换手/子池/鲁棒池测试,且**必须写描述(Idea + 数据理由 + 算子理由)**。

---

# 第三部分:面试高频自测(对着讲一遍)

> 用下面这些问题当"口述对练"提纲。能用自己的话答出来,原理就过关了。(模拟题不在本资料范围,按你的要求不练。)

**数据篇**
1. Matrix 和 Vector 字段区别?向量字段为什么不能直接进表达式?用什么算子转?
2. Group 字段是干嘛的?`group_rank` 和 `rank` 差在哪?怎么自己造分组?
3. 拿到一个新字段,怎么快速判断它的覆盖率、更新频率、取值范围?(6 技巧能说几个)
4. Data Explorer 的 3Ss 法则是什么?为什么有些字段要先定 region/delay 才能搜到?

**回测原理**
5. BRAIN 回测的七步机制讲一遍——从"表达式"到"累计 PnL 曲线"中间发生了什么?
6. 账本为什么是 2000 万、杠杆基准为什么是 1000 万?多空市场中性怎么来的?
7. IS（样本内）/ Semi-OS（半样本外）/ OS（样本外）三段分别是什么?为什么要把最后 2 年藏起来?Test Period 干嘛用?
8. Delay 0 和 Delay 1 的区别?Decay 是怎么降换手的?

**提升质量**
9. 六大指标公式能写几个?Fitness 为什么是核心优化目标?
10. Sharpe 不够高怎么提?Weight test 三种报错分别怎么修?
11. 中性化的本质是什么?不同数据集类别官方推荐哪种中性化?
12. Sub-Universe 测试的目的和阈值公式?为什么 `rank(-assets)` 这类会害你过不了?

**提交**
13. 提交前 6 项测试分别是什么门槛?
14. Self-Correlation 的 0.7 和"高 10%"双规则怎么理解?
15. 测试挂了按什么顺序报?Weight 挂了和 SubUniverse 挂了提示分别是什么?
16. 官方说"低相关比小幅提性能更重要",为什么?(→ 组合 diversification,OS 鲁棒性)

---

> **本文档配套原文位置**:`docs/study/learn/docs/` 下
> `05_understanding-data/*`(数据)、`02_create-alphas/*`(回测设置/机制)、
> `04_interpret-results/*`(指标/提交/子池)、`01_discover-brain/04_intermediate-pack-part-1.md`(六大指标)、
> `06_advanced-topics/*`(中性化/改进必读)。需要看配图或英文原句,直接开对应文件。
