# Alpha 入门培训系列（introduction-alphas）｜6 个视频中英对照合集

> **合集归档信息（本文件由多个视频译文合并而成）**
> - 官方课程组：`introduction-alphas`
> - 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/alpha>
> - 含视频：**6 个**（清单见下表）
> - 字幕来源：**平台官方 transcript**（`GET /video-courses`），非本地 ASR；抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译；括号内英文为原词
> - 合并工具：`src/tools/merge_video_notes.py`
> - ⚠️ 官方字幕为自动生成，ASR 误识在各视频正文内就地标注，另见文末「附录 A：字幕勘误汇总」

## 目录

| # | 视频标题 | 源文件 |
|---|---|---|
| 1 | What is an Alpha?（什么是 Alpha） | `视频01_什么是Alpha_中英对照.md` |
| 2 | Making an Alpha: Simulation Settings（制作 Alpha：模拟设置） | `视频02_制作Alpha_模拟设置_中英对照.md` |
| 3 | Making an Alpha: Simulating an Alpha（制作 Alpha：模拟一个 Alpha） | `视频03_制作Alpha_模拟过程_中英对照.md` |
| 4 | Alpha expression to PnL Chart（从 Alpha 表达式到 PnL 曲线） | `视频04_从表达式到PnL曲线_中英对照.md` |
| 5 | Simulation Results（模拟结果） | `视频05_模拟结果_中英对照.md` |
| 6 | OSTests in an Alpha（Alpha 的样本外测试） | `视频06_Alpha的样本外测试_中英对照.md` |

---

# 视频 1｜What is an Alpha?（什么是 Alpha）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/alpha> ｜ 时长：4 分 14 秒 ｜ 视频源：Vidyard（uid `T41ioYrY5YS174NiMZZFhy`）
> 源文件：`视频01_什么是Alpha_中英对照.md`

## 一、中文译文

### 1. Alpha 是什么

对 WorldQuant 来说，**Alpha 是用于预测金融标的表现的数学模型**。

当我们开发一个 Alpha 时，我们假定手里有一个**虚拟投资组合（fictitious portfolio）**，目标是预测：资金应当如何分配到一组金融标的上。在这个过程中，我们要在维持不错收益的同时，确保有**下行保护（downside protection）**。

为了做到这一点，我们开发**股票多空市场中性（equity long-short market-neutral）**的 Alpha。这类投资之所以有吸引力，是因为它们预期能产生**显著优于纯多头（long only）组合的风险调整后收益（risk adjusted returns）**。我们来理解一下这句话的含义。

### 2. 做多与做空

你可能知道，对一只股票建立**多头头寸（long position，即做多）**就是买入它——股价上涨，你就赚钱。

反过来，建立**空头头寸（short position，即做空）**是指：借入你并不持有的股票（通常从券商处借入），把它卖出，然后指望它下跌。等到它跌了，你就可以用比卖出价更低的价格买回来，把借来的股票还掉。

### 3. 股票多空市场中性策略

股票多空市场中性投资是一种主要由**对冲基金（hedge funds）**使用的策略。它的做法是：以**等额资金**建立多头头寸（预期上涨的股票）和空头头寸（预期下跌的股票）。

如果判断成真、且两边头寸规模相等，对冲基金就能获利。话虽如此，**即使多头那一侧出现了亏损，这个策略依然可能奏效**。你可能想问为什么？因为做空的盈利会大于多头的亏损，这种情况下对冲基金仍然获益。

所以，股票多空策略的目标是：**尽量减少对整体市场的敞口（exposure），转而从两只股票之间的差值——也就是价差（spread）——的变化中获利。**

### 4. 股票池与 Alpha 向量

开发一个 Alpha 时，你必须先定义**要交易哪些标的**，我们称之为**股票池（universe）**。股票池可以是按**流动性（liquidity）**筛选出的一组美股。

Alpha 是股票池中各股票**预测值**构成的**向量（vector）**。每一个取值每天都会变化，它有两个属性：

- 第一，**Alpha 的符号（sign）**；
- 第二，**Alpha 的数值大小（magnitude）**。

某只股票取值为正，意味着你要**做多（买入）**它；取值为负，意味着你要**做空**它。

不同股票取值的大小，决定了我们在组合中**分配资金的比例**。

### 5. 开发 Alpha 的流程

开发一个 Alpha：

- **第一步，要有想法（idea）**——它可以极其基础，也可以非常复杂；
- **第二步，把这个想法实现出来。**

实现方式有两种：一种是用**（快速）表达式（expression）**，非常简单直接；另一种是写 **Python 代码**。

表达式或 Python 代码会在**历史数据**上运行，输出 Alpha 向量——也就是每个交易日、每只股票各有一个取值。这两种方式我们会在后续视频里详细展开。

下一步，你要在这个**原始 Alpha 向量**上施加各种**算子（operations）**，使它达到**多空中性（long-short neutral）**，并提升它的**预测能力**。

最后，平台会给出各种**统计指标**，用来刻画这个想法的强度，以及它产生的盈亏。你可以分析这些指标，据此修改实现方式、提升信号的预测能力。如此反复迭代，直到你确信这个 Alpha 已经可以**提交测试**，并用于真实市场。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1. Alpha 是什么**

> To WorldQuant, an Alpha is a mathematical predictive model of a performance of financial instruments.
> When we develop an Alpha, we assume we have a fictitious portfolio.
> The aim is to predict how we distribute the money among a group of financial instruments.
> While doing this, we try to ensure we have a downside protection while maintaining some good returns.
> To do that, we develop equity long-short market-neutral Alphas.
> Such investments are attractive because they are expected to produce substantially better risk adjusted returns than long only portfolios. Let's understand what that means.

**2. 做多与做空**

> You may know taking a long position in a stock simply means buying it. And if the stock increases in value, you will make money.
> On the other hand, taking a short position in a stock means borrowing an equity that you do not own, usually from your broker, selling it and then hoping it declines in the value.
> And this is the time you can buy it back at a lower price than you have paid for it and return the borrowed shares.

**3. 股票多空市场中性策略**

> Equity long-short market-neutral investing is a strategy used primarily by the hedge funds.
> This involves equal dollar amounts of long positions in stock, which are expected to increase in value and short positions in the stock that are expected to decrease in value.
> If this happens and the positions are of equal size, the hedge fund will benefit.
> Having said that, the strategy will work even if the long position declines in value. You wonder why? Because the profit from the shorting will be higher than the losses from the long positions, and in that scenario, the hedge fund will still benefit.
> So the goal of an equity long-short strategy is to minimize the exposure to the market in general and profit from the changes in the difference or the spread between two stocks.

**4. 股票池与 Alpha 向量**

> While developing an Alpha, you must begin by defining what instruments you want to trade. We call it a universe. The universe can be a group of US stocks defined on the basis of their liquidity.
> An Alpha is a vector of the predicted value of the stocks in the universe.
> Each value can change each day and has two properties. First, the sign of the Alpha and second, the magnitude of the Alpha.
> A positive sign or value for a stock means you want to long or buy that stock. A negative value for the stock means you want to short that stock.
> The magnitudes of the values for different stocks determine what proportion we are going to use to distribute money in our portfolio.

**5. 开发 Alpha 的流程**

> To develop an Alpha first, you need to have an idea. Which can be very basic or very complex.
> Second, you need to implement that idea. Implementation of the idea can be done in two ways. First, very simply, through an expression. Second, through the python code.
> The expression or python code will run on the past data to output the Alpha vector. So this will have a value for each day and has one value for each stock.
> Now we will talk in more detail about these two ways in the further videos.
> But as the next step, you will apply operations on this raw Alpha vector to make it long-short neutral and to improve your predictability.
> Finally, you will be provided with different statistics that will explain the strength and the profit or loss generated by the ideas.
> You can analyze these statistics to make changes to the implementation, improve the predictability of your signal. And you can keep repeating this process until you are satisfied that your Alpha is ready to be submitted for testing and used in the real markets.

---


---

# 视频 2｜Making an Alpha: Simulation Settings（制作 Alpha：模拟设置）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/making-alpha-simulation-settings> ｜ 时长：4 分 03 秒 ｜ 视频源：YouTube（uid `-HM9LogpgY4`）
> 源文件：`视频02_制作Alpha_模拟设置_中英对照.md`

## 一、中文译文

### 1. 为什么模拟设置重要

为每一个你创建的 Alpha 确定好**模拟环境（simulation environment）**非常重要。这些模拟设置就像一份**清单（checklist）**，照着走才能确保你没有做错。在平台上自定义这些设置非常容易。

下面我会逐项说明每个设置做什么、以及你该怎么定。

### 2. 区域与股票池（Region / Universe）

你要决定的**头一件事**是：交易哪个**区域（region）**、哪个**股票池（universe）**。假设你决定交易美股（US equities），下一步就是选择要交易**流动性最好的多少只股票**。

比如，你可以选 **USA TOP3000**，也可以选 **USA TOP500**。在 TOP500、TOP200 这类**高流动性股票池**里做 Alpha 相对更难——因为这些股票可交易的量更大，**信息被吸收的速度快得多**。

但反过来说，这类 Alpha 也**更值钱**，因为挂在上面的**交易成本更低**。

### 3. 延迟（Delay）

下一个要定的设置是：你的 Alpha 用**哪个时点**的数据，在模拟设置里叫 **Delay（延迟）**。

**Delay-1** 使用**昨天的价格**；**Delay-0** 使用**当天截至某个选定时刻的价格**。

### 4. 衰减（Decay）

接着要定的是：要不要给你的 Alpha 加 **Decay（衰减）**。

Decay 会把**过去指定天数**的 Alpha 值做一个**加权求和（weighted sum）**，作用是抹掉某一天 Alpha 值里的**剧烈波动或离群值（outliers）**。如果你想用上**前一天的 Alpha 值**，Decay 就有用。

只要你觉得对你的 Alpha 想法而言这在逻辑上说得通，或者你需要**降低 Alpha 的换手率（turnover）**，就应该用它。

### 5. 中性化（Neutralization）

下一个非常重要的设置是**中性化（neutralization）**。当你在开发一个**多空中性（long-short neutral）** Alpha 时，你需要在设置里选定：要**对哪个分组**做中性化。这个分组可以是**整个市场**，也可以是一个**交易所（market exchange）**或一个**行业（industry）**。

这一步也可以在**表达式框**里用 **`IndNeut`** 算子完成——好处是你可以**自定义分组**。

### 6. 截断（Truncation）

下一个设置是 **Truncation（截断）**。Truncation 的作用是确保你**不会把巨额资金压在极少几只股票上**；它也让 Alpha 更**分散（diversified）**，能扛住金融市场的各种情形。

我们建议把这个值设在 **0.1 或以下**，含义是：把**任何单只股票上的敞口（exposure）控制在 10% 以内**。

### 7. 模拟时长（Simulation Duration）

下一个是**模拟时长**。这个设置代表你选择用多长的时间跨度来**回测（backtest）**你的 Alpha 想法。

我们建议模拟窗口**至少五年**。

### 8. 回溯天数（Lookback Days）

最后一个要关注的是**回溯天数（lookback days）**。你的 Alpha 想法通常需要**用过去的信息**来生成**当天的持仓**。

回溯天数必须设为**大于或等于**你的 Alpha 实际往回看的天数。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1. 为什么模拟设置重要**

> It is very important to decide the simulation environment for each Alpha you create.
> These simulation settings are like a checklist you need to follow to ensure you are doing the right thing.
> The settings are very easy to customize on the platform.
> I will explain what each setting does and how you should decide upon the correct setting.

**2. 区域与股票池**

> The first thing you need to decide is the region and the universe you want to trade.
> Say you decide to trade the US equities, the next step would be to choose how many of the most liquid stocks to trade.
> For example, you might choose to trade the USA top 3000 or the USA top 500.
> It is relatively difficult to make an Alpha for a highly liquid universe like top 500 or top 200.
> That's because the information gets absorbed much faster due to higher tradable volumes available for these stocks.
> But such Alphas are also more valuable because they have lower trading costs attached to them.

**3. 延迟**

> Next simulation setting that you need to decide is the timing of the data you want to use for your Alpha.
> We refer to it as Delay in the simulation settings.
> Delay-1 uses yesterday's prices.
> While Delay-0 uses today's prices up to a chosen time during the day.

**4. 衰减**

> The next simulation setting you need to set is to decide if you want to use some Decay for your Alpha.
> Decay provides a weighted sum of the Alpha values for a specified number of days in the past.
> it helps remove any major fluctuations or outliers in the Alpha values on any given day.
> Decay helps if you want to use the previous day's Alphas value.
> You should use it if you think it would be logical for your Alpha idea or if you need to reduce your Alpha's turnover.

**5. 中性化**

> The next very important setting is using the neutralization.
> When you're developing a long-short neutral Alpha, you need to choose the group in the simulation setting you want to neutralize your Alpha over.
> It could be a market exchange or an industry.
> This can also be done in the expression box by using the IndNeut operator, which gives you the flexibility to define your own group.

**6. 截断**

> The next simulation setting is the Truncation.
> Truncation helps ensure you don't have a huge amount of capital assigned to very few stocks in your Alpha.
> It also helps make sure that the Alpha is diversified and can survive different scenarios in the financial markets.
> We recommend setting this value at or below 0.1, which means you are trying to control the exposure on any given stock up to a level of 10%.

**7. 模拟时长**

> The next simulation setting is this simulation duration.
> This setting signifies the duration you choose to backtest your Alpha idea.
> We recommend using a window of at least five years for your simulation.

**8. 回溯天数**

> The next simulation setting you need to look into is the lookback days.
> Your Alpha idea usually needs to use information from the past to generate the current days positions.
> The number of lookback days must be set greater than or equal to the days your Alpha looks back in the past.

---


---

# 视频 3｜Making an Alpha: Simulating an Alpha（制作 Alpha：模拟一个 Alpha）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/making-alpha-simulating-alpha> ｜ 时长：3 分 29 秒 ｜ 视频源：YouTube（uid `AMzPHBintkM`）
> 源文件：`视频03_制作Alpha_模拟过程_中英对照.md`

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


---

# 视频 4｜Alpha expression to PnL Chart（从 Alpha 表达式到 PnL 曲线）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/alpha-expression-to-pnl> ｜ 时长：11 分 22 秒 ｜ 视频源：YouTube（uid `bXOirnDpZsM`）
> 源文件：`视频04_从表达式到PnL曲线_中英对照.md`

## 一、中文译文

### 1. 为什么值得了解后台原理

本视频假定你已经看过 "Getting Started with Brain" 课程的第 1、2、3 个视频。如果还没看，建议先回去补上。

前面的视频里我们展示了：在模拟窗口里输入一条 Alpha 表达式、按下 **Simulate（模拟）** 按钮之后，就会生成一条与该表达式对应的**盈亏（PnL）曲线**。

**Brain 平台是自动完成这一切的**，但我们想让你**大致看一眼后台发生了什么**——究竟做了哪些计算，才能把 Alpha 表达式转换并绘制出**累计 PnL 曲线**。虽然你**永远不需要自己动手算这些**，但**建立直觉**对做 Alpha 是有帮助的。

我们用一个 Alpha 示例来说明：**负收益率的排序（rank of negative returns）**。

### 2. 示例背后的假设

这条表达式背后的假设是：我们想在明天**买入（做多）**那些**今天收益率为负、或相对更低**的股票；想在明天**卖出（做空）**那些**今天收益率为正、或相对更高**的股票。

这是**均值回归（reversion）**想法的一个最基础的例子。

这里我们用了 **`rank`** 算子：它把括号内的输入值排序，返回在 **0 到 1 之间均匀分布**的值。

### 3. 后台的七个步骤（总览）

当你点击 Simulate 并填入模拟设置后，**Brain 模拟器会为每个金融标的建立多头或空头头寸**，并生成你看到的 PnL 曲线。

在幕后，**要执行七个步骤（操作）**，才会产出最终的 PnL 曲线。

在真实的 Alpha 模拟中，股票池里通常会有 **200 到 3000 只**股票标的。但为了更好地理解这个概念，我们假设一个假想场景：**模拟池里只有 8 只股票**。

我们先用 **市场中性化（market neutralization）、Delay-1、Decay-0** 的设置来模拟 "负收益率的排序" 这条表达式。

**表格的列定义：**

- **B 列**：Alpha 向量里的 8 只股票；
- **C 列**：这些股票在（比方说）**2 月 1 日**的收益率——它们作为 "负收益率的排序" 这条表达式的**输入数据**。

### 4. 第 1 步：对每只股票求值，生成 Alpha 向量

第一步是**对每只股票分别求值**，生成**该日期的 Alpha 向量**。

由于我们设的是 **Delay-1**，这个日期会是 **2 月 2 日**。Delay-1 的含义是：**用 T-1 日的数据来生成 T 日的 Alpha 向量**。

为了产出 Alpha 向量，模拟器对"负收益率"执行 `rank` 运算，得到一个与每只股票对应的数值向量。**最终的向量长什么样，取决于表达式里用了哪些算子。**

因为用了 `rank` 算子，我们在 **D 列**看到的是 **0 到 1 之间均匀分布**的值。注意：**收益率最低的那只股票拿到了最高值**，反之亦然——这与我们的假设一致。

### 5. 第 2 步：中性化（减去分组均值）

第二步是：用**向量中的每一个值**减去**该分组内所有值的均值**，使向量中所有值的**和为零**。

这一步就叫**中性化（neutralization）**。

分组可以是**整个市场**，也可以是对股票的**板块（sector）、行业（industry）或子行业（sub-industry）**分组做这个中性化操作。在我们这个例子里，因为模拟池只有 8 只股票，所以假定对**整个市场**做中性化。

于是我们取 **D12 单元格**中这些数字的均值，再从每只股票里减去这个均值，得到 **F 列**的新向量。注意：这些数字的**和与均值都等于零**；而且**正数之和等于负数之和**。

### 6. 第 3 步：缩放 / 归一化

第三步，把得到的值做**缩放（scaled）或归一化（normalized）**，使 Alpha 向量中所有值的**绝对值之和为 1**。

这里我们把每一行的绝对值加起来，得到总和 **2.3**；然后用每一行除以这个总和，就得到**归一化后的值**。

所谓"归一化"，是指 **H 列**的**绝对值总和为 1**。这个向量也可以称为**归一化的权重向量（normalized vector of weights）**。

### 7. 第 4 步：分配资金，构建组合

第四步，用这些归一化权重，Brain 模拟器从一个**2000 万美元的虚拟账本（fictitious book of $20 million）**中给每只股票分配资金，构建出一个**投资组合**。

**G 列**总计 2000 万美元的虚拟资金，是依据 **H 列**的归一化权重分配到各只股票上的。

这意味着：我们在**股票一**上有 **-440 万美元**的头寸（即做空了价值 440 万美元的股票一），在**股票五**上有 **+60 万美元**的多头头寸（即买入了 60 万美元的股票五）。

这就是**多空市场中性化**的结果，也是在 Brain 上创建这类预测模型（Alpha）的**主干思路**。用这个技术，一个策略**无论市场涨跌都可能获利**。

### 8. 第 5 步：计算当日 PnL

第五步，我们基于**次日实际观察到的股票收益率**，计算该 Alpha 产生的**每日 PnL**。

在给股票分配好美元头寸之后，我们根据每只股票当天的收益率，计算每只股票产生的 PnL。

假设这些股票在 **2 月 2 日**的实际收益率如 **K 列**所示。我们看到：虽然我们预期股票一和股票二会跌，它们实际上涨了，于是如 **L 列**所示，我们亏了。

我们还预期股票六会上涨，但它走平了。所以总体上，**我们判断错了 3 只，判断对了 5 只**。

这一天我们总共赚了 **3 万美元**（0.03 百万美元），这是把向量中所有股票的 PnL 相加得到的。**模拟器就是这样计算 Alpha 在任意给定日期的 PnL 的。**

### 9. 第 6 步：在整个样本内区间逐日重复

第六步，我们对**若干年历史跨度内的每一个日期**，重复第 1 步到第 5 步——这个跨度也叫**样本内区间（in-sample period，简称 IS 期）**——从而算出 Alpha 在 IS 期内**每一天的 PnL**。

### 10. 第 7 步：得到累计 PnL 曲线

第七步，模拟器据此计算 Alpha 从 IS 期**起点到终点**的**累计 PnL**，得到**累计 PnL 曲线**。

这一点用我们前面模拟的那个 Alpha 的 PnL 图更容易理解。在这张图里，时间是**从 2016 年 2 月到 2021 年 1 月，共五年**。用我们示例中讨论的步骤，模拟器会算出 Alpha 的每日 PnL，并导出你在这里看到的累计 PnL 曲线。

注意：**从 2021 年 2 月到 2023 年 1 月这两年，在模拟窗口里是看不到的**——这段叫**样本外区间（out-of-sample period，简称 OS 期）**。

在你**提交**一个 Alpha 之后，平台会跑若干测试来分析该 Alpha 在 **OS 期的表现**。**一个同时通过样本内测试和样本外测试的 Alpha，才能称为稳健的 Alpha。**

以上就是 Brain 模拟器如何从一条 Alpha 表达式生成 PnL 曲线。

### 11. 换个中性化设置会怎样

在我们这个例子里，假定用的是**市场中性化 + Decay-0**。但如果你用了其他中性化设置，模拟器会对 Alpha 施加**类似的操作**。

举例：如果模拟池里有 **80 只股票，分成 10 个组（或行业），每组 8 只**，那么模拟器会**对 10 个组分别执行这些操作**，最后**把每组的 PnL 相加**，得到该 Alpha 的每日 PnL，并绘制累计 PnL 曲线。

### 12. 引入 Decay 会怎样

但是，如果我们在设置里引入 **Decay（衰减）**，就必须**多执行一步**才能得到最终的 Alpha 向量。

假设我们在模拟设置里用 **Decay = 3**。那么 Alpha 的**最终权重向量**，是由**当天的值**与**前一天的衰减值**结合计算出来的。

在我们这个例子里，我们算出了 Alpha 在 **2 月 2 日**的归一化权重。假设该 Alpha 向量中各股票在 **2 月 1 日**和 **1 月 31 日**的归一化权重分别如 **N 列**和 **O 列**所示，那么 Alpha 的**最终权重**就用 **P 列**给出的那个**加权平均公式**来计算。

用这个新导出的向量，模拟器会计算每日 PnL，进而得到累计 PnL 曲线。注意：**即使使用了 Decay，越近期的值仍然被赋予越大的权重。**

**Decay 是降低交易成本（或换手率）的一个非常重要的因素**，因为它也纳入了前几天的信息，**防止 Alpha 反应过度（overly reactive）**。

### 13. 小结

总结一下：一旦我们在 Brain 模拟器里输入 Alpha 表达式和模拟设置，它就会执行本视频讨论的这些操作，**为每个金融标的建立多头或空头头寸，并生成 PnL 曲线**。

现在，建议你去看第 4 个和第 5 个视频，进一步了解**如何解读 PnL 曲线及随附的各项统计指标**。

> 译注：本视频自述"建议接着看视频 4 和 5"，指的是该系列内的后续视频，即本归档的 **《Simulation Results》**（模拟结果）与 **《OSTests in an Alpha》**（Alpha 的样本外测试）。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1. 为什么值得了解后台原理**

> This video assumes that you have already watched the "Getting Started with Brain" course videos 1, 2, and 3.
> If you haven't done this yet, I suggest you go back and watch those videos first.
> In the preceding videos, we showed that after you type an alpha expression into the simulate window and press the "Simulate" button, a profit and loss (PnL) chart is generated that corresponds to that alpha expression.
> The Brain platform does this automatically, but we want to give you a brief glimpse of what happens in the background—what calculations are happening that translate the alpha expression and create the cumulative PnL chart.
> Even though you will never need to do these calculations yourself, developing an intuition for them will help you in the alpha-making process.
> Let's illustrate this using the alpha example rank of negative returns.

**2. 示例背后的假设**

> The hypothesis in this expression is that we want to buy (go long) on those stocks tomorrow that had negative or comparatively lower returns today, and we want to sell (go short) those stocks tomorrow that had positive or comparatively higher returns today.
> This is a very basic example of a reversion idea.
> We have used the rank operator here, which ranks the input values inside the operator and returns values equally distributed between zero and one.

**3. 后台的七个步骤（总览）**

> When you click "Simulate" and input the simulation settings, the Brain simulator takes a long or short position for each financial instrument and generates the PnL chart you see.
> Behind the scenes, seven steps or operations are performed before the final PnL chart is generated.
> Normally, in an alpha simulation, there would be between 200 and 3,000 stock instruments in the universe.
> But to better understand this concept, we will assume a hypothetical scenario in which the simulation universe has only eight stocks.
> We simulate the expression "rank of negative returns" with market neutralization, delay-1, and decay-0 settings for now.
> - Column B: The eight stocks in the alpha vector.
> - Column C: The returns of the stocks as of, let's say, February 1.
> These serve as the input data for the alpha expression "rank of negative returns."

**4. 第 1 步：对每只股票求值，生成 Alpha 向量**

> Step 1: The first step in the process is to evaluate the alpha expression for each stock to generate the alpha vector for the given date.
> Since we have assumed delay-1 settings, this date would be February 2.
> The delay-1 setting uses data as of T-1 date to create the alpha vector as of T date.
> To produce the alpha vector, the simulator performs the rank operation on negative returns and produces a vector of values corresponding to each stock.
> The resulting vector depends on the operators used in the alpha expression.
> Since we have used the rank operator, we see equally distributed values between zero and one in column D.
> Note that the stock with the lowest return has the highest value and vice versa, in line with our hypothesis.

**5. 第 2 步：中性化（减去分组均值）**

> Step 2: The second step is to subtract the average of the vector values in the group from each value in the vector so that the sum of all values in the vector is zero.
> This is called neutralization.
> The group can be the entire market, or you can perform this neutralization operation on sector, industry, or sub-industry groupings of stocks.
> In our example, since we have only eight stocks in the simulation universe, we have assumed neutralization over the market.
> So, we take the average of the numbers in cell D12 and subtract the average from each stock.
> This gives us a new vector in column F.
> Note that both the sum and average of these numbers are equal to zero.
> Also, the sum of positive values is equal to the sum of negative values.

**6. 第 3 步：缩放 / 归一化**

> Step 3: In step three, the resulting values are then scaled or normalized so that the absolute sum of the values in the alpha vector is one.
> Here, we sum the absolute values of each row and find the sum, which is 2.3.
> Then, we divide each row by this sum, which results in normalized values.
> By "normalized," we mean that the total absolute sum of column H is one.
> We can also call this vector a normalized vector of weights.

**7. 第 4 步：分配资金，构建组合**

> Step 4: In the next step, using these normalized weights, the Brain simulator allocates capital to each stock from a fictitious book of $20 million and constructs a portfolio.
> Column G has a total of $20 million of fictional money allocated to the stocks using the normalized weights in column H.
> This means we have a position of minus $4.4 million in stock one (i.e., we have shorted $4.4 million worth of stock one) and a long position of $0.6 million in stock five (i.e., we have invested $0.6 million in stock five).
> This is a result of long-short market neutralization and is the backbone of creating these predictive models, or alphas, on Brain.
> With this technique, a strategy can have the potential to be profitable regardless of the direction of the market.

**8. 第 5 步：计算当日 PnL**

> Step 5: We calculate the daily PnL generated by the alpha based on the observed stock returns of the next day.
> After allocating dollar positions on the stocks, we calculate the PnL generated by each stock based on the returns each stock had that day.
> Suppose the actual returns on these stocks as of February 2 are shown in column K.
> We see that although we expected stock one and stock two to fall in price, they actually went up, so we had a loss as shown in column L.
> We also expected stock six to go up in price, but it stayed flat, so we were wrong in general about three stocks, but we were right about five.
> In total, we made a gain of $0.03 million on this day with our alpha, which is calculated by adding the PnLs of all the stocks in our vector.
> This is how the simulator calculates the PnL generated by the alpha for any given date.

**9. 第 6 步：在整个样本内区间逐日重复**

> Step 6: We repeat the same process from step one to step five for each date in a several-year history span, also called the in-sample period or the IS period, to calculate the daily PnL generated by the alpha for each day in the IS period.

**10. 第 7 步：得到累计 PnL 曲线**

> Step 7: From this, the simulator calculates the alpha's accumulated PnL from the start to the end of the IS period to get the alpha's accumulated PnL chart.
> This can be better understood with the help of the PnL chart of the alpha we simulated earlier.
> In this chart, we have a period of five years from February 2016 to January 2021.
> Using the steps we discussed in our example, the simulator would calculate the daily PnL of the alpha and derive the cumulative PnL chart as we see here.
> Note that the two years from February 2021 to January 2023 are not visible to us in the simulation window; that's called the out-of-sample or OS period.
> After you submit an alpha, several tests are run to analyze the alpha's performance in the OS period.
> An alpha that passes both the in-sample as well as the out-of-sample test can be said to be a robust alpha.
> This is how the Brain simulator creates the PnL chart from an alpha expression.

**11. 换个中性化设置会怎样**

> In our example, we have assumed that we are using market neutralization and decay-zero settings.
> But if you use any other neutralization settings, similar operations would be performed on the alpha.
> For example, if we have 80 stocks in the simulation universe consisting of 10 groups or industries with eight stocks each, the simulator would perform these operations on each of the 10 groups and finally add the PnL from each group to get the daily PnL of the alpha and create the cumulative PnL chart.

**12. 引入 Decay 会怎样**

> However, if we introduce decay into our alpha settings, an additional step must be performed to get the final alpha vector.
> Suppose we use a decay of three in our simulation settings.
> The final vector of weights in the alpha would be calculated by combining today's values with the previous day's decayed value.
> In our example, we calculated the normalized weight in our alpha as of February 2.
> Let's assume that the normalized weights of stocks in the alpha vector as of February 1 and January 31 are as shown in columns N and O, respectively.
> Then, the final weights in the alpha would be calculated using the given weighted average formula in column P.
> Using this new derived vector, the simulator would calculate the daily PnL and, consequently, the cumulative PnL chart.
> Note that even if decay is used, more weight is assigned to the most recent values.
> Decay is a very important factor in reducing transaction costs or turnover, as it includes information from previous days as well, preventing the alpha from being overly reactive.

**13. 小结**

> To summarize: Once we input the alpha expression and the simulation settings in the Brain simulator, it performs the operations we discussed in this video to take long or short positions for each financial instrument and generate the PnL chart.
> Now, I suggest that you move to videos four and five to learn more about how to interpret the PnL chart and the accompanying statistics.

---


---

# 视频 5｜Simulation Results（模拟结果）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/simulation-results> ｜ 时长：7 分 12 秒 ｜ 视频源：YouTube（uid `r6lSEkA0Sho`）
> 源文件：`视频05_模拟结果_中英对照.md`

## 一、中文译文

### 1. 模拟结果分两种形式

模拟完成后，平台会把结果呈现给你。结果分两种形式：

1. **汇总表现参数（aggregate performance parameters）**；
2. **汇总表现参数的明细分析（detailed analysis）**。

### 2. 汇总表现参数包含哪些

先说**汇总表现参数**。它包括：

- **收益率（returns）**
- **PnL（盈亏）**
- **信息比率（information ratio）或夏普比率（Sharpe ratio）**
- **换手率（turnover）**
- **回撤（drawdown）**

你要分析这些指标，判断结果是否令人满意，还是需要继续改进（improve）你的信号。

下面逐个详细说明。

### 3. 收益率（Return）

**第一个是收益率。** 模拟结果中**每一年的收益率**，代表的是**那一年日收益率的平均值**。

**日收益率的算法**是：今天的收盘价减去昨天的收盘价，再整体除以昨天的收盘价。

### 4. PnL（盈亏）

**第二个是 PnL。** PnL 就是你的想法产生的**盈亏**。

**算法**是：对你想交易的股票池里的每一只股票，把**持仓（position）**与**当日收益率**相乘，再求和。

所以 **PnL 越高——也就是利润越好——对你的 Alpha 想法越有利。**

### 5. 信息比率 / 夏普比率（IR / Sharpe）

**第三个是信息比率。** 信息比率，也就是夏普比率，提供的是**风险调整后收益（risk adjusted returns）**。

**这是你开发 Alpha 时最需要关注的一个比率**，它可以被看作**模型预测能力（prediction ability）的代理指标**。

**信息比率（或夏普比率）越高，你的 Alpha 就越好。**

如果**在多年回测中信息比率/夏普比率表现得更稳定**，说明你的信号在样本内**不同年份都工作良好、表现一致**，这会让你**更有信心把钱投到这个信号上**。

所以正如我所说，**Alpha 的预测能力就由这个比率来刻画**。

**算法**是：**日 PnL 的均值**除以**日 PnL 的波动率**（即日 PnL 的**标准差**）。

而**夏普比率就是年化后的 IR**，算法是：**IR × √252**。

那么 **252 是什么？** 252 代表**一年的估计交易日数**。

### 6. 换手率（Turnover）

**下一个重要参数是换手率。** 换手率代表**交易一个信号的成本**，等于**成交价值（value traded）与持仓价值（value held）之比**。

它的道理是：当我们按 Alpha 的指引在市场上执行多空交易时，**这些操作本身是有成本的**，而这个成本就由换手率来刻画。

**换手率越低越好。** 实践中，你开发 Alpha 时**应该把换手率的目标定在 40% 以下**。

我再重复一遍，因为这一点非常重要：**你的 Alpha 换手率应当低，尽量保持在 40% 以下。**

另外还有 **Delay-0 和 Delay-1** 两类 Alpha，通常你会看到 **Delay-0 的 Alpha 换手率更高**，但**无论 Delay-0 还是 Delay-1，你的关注点都应该是把换手率保持在 40% 以下。**

### 7. 回撤（Drawdown）

**下一个参数是回撤。** 回撤代表**回测中任何一年里发生的最大亏损的百分比**。

实践中，**你应该把"收益率/回撤"这个比值的目标定在大于 1**。**收益与回撤的比值越高，对你的 Alpha 越好。**

我再重复一遍：我说的是**收益率与回撤的比值**，但**回撤本身要低**。

**回撤越低越好，但"收益/回撤"的比值应该更高。**

到这里，模拟结果里你能看到的所有汇总表现参数就讲完了。

### 8. 明细分析：把汇总参数拆开看

学完汇总表现参数之后，现在我们来说**明细分析**。

平台会给你**深入的分析**，展示这些汇总表现参数**可以如何拆解**。这包括图形化结果，用来呈现：

- **资金分布（capital distribution）**
- **覆盖率（coverage）**
- **夏普比率（Sharpe ratio）**
- **不同行业、不同板块、不同市值分组的股票所产生的 PnL**

**表现来源在行业、板块、市值上的分散度越高，你的 Alpha 就越稳健（robust）。**

**为什么？** 因为你的 Alpha 的表现**不是来自单只股票，而是来自一大群不同类型的股票。**

### 9. 分散度为什么在量化 Alpha 里尤其重要

在**量化 Alpha** 里，这个参数**非常非常重要**。**为什么？**

**因为我们不交易少数几只股票——在量化 Alpha 里，我们交易的是一大篮子股票。**

所以正如我所说：资金**分布在不同行业**、PnL**来自不同市值的股票**，这是好事，因为它说明**这个想法在不同类型的股票上都能工作**；而**按板块看的夏普**则说明**信号在不同板块上都具备可预测性**。

所以在量化 Alpha 里，**不仅要有好的汇总参数，还要确保表现来自一个分散的股票集合**。

**这可以防止**在某个板块、行业或任何其他标准分组上出现**集中度风险（concentration risk）**。

现在你已经了解了汇总表现参数以及分析其明细的方法，我希望这能帮助你创建出**在样本外表现更好**的 Alpha。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1–2. 结果分两种形式 / 汇总参数包含哪些**

> Once the simulation is complete, the platform will present you with the results.
> The results come in two forms.
> First, the aggregate performance parameters and second, the detailed analysis of the aggregate performance parameters.
> Let's first talk about the aggregate performance parameters.
> The aggregate performance parameters include returns, PnL, the information ratio or the Sharpe ratio, turnover, and drawdown.
> You will analyze these to determine if the results are satisfactory or if you need to work more to improvise your signal.
> Now let's talk about each of these performance parameters in detail.

**3. 收益率**

> The first one is the return.
> The return for every year in the simulation results represents the average of the daily return for that year.
> The daily return is calculated as the difference of today's close price and yesterday's close price, the whole divided by the yesterday's close price.

**4. PnL**

> The second performance parameter is the PnL.
> PnL is the profit and the loss generated by your idea.
> To calculate the PnL you sum the product of the position and the daily return for every stock in the universe that you decided to trade.
> So the higher the PnL, which means if the profits are good, the better it is for your Alpha idea.

**5. 信息比率 / 夏普比率**

> The next performance parameter is the information ratio.
> The information ratio or the Sharpe ratio, provides the risk adjusted returns.
> This is the most important ratio that you would take care of when you're developing your Alpha.
> It can be treated as a proxy for the prediction ability of your model.
> The higher the information ratio or the Sharpe ratio, the better your Alpha is.
> A more consistent information ratio or Sharpe ratio over years of backtesting indicates that your signal has worked well over different years in the In-Sample and has produced consistent performance.
> This gives you higher confidence to invest your money in that particular signal.
> So the prediction ability, as I mentioned, of the Alpha is captured by this ratio.
> And it is calculated as the mean of the daily PnL divided by the volatility of the daily PnL, which is calculated as the standard deviation of the daily PnL.
> While the Sharpe ratio is nothing but the annualized IR, and it is calculated as the IR multiplied with the square root of 252.
> Now what is 252? The 252 parameter represents the estimated number of trading days in a year.

**6. 换手率**

> So the next important parameter is the turnover.
> The turnover represents the cost of trading a signal.
> It is equal to the ratio of the value traded to the value held.
> And the idea behind this is when we try to execute long-short trades in the market, as suggested by your Alpha, there's a cost attached to doing that and this cost is captured by the turnover.
> The lower the turnover, the better it is.
> And as a practice when you develop an Alpha, you should target a turnover below 40%.
> I repeat this again because this is very important to understand that turnover should be low for your Alpha and try to keep it below 40%.
> There are also delay-0 and delay-1 Alphas and usually you would see that delay-0 alphas have higher turnovers, but your focus should still be to keep the turnovers below 40%, both for delay-0 and delay-1.

**7. 回撤**

> The next performance parameter is the drawdown.
> The drawdown represents the percentage of the largest loss incurred during any year in your backtesting.
> As a practice, you should target a return-to-drawdown ratio greater than one.
> The higher the ratio of returns to drawdown, the better it is for your Alpha.
> I repeat, I'm talking about the ratio of the returns to drawdown, but the drawdown should be low.
> The lower the drawdown, the better it is.
> But the returns to drawdown ratio should be higher.
> So now we have talked about all the aggregate performance parameters that you see in your results.

**8–9. 明细分析 / 分散度**

> So having learned about the aggregate performance parameters, now let's talk about the detailed analysis of the aggregate performance parameters.
> The platform will provide to you the in depth analysis of how this aggregate performance parameters can be broken down.
> So this will include the graphical results representing the capital distribution, the coverage, Sharpe ratio and the PnL generated by different industries, different sectors and different capitalization of stocks grouped together.
> So the more diversified the sources of performance across industries, sectors and capitalization, the more robust your Alpha is.
> Why? Because your Alpha is deriving performance, not from a single stock, but from a group of different kinds of stocks.
> And in a quantitative Alpha, this parameter is very, very important.
> Why? Because we do not trade a few stocks.
> We in a quantitative Alpha, we trade a big set of stocks.
> So as I mentioned, it's good if the capital is distributed across different industries, the PnL is generated by stocks of varying capitalization, as that would indicate that the idea works well across different kinds of stocks, and the Sharpe by sector shows the signal has predictability across various sectors.
> So in a quantitative Alpha, it's not only important to have good aggregate parameters, you also should ensure that the performance is derived from a diversified set of stocks.
> This prevents any concentration risk on a given sector, industry or any other standard group.
> Now that you have learned about the aggregate performance parameters and the way to analyze the details of these performance parameters, I hope this will help you create the Alphas, which would perform better in the Out-of-Sample.

---


---

# 视频 6｜OSTests in an Alpha（Alpha 的样本外测试）

> 课程页：<https://platform.worldquantbrain.com/learn/courses/introduction-alphas/ostests-alpha> ｜ 时长：8 分 31 秒 ｜ 视频源：YouTube（uid `b9VQEoCvBVU`）
> 源文件：`视频06_Alpha的样本外测试_中英对照.md`

## 一、中文译文

### 1. Alpha 进入生产前要经历什么

一个 Alpha 在**进入生产环境（production）、开始被用于交易**之前，必须经过**若干阶段**。

在你**开发和提交** Alpha 之后，WorldQuant 会对它施加**各类测试**。这些测试分成**两大类**。

**第一类：基础测试（base tests）**。共有 **8 项基础测试**，在 **`OSTEST-PENDING`** 阶段执行。如果状态显示 **`OSTEST-FAIL`**，说明你的 Alpha **至少没通过其中一项**。

**第二类：表现测试（performance tests）**。共有 **2 项表现测试**，在 **`OSTEST2-PENDING`** 阶段执行，**通常需要更长时间才能通过**。

下面我逐项详细解释这些测试，并给出一些**帮助你通过测试的指引**。

### 2. 测试一：权重检查（Check Weight Test）

**第一项是权重检查测试**，属于基础测试。它确保你**不会把巨额资金分配到极少几只股票上**。控制住这一点，就能让 Alpha **分散**，并**扛住金融市场的各种情形**。

这项测试**在你提交 Alpha 之前就会执行**。

**通过条件**：任意一只股票的**最大权重低于 10%**。

**可能失败的情形**：如果在一年中有**相当多的天数里只有太少股票被赋予权重**，Alpha 就会失败。

注意：**模拟开始时所有股票权重都为零，这不会导致失败**——这个条件**只在 Alpha 开始分配权重之后才适用**。**最少股票数的具体数值随股票池不同而不同**（即各股票池的最少持仓数不尽相同）。

另外，**权重过度集中在某一只股票上**也会失败。例如，如果**某一只股票占了全部 Alpha 权重的 30%，就会失败**。

那么怎样让 Alpha 通过这项测试？**只要你在模拟设置里把 Truncation（截断）设到 0.1 以下，Alpha 就能通过。**

### 3. 测试二：次小股票池测试（Subuniverse Test）

**下一项是次小股票池测试。** 所谓 **subuniverse 值，指的是在"下一个更小的标准股票池"中的夏普比率**。

这项测试确保你的 Alpha **表现不是来自所选股票池中极小的一部分标的**。

**通过条件**：Alpha 的 **subuniverse 夏普大于由屏幕上公式算出的夏普**。

**该公式对 Delay-1 和 Delay-0 的 Alpha 是不同的**（如屏幕上所示）。

**提高通过率的做法**：**提交前，永远先检查你的 Alpha 在"下一个更小的股票池"中的表现。** 并且在实践中建议——**在更小的股票池上开发你的 Alpha，然后在更大的股票池上提交**。这样也能帮你确保 Alpha 通过次小股票池测试。

### 4. 测试三：次大股票池测试（SuperUniverse Test）

**下一项是次大股票池测试。** 与次小股票池测试类似，**superuniverse 值指的是在"下一个更大的标准股票池"中的夏普比率**。

**通过条件**：该 Alpha 在**下一个更大股票池**上算出的夏普，**大于该 Alpha 自身夏普的 0.7 倍**。

**提高通过率的做法**：**提交前，先检查它"下一个更大的股票池"中的表现。**

### 5. 测试四：排序后夏普测试（Rank Sharpe Test）

**下一项重要测试是排序后夏普测试。**

**Rank Sharpe 的定义**是：对 Alpha 的**多头侧和空头侧分别**施加 **`rank` 算子**以及**指数为 3 的 `power` 算子**之后的夏普比率；随后，**再把两侧各自缩放回原来的规模**。

**通过条件（两条同时满足）**：

1. Rank Sharpe **为正**；
2. 并且，**Rank Sharpe 与原始 Sharpe 的比值 ≥ 0.5**，**或 Rank Sharpe > 0.15**。

### 6. 测试五：偏差测试（Bias Test）

**下一项是偏差测试（bias test）**，目标是**检测你的 Alpha 中是否存在前视偏差（forward bias）**。

如果 Alpha 通过了这项测试，说明**在回测时，你没有使用任何比模拟日期更靠近当前时点的数据**。

**表达式 Alpha（expression Alpha）不会在这项测试上失败**；但**对于 Python Alpha，请务必在需要的地方写上延迟参数**（字幕原文为 `di-delay`，词义不明，见文末勘误）。

### 7. 测试六：相关性测试（Correlation Test）

**下一项是相关性测试。这是一项唯一性测试（uniqueness test）。**

**Alpha 通过"与外部 WebSim Alpha 的相关性测试"的条件是满足以下任一：**

1. **PnL 相关性**：该 Alpha 与任何外部 WebSim Alpha 的 PnL 相关性 **小于 0.7**；
2. **同组相关性**：该 Alpha 与**同一分组**内外部 WebSim Alpha 的 **PnL、持仓（position）或交易（trade）相关性小于 0.4**；
3. **夏普优势**：该 Alpha 的夏普比**同组中那些 PnL/持仓/交易相关性高于 0.7 阈值的任何 Alpha** **高出 10%**。

### 8. 测试七：全局相关性检查（CheckCorrAll Test）

**CheckCorrAll 测试至少需要三个周末才能跑完**，在此期间，**OSTEST 状态页会把测试结果标注为 pending（进行中）**。

要让 Alpha 通过这项测试，**去尝试新的想法、尝试不同的算子、尝试不同类别的数据集，并尝试你想法中的替代实现方式**。

### 9. 测试八：样本内夏普测试（IS Sharpe Test）

**下一项是 IS Sharpe 测试。**

**IS Sharpe 测试的目标，是把真正的 Alpha 中的随机噪声剔除出去。**

要让 Alpha 通过这项测试，**尽量让表现跨年份保持一致，并最大化你的夏普比率。**

### 10. 两项表现测试之一：样本外夏普测试（OS Sharpe Test）

下面讲我们有的**两项表现测试**。

**第一项是 OS Sharpe 测试。** 和 IS Sharpe 测试一样，**OS Sharpe 测试的目标也是把随机噪声从真正的 Alpha 中分离出来**。

**Alpha 必须满足不同时间区间对夏普设定的要求**，才能通过这项测试。

**提高通过率的做法**：为更好的 OS Sharpe **纳入有逻辑的参数**，**尽量不要对 Alpha 做大量过拟合**，这样你的 Alpha 通过这项测试的概率会**非常高**。

### 11. 两项表现测试之二：新高测试（New High Test）

**最后一项是新高测试。** 顾名思义，**当提交的 Alpha 在平台上你能看到的累计 PnL 曲线上创出新高时**，这项测试即告通过。

**一个好的 Alpha 通常能轻松通过这项测试。**

### 12. 结语

在理解了这些测试以及让 Alpha 通过它们的各种方法之后，**请在你提交 Alpha 之前尽量遵循这些做法**。

这样能确保**你提交的 Alpha 中有很大一部分能通过测试并进入生产**。

---

## 二、英文原文（官方 transcript，逐段）

> 官方原字幕按 40 字符硬换行，此处已按句子重新断行，文字未改。

**1. Alpha 进入生产前要经历什么**

> An Alpha must go through different stages before it enters production and starts getting used for trading.
> After you develop and submit your Alpha WorldQuant applies various tests to it.
> These tests fall into two categories.
> First, the base tests.
> There are eight base tests, which are carried out in the OSTEST-PENDING phase The OSTEST-FAIL status means your Alpha failed at least one of these tests.
> The second kinds of tests are the performance tests.
> There are two performance tests which are conducted in the OSTEST2-PENDING phase.
> It usually takes longer to pass these tests.
> I will now explain each of these tests in detail and provides some guidelines to help you pass these tests for your Alphas.

**2. 权重检查测试**

> The first test is the check weight test.
> It is a base test, and it ensures that you don't have a huge amount of capital assigned to a very few stocks.
> Controlling this makes sure your Alpha is diversified and can survive different scenarios in the financial markets.
> This test is applied before you submit your Alpha.
> An Alpha passes this test if the maximum weight in any stock is less than 10%.
> An Alpha can fail this test if too few stocks are assigned weight for a significant number of days in a year.
> Note that assigning zero weights to all stocks at the start of the simulation does not fail this condition.
> It only applies after the Alpha starts assigning the weights.
> The exact number of the minimum stocks varies with the simulation universe.
> An Alpha can fail the test if the weight is too concentrated on one stock.
> For example, if a stock has 30% of all the Alpha weight, it will fail.
> Now, let me tell you how to make your Alpha pass this test.
> If you have set the Truncation to less than 0.1 in the simulation settings, your Alpha will pass this test.

**3. 次小股票池测试**

> The next test is the subuniverse test.
> The subuniverse value is the Sharpe in the next smallest standard universe.
> This test makes sure that the performance of your Alpha isn't derived from a very small set of instruments in the chosen universe.
> An Alpha will pass the subuniverse test if it's subuniverse Sharpe is greater than the Sharpe calculated by the formula, as you can see on your screen right now.
> The formula is different for Delay-1 and Delay-0 Alphas as you can see on the screen.
> To improve the chance that your Alpha will pass this test, always check the performance of your Alpha in the next smallest universe before submitting it.
> Develop your Alphas on the next smallest universe and submit on the higher universe.
> This can also help you make sure that your Alpha is passing the subuniverse test.

**4. 次大股票池测试**

> The next test is the SuperUniverse test.
> Similar to the subuniverse test, the superuniverse value is the Sharpe of the next largest standard universe.
> And Alpha will pass the SuperUniverse test when the Sharpe calculated on the next larger universe for this particular Alpha is greater than 0.7 times the Sharpe of the Alpha itself.
> To make sure your Alpha passes this test, check its performance in the next largest universe before you submit it.

**5. 排序后夏普测试**

> The next important test is the rank Sharpe test.
> The rank Sharpe is defined as the Sharpe of the Alpha after applying the operator rank and the power with the exponential three separately, to the long and the short sides of the Alpha.
> Later, the rescaling of each side is done to the original size.
> An Alpha passes the rank Sharpe test if it has a positive Sharpe.
> And after that, if the ratio of the rank Sharpe to the original Sharpe is greater than or equal to 0.5, or the rank Sharpe is greater than 0.15.

**6. 偏差测试**

> The next test is the bias test.
> The goal of the bias test is to detect any forward bias in your Alpha.
> If your Alpha passes this test, it means that while doing the backtesting, you have not used any data from a time period more recent than the simulation date.
> An expression Alpha will not fail this test, but for the python Alphas, make sure you write 'di-delay' in your codes wherever required.

**7. 相关性测试**

> The next test is the correlation test.
> This is a uniqueness test.
> An Alpha passes the correlation test versus external WebSim Alphas when one of the falling criteria is met: if the PnL correlation of the Alpha with any external WebSim Alpha is less than 0.7, it passes the test.
> If the Alpha's PnL position or trade correlation with external WebSim Alpha in the same group is less than 0.4, it would pass the test.
> And lastly, if the Alpha has 10% higher Sharpe than any Alpha in the same group with PnL positions or trade correlation above the 0.7 correlation threshold, your Alpha would pass the test.

**8. 全局相关性检查**

> The CheckCorrAll test takes at least three weekends to run, and during this time, the OSTEST status page will describe the test's result as pending.
> to make your Alpha pass this test, try new ideas, try different operators, try different categories of datasets and try alternate implementations of your ideas.

**9. 样本内夏普测试**

> The next test is the IS Sharpe test.
> The goal of the IS Sharpe test is to weed out any random noise from the true Alpha.
> To make your Alpha pass this test, try to have consistent performance across years and maximize your Sharpe.

**10. 样本外夏普测试**

> Now let's talk about the two performance tests that we have.
> The first test is the OS Sharpe test.
> Just like the IS Sharpe test, the OS Sharpe test's aim is to separate random noise from true Alpha An Alpha must meet the set requirements for the Sharpe for different intervals to pass this test.
> For a better OS Sharpe incorporate logical parameters, try not to do a lot of overfitting for your Alpha and the probability of your Alpha passing this test would be very high.

**11. 新高测试**

> The last test is the new high test.
> As the name suggests, this test is passed, when the submitted Alpha reaches a new high in the cumulative PnL curve visible to you on the platform.
> A good Alpha usually passes this test easily.

**12. 结语**

> Having understood each of these tests and the different ways to make your Alpha pass this test, please try to follow these practices before you submit your Alpha.
> This would ensure that a big piece of the Alphas submitted by you pass the tests and go into production.

---


---

# 附录 A：字幕勘误汇总（官方字幕为自动生成）

> 各视频正文内已就地标注，此处汇总便于速查。

### What is an Alpha?（什么是 Alpha）

| 位置 | 字幕原文 | 应为 | 说明 |
|---|---|---|---|
| 做多/做空段 | `equity long-shot` | `equity long-short` | ASR 误识，全篇出现 1 次；`long-short` 出现 4 次 |
| 流程段 | `to improvise your predictability` | `to improve your predictability` | ASR 误识；`improvise`（即兴）与上下文不符 |
| 流程段 | `to make it long-short neutral` | 语义正确，指"多空中性" | 对应平台设置里的**中性化（Neutralization）** |

---

### Making an Alpha: Simulation Settings（制作 Alpha：模拟设置）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 4 段 | `it helps remove any major fluctuations…` | 句首 `it` 小写，系自动断句所致，非笔误，译文按正常句首处理 |
| 第 8 段 | `the days your Alpha looks back in the past` | 口语化表达，语义清楚，未改动 |

**本视频未发现影响语义的 ASR 误识。**

---

### Making an Alpha: Simulating an Alpha（制作 Alpha：模拟一个 Alpha）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 2 段 | `the current days positions` | 缺撇号，应为 `current day's positions`，语义无歧义 |
| 第 3 段 | `the platform will present to you with the results` | 口语冗余（present to you with），非误识 |
| 全篇 | 对比视频 01/05 出现的 `improvise`（应为 `improve`） | **本视频未出现该误识**，原文即为正确的 `improve your signal` |

**本视频未发现影响语义的 ASR 误识。**

---

### Alpha expression to PnL Chart（从 Alpha 表达式到 PnL 曲线）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 3 段 | `We simulate the expression "rank of negative returns" with market neutralization, delay-1, and decay-0 settings for now. - **Column B**: The eight stocks…` | **幻灯片朗读错位**：列标签 B / C 的说明被拼进了同一段。译文已按"表达式 → 列定义"的顺序拆分还原 |
| 第 3 段 | `rank of negative returns` | 视频中是对幻灯片的**口头引用**，实际表达式为 `rank(-returns)` 一类的形式（负号 + 排序），此处保留口语原样 |
| 第 5 段 | `the average of the numbers in cell D12` | 直接朗读了表格单元格坐标，译文照录 |
| 第 7 段 | `This means we have a position of minus $4.4 million…` | 口语化表达，即 -440 万美元（空头）；译文补注了"即做空" |
| 第 13 段 | `videos four and five` | 指该系列内的后续视频，译文补注了对应的中文标题 |

**未发现其他影响语义的 ASR 误识。**

---

### Simulation Results（模拟结果）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 2 段 | `work more to **improvise** your signal` | **ASR 误识**：应为 `improve`（改进）。与视频 01 出现的是同一类错误 |
| 第 3 段 | `the whole divided by the yesterday's close price` | 多了冠词 `the`，口语瑕疵，语义无歧义 |
| 第 6 段 | `delay-0 alphas`（小写） | 大小写不规范，译文按 `Delay-0` 处理 |
| 第 8 段 | `the in depth analysis of how this aggregate performance parameters can be broken down` | 口语语法松散（this → these），非误识 |

---

### OSTests in an Alpha（Alpha 的样本外测试）

| 位置 | 字幕原文 | 说明 | 应读作 |
|---|---|---|---|
| 第 7 段 | `when one of the **falling** criteria is met` | **ASR 误识** | `following criteria`（满足以下任一条件） |
| 第 6 段 | `make sure you write **'di-delay'** in your codes wherever required` | **词义不明**：`di-delay` 非任何已知函数名，疑为 ASR 把 `delay` 前后的词粘连所致 | 语义为"Python Alpha 须在代码里显式声明数据延迟"。**具体写法以平台 Python API 文档为准，本归档不作臆测** |
| 第 1 段 | `in the OSTEST-PENDING phase The OSTEST-FAIL status…` | 两句被拼成一段（缺句号） | 应为两句话 |
| 第 4 段 | `And Alpha will pass the SuperUniverse test` | 口语误读 | `An Alpha will pass…` |
| 第 5 段 | `the power with the exponential three` | 口语表达 | 即 `power(x, 3)`，指数为 3 的幂算子 |
| 第 7 段 | `The Alpha's PnL position or trade correlation` | 缺标点 | 应为 `PnL, position, or trade correlation`（PnL / 持仓 / 交易相关性） |
| 第 10 段 | `separate random noise from true Alpha An Alpha must meet…` | 两句被拼成一段 | 应为两句话 |

---


---

# 附录 B：术语总表（跨视频合并去重）

> 按英文术语去重；同一术语在多个视频出现时保留首次出现处的解释。

| 英文 | 中文 | 说明 | 公式 / 口径 |
|---|---|---|---|
| 252 | 年交易日数 | 年化因子 | — |
| capital distribution | 资金分布 | 权重在不同标的/分组上的分布 | — |
| capitalization | 市值 | 分组维度（大盘/中盘/小盘） | — |
| concentration risk | 集中度风险 | 表现过于依赖单一分组 | — |
| coverage | 覆盖率 | 有持仓标的的占比 | — |
| drawdown | 回撤 | 任一年最大亏损百分比；越低越好 | — |
| information ratio (IR) | 信息比率 | 预测能力的代理 | mean(日PnL) / std(日PnL) |
| PnL | 盈亏 | 持仓与收益率的乘积求和 | Σ(position × daily return) |
| return-to-drawdown | 收益回撤比 | 目标 > 1，越高越好 | returns / drawdown |
| returns | 收益率 | 每年收益 = 该年日收益均值 | (今收 − 昨收) / 昨收 |
| robust | 稳健 | 表现来源分散 | — |
| Sharpe ratio | 夏普比率 | 年化后的 IR | IR × √252 |
| turnover | 换手率 | 交易成本；目标 < 40% | value traded / value held |


---

# 附录 C：面试考点汇总

## 视频 2｜Making an Alpha: Simulation Settings（制作 Alpha：模拟设置）

- **为什么高流动性池子更难做 Alpha？** 可交易量大 → 信息消化快 → 定价更充分、alpha 更难榨取；但成本低，所以做出来更值钱。这是"难度换价值"的权衡。
- **Delay-0 和 Delay-1 的差别**：数据时点不同，Delay-0 用当天数据、通常换手更高。
- **Decay 是降换手的主要手段之一**，与 `hump`、`trade_when` 同属"减少无谓换手"的工具族。
- **Truncation 与 Check Weight 测试的关系**：设 ≤0.1 基本可以保证通过权重检查（详见视频 06）。
- **回溯天数必须 ≥ 表达式实际回溯窗口**，否则平台会报错（例如用了 `ts_mean(x, 60)`，lookback 至少 60）。
- **中性化两种做法**：面板设置 vs 表达式里的 `IndNeut` / `group_neutralize`，可自定义分组。

## 视频 3｜Making an Alpha: Simulating an Alpha（制作 Alpha：模拟一个 Alpha）

- **完整流程**：想法 → 选算子和数据集 → 定模拟设置 → 写表达式 → 逐标的求值构建组合 → 按值分配权重 → 每日重复 → 算 PnL。
- **中性化发生在哪一步？** 表达式值（原始值）**不直接用**，先做中性化得最终值，再决定多空方向。这是"raw value vs final value"的关键区分。
- **符号规则**：最终值为负 → 做空；为正 → 做多；NaN → 空仓不产生 PnL。这条在调试表达式时是判断方向的最直接依据。
- **两类输出**：汇总参数（4 个） + 明细拆解（资金分布 / 覆盖率 / Sharpe / 按市值·行业·板块分组的 PnL）。
- **面试高频结论**：**分散度越高，Alpha 越稳健**——因为量化 Alpha 交易的是"一大篮子股票"，而不是少数几只。

## 视频 4｜Alpha expression to PnL Chart（从 Alpha 表达式到 PnL 曲线）

**这是六条视频里最容易被追问的一条，七个步骤要能复述：**

| 步骤 | 做什么 | 关键点 |
|---|---|---|
| 1 | 逐标的求值，生成 Alpha 向量 | Delay-1 用 T-1 数据生成 T 日向量 |
| 2 | 中性化：减去分组均值 | 和 = 0，正数之和 = 负数之和 |
| 3 | 归一化 | 绝对值之和 = 1 |
| 4 | 按权重分配资金，建组合 | 2000 万美元虚拟账本，多空对冲 |
| 5 | 用次日实际收益算当日 PnL | 头寸 × 收益率，逐股求和 |
| 6 | 对 IS 期每一天重复 1~5 | 得到逐日 PnL |
| 7 | 累加得累计 PnL 曲线 | 2016-02 ~ 2021-01 为 IS；2021-02 ~ 2023-01 为 OS（不可见） |

**容易问到的细节：**

- **为什么是 2000 万美元？** 这是平台的固定名义账面规模，用于把归一化权重换算成美元头寸。
- **多空为什么能对冲？** 第 4 步的美元头寸中有正有负，正数（多头）与负数（空头）金额相互抵消，策略**不依赖市场方向**。
- **中性化分组不同会怎样？** 换成 80 只股票 / 10 组时，模拟器**对每组各做一遍第 2~5 步**，最后**把各组 PnL 相加**。
- **Decay 多做了什么？** 多一步：把**今天的权重**与**前几天的衰减权重**做加权平均得到最终权重——这就是 Decay 能降换手、防止"反应过度"的原因。
- **IS / OS 的边界**：IS 五年可见、OS 两年不可见；**只有 IS 与 OS 双双通过，才算稳健 Alpha**（与视频 06 的 OSTests 直接衔接）。
- **NaN 的处理**（视频 03 已述，本视频第 1 步隐含）：向量中 NaN 表示不持仓。

## 视频 5｜Simulation Results（模拟结果）

**四个核心指标的公式必须记住：**

| 指标 | 公式 | 目标 |
|---|---|---|
| 日收益率 | (今日收盘 − 昨日收盘) / 昨日收盘 | — |
| 年化收益率 | 该年日收益率的**平均** | — |
| PnL | Σ(持仓 × 当日收益率) | 越高越好 |
| IR | mean(daily PnL) / std(daily PnL) | 越高越好 |
| Sharpe | IR × √252 | 越高越好 |
| Turnover | 成交价值 / 持仓价值 | **< 40%**（Delay-0 与 Delay-1 同样要求） |
| Drawdown | 任一年最大亏损百分比 | 越低越好 |
| 收益/回撤 | returns ÷ drawdown | **> 1** |

**易被追问的点：**

- **为什么 252？** 一年估计的交易日数，是 IR 年化成 Sharpe 的因子。
- **PnL 越高越好吗？** 是，但**不能只看 PnL**——要看**风险调整后**的 Sharpe/IR，这才是预测能力的代理。
- **"一致性"为什么重要？** 多年 IR/Sharpe 稳定 = 信号跨年份工作良好 = 更值得投钱。
- **Delay-0 的换手率通常更高**，但 40% 的底线对两类 Alpha 都适用。
- **回撤看两个方向**：回撤**绝对水平要低**，同时**收益/回撤比值要高**——不要只记一个。
- **为什么要看分散度？** 量化 Alpha 交易的是一大篮子股票；表现来源分散 = 不依赖单一板块/行业/市值，**防集中度风险**，这也是**样本外能活下来**的关键。

## 视频 6｜OSTests in an Alpha（Alpha 的样本外测试）

**基础测试 8 项**（`OSTEST-PENDING` 阶段）

| # | 测试 | 通过条件 | 改进手段 |
|---|---|---|---|
| 1 | **Check Weight** | 单股最大权重 **< 10%**；不能长期只有极少数股票有权重 | **Truncation 设 < 0.1** |
| 2 | **Subuniverse** | 次小股票池 Sharpe **> 屏幕公式值**（Delay-0/1 公式不同） | 在**更小池**上开发，在**更大池**上提交 |
| 3 | **SuperUniverse** | 次大股票池 Sharpe **> 0.7 × 自身 Sharpe** | 提交前检查次大池表现 |
| 4 | **Rank Sharpe** | RankSharpe **> 0** 且（**RankSharpe/Sharpe ≥ 0.5** 或 **RankSharpe > 0.15**） | 提升信号线性度 |
| 5 | **Bias** | 无前视偏差 | 表达式 Alpha 不会失败；Python Alpha 须显式声明延迟 |
| 6 | **Correlation** | 三者任一：与外部 WebSim Alpha 的 **PnL corr < 0.7**；或同组的 **PnL/持仓/交易 corr < 0.4**；或 Sharpe **高 10%** | 换数据、换算子、换实现 |
| 7 | **CheckCorrAll** | 全局相关性通过（**≥ 3 个周末**） | 新想法 / 不同算子 / 不同类别数据集 / 替代实现 |
| 8 | **IS Sharpe** | 剔除随机噪声，跨年表现一致且 Sharpe 最大化 | 提高跨年一致性 |

**表现测试 2 项**（`OSTEST2-PENDING` 阶段，通常更慢）

| # | 测试 | 通过条件 | 改进手段 |
|---|---|---|---|
| 9 | **OS Sharpe** | 满足不同时间区间的 Sharpe 要求 | **参数讲逻辑、不要过拟合** → 通过概率很高 |
| 10 | **New High** | 提交的 Alpha 在累计 PnL 曲线上**创新高** | 好的 Alpha 通常轻松通过 |

**面试高频追问：**

- **8 + 2 的划分**：基础测试 8 项（提交前即可执行部分） + 表现测试 2 项（`OSTEST2-PENDING`，耗时更长）。
- **`OSTEST-FAIL` 的含义**：不是"某一个测试失败"，而是**至少一项基础测试没通过**。
- **权重检查的两个失败条件**：① 权重过度集中（如单股 30%）；② 一年中相当多天数只有极少股票有权重。**开盘全零不算失败**。
- **相关性测试是"唯一性测试"**：这是与我们项目里"相关性墙"直接对应的官方口径——**三种过法**（外部 < 0.7 / 同组 < 0.4 / Sharpe 高 10%）。
- **CheckCorrAll 为什么慢？** 需要**至少三个周末**跑批，期间状态一直是 pending。
- **IS Sharpe 与 OS Sharpe 的分工**：两者都在"剔除随机噪声"，区别是一个在样本内、一个在样本外；**OS 靠的是不过拟合**。
- **本项目实证呼应**：我们在 `SUBMITTED_LEDGER` 里遇到的 selfCorr ≥ 0.7 触发生产相关性测试，正是第 6 项的机制；我们用的"豁免线 = 1.10 × 对手 Sharpe"，也正对应第 6 项的**第 3 种过法（Sharpe 高 10%）**。
