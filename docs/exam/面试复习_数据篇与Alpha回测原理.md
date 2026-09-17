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

**找 Alpha 的来源维度(面试能展开讲)**:
- **价值/质量类**:盈利收益率、负债结构、现金流(`operating_income`、`est_eps`、`liabilities/assets`)——基本面字段,通常配 industry/subindustry 中性化。
- **动量/反转类**:`ts_rank(x, N)`、`-ts_delta(close, 5)`、新闻/情绪强度。
- **情绪/新闻类**:向量字段(`scl12_buzz`、`nws12_*`)先 `vec_*` 聚合。
- **微观结构类**:量价(`volume*close` 作流动性代理)、Amihud 类流动性因子。

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
- **IS / Semi-OS / OS(为什么分三段)**——对应 `parameters-simulation-results`:
  - **IS(样本内)**:滚动 5 年(顾问 10 年),从约 7 年前到约 2 年前,每日更新。你看到的回测都在这段。
  - **Semi-OS**:最近 2 年,**对评分和测试隐藏**。
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
| **Pasteurize** | 把非 universe 内标的输入置 NaN | 默认 On;可手动 `pasteurize(x)` 关掉用 Off |
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

- **ATOM**:只用 1 个 dataset 的字段(分组字段不计数)。可跳过 IS Ladder Sharpe 测试,但必须过常规 IS 测试 + 2Y Sharpe 测试。
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
7. IS / Semi-OS / OS 三段分别是什么?为什么要把最后 2 年藏起来?Test Period 干嘛用?
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
