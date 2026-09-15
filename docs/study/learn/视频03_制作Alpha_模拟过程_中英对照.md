# 视频 03｜Making an Alpha: Simulating an Alpha（制作 Alpha：模拟一个 Alpha）— 中英逐段对照

> **归档信息**
> - 课程页：https://platform.worldquantbrain.com/learn/courses/introduction-alphas/making-alpha-simulating-alpha
> - 课程组：`introduction-alphas`（Introduction to Alphas 系列，共 6 个视频）
> - 视频标题：**Making an Alpha: Simulating an Alpha** ｜时长 **3 分 29 秒** ｜语言：英文
> - 视频源：YouTube（uid `AMzPHBintkM`）
> - 字幕来源：**平台官方 transcript**（经 `GET /video-courses` 取得，非本地 ASR），抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译（universe→股票池、instrument→标的、positions→持仓、neutralization→中性化）；译文中括号内英文为原词。
> - ⚠️ 官方字幕是自动生成的，本视频未发现影响语义的 ASR 误识（详见文末「字幕勘误」）。

---

## 一、中文译文

### 1. 模拟一个 Alpha 的完整步骤

在前面几个视频里，我们已经了解了什么是 Alpha、模拟设置有哪些、以及如何分析各项表现参数。现在来讨论：模拟一个 Alpha 时你应该按什么步骤走，以及在等待模拟结果的过程中，平台后台在做什么。

**第一步，想出一个创建 Alpha 的**想法（idea）。** 它可以非常简单，也可以非常复杂。

**第二步，想清楚你打算用哪些**算子（operators）和**数据集（data sets）**来实现这个想法。

**第三步，为你的想法确定合适的**模拟设置（simulation settings）**。

**第四步，填入模拟设置，以及一条由**数据、算子和常数**组成的 Alpha 表达式——也就是你决定用来实现这个想法的代码。

输入代码会**对每个标的分别求值**，从而构建出一个投资组合。平台随后按表达式的值**等比例**给每只股票分配投资，持有期为**一天**。

### 2. 后台在做什么：从表达式到持仓

这个过程**每天重复一次**。如果用户指定了**中性化（neutralization）**，那么**原始值**——也就是表达式的值——**不会被直接使用**，而是要先施加中性化运算，算出**最终值**。

有了最终值之后：

- **负数**对应**空头头寸（short positions）**；
- **正数**对应**多头头寸（long positions）**。

平台基于每天的持仓计算 **PnL（盈亏）** 并展示给用户。**NaN 表示不持仓**，因此也就**不产生 PnL**。

### 3. 模拟完成后拿到什么

模拟完成后，平台会把结果呈现给你，结果分两种形式。

**第一种：汇总表现参数（aggregate performance parameters）**，例如：

- 夏普比率（Sharpe ratio）
- 收益率（returns）
- 换手率（turnover）
- 回撤（drawdown）

你要分析这些指标，判断结果是否令人满意，还是需要继续改进你的信号。

**第二种：汇总表现参数的详细拆解（detailed analysis）**，包括图形化结果，用来呈现：

- **资金分布（capital distribution）**
- **覆盖率（coverage）**
- **夏普比率（Sharpe ratio）**
- **不同市值分组的股票**共同产生的 PnL
- **不同行业内的股票**共同产生的 PnL
- **所有板块（sectors）**归总后的 PnL

### 4. 关键判断标准：分散度 = 稳健性

请记住：**表现来源在板块、行业、市值上的分散度越高，你的 Alpha 就越稳健（robust）。**

我们会在之后所有的视频里沿用这套流程，并且我会用 Alpha 示例来讲解：如何用不同的算子和数据集来创建 Alpha。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1. 模拟一个 Alpha 的完整步骤**

> In the past few videos, we have learned about Alphas, the simulation settings and how to analyze the performance parameters.
> Now let's discuss what steps you should take while simulating an Alpha and what goes on in the background while you wait for the simulation results.
> The first thing you need to do is think of an idea to create an Alpha.
> It can be very simple or complex.
> Next, you should think of the operators and the data sets you will use to implement your idea.
> After that, you need to decide upon the right simulation settings for your idea.

**2. 后台在做什么：从表达式到持仓**

> The next step is to enter the simulation settings and an Alpha expression that consists of data, operators and constants, which you have decided to implement your Alpha idea.
> The input code is evaluated for each instrument to construct a portfolio.
> The platform will then allocate an investment in each stock for one day period in proportion to the values of the expression.
> The process repeats each day.
> And if the user specifies the neutralization, the raw values - that is the values of the expression - aren't used directly, and the neutralization operation is applied to calculate the final value.
> With the final values, negative numbers would result in short positions.
> The positive numbers will result in long positions.
> And based on their daily positions, PnL is calculated and displayed to the user.
> The NaN means no positions, and thus there would be no PnL.

**3. 模拟完成后拿到什么**

> Once the simulation is complete, the platform will present to you with the results.
> They come in two forms.
> First, it provides you an aggregate performance parameters like the Sharpe ratio, the returns, the turnover and the drawdown.
> You will analyze these to decide if the results are satisfactory or if you need to work more to improve your signal.
> You will also get a detailed analysis of the aggregate performance parameters.
> These would include graphical results representing the capital distribution, the coverage, the Sharpe ratio and the PnL generated from different capitalization stocks grouped together or different stocks within industries, all sectors grouped together.

**4. 关键判断标准：分散度 = 稳健性**

> Keep in mind that the more diversified the sources of performance across sectors, industries and capitalization, the more robust your Alpha is.
> We will follow this process in all our future videos, and I will use Alpha examples to explain how to use different operators and data sets for creating Alphas.

---

## 三、字幕勘误（官方字幕为自动生成）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 2 段 | `the current days positions` | 缺撇号，应为 `current day's positions`，语义无歧义 |
| 第 3 段 | `the platform will present to you with the results` | 口语冗余（present to you with），非误识 |
| 全篇 | 对比视频 01/05 出现的 `improvise`（应为 `improve`） | **本视频未出现该误识**，原文即为正确的 `improve your signal` |

**本视频未发现影响语义的 ASR 误识。**

---

## 四、本视频的量化术语对照

| 英文 | 中文 | 说明 |
|---|---|---|
| instrument | 标的 | 可交易的金融工具（此处指单只股票） |
| evaluate (per instrument) | 逐标的求值 | 表达式在每个标的上分别计算 |
| portfolio | 投资组合 | 由多头与空头持仓构成 |
| final value | 最终值 | 施加中性化之后的表达式值 |
| short position / long position | 空头 / 多头头寸 | 负值做空、正值做多 |
| NaN | 空值 | 表示不持仓，不产生 PnL |
| aggregate performance parameters | 汇总表现参数 | Sharpe / Returns / Turnover / Drawdown |
| capital distribution | 资金分布 | 权重集中度图示 |
| coverage | 覆盖率 | 有持仓的标的占比 |
| capitalization | 市值 | 用于分组分析（大盘/中盘/小盘） |
| sectors | 板块 | 比行业更粗的分组层级 |
| robust | 稳健 | 表现来源分散、不易因单一场景失效 |

---

## 五、与本视频相关的面试考点

- **完整流程**：想法 → 选算子和数据集 → 定模拟设置 → 写表达式 → 逐标的求值构建组合 → 按值分配权重 → 每日重复 → 算 PnL。
- **中性化发生在哪一步？** 表达式值（原始值）**不直接用**，先做中性化得最终值，再决定多空方向。这是"raw value vs final value"的关键区分。
- **符号规则**：最终值为负 → 做空；为正 → 做多；NaN → 空仓不产生 PnL。这条在调试表达式时是判断方向的最直接依据。
- **两类输出**：汇总参数（4 个） + 明细拆解（资金分布 / 覆盖率 / Sharpe / 按市值·行业·板块分组的 PnL）。
- **面试高频结论**：**分散度越高，Alpha 越稳健**——因为量化 Alpha 交易的是"一大篮子股票"，而不是少数几只。
