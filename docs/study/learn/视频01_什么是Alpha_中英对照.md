# 视频 01｜What is an Alpha?（什么是 Alpha）— 中英逐段对照

> **归档信息**
> - 课程页：https://platform.worldquantbrain.com/learn/courses/introduction-alphas/alpha
> - 课程组：`introduction-alphas`（Introduction to Alphas 系列，共 6 个视频）
> - 视频标题：**What is an Alpha?** ｜时长 **4 分 14 秒** ｜语言：英文
> - 视频源：Vidyard（uid `T41ioYrY5YS174NiMZZFhy`）
> - 字幕来源：**平台官方 transcript**（经 `GET /video-courses` 取得，非本地 ASR），抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译（universe→股票池、long/short→多/空、market-neutral→市场中性、exposure→敞口、spread→价差）；译文中括号内英文为原词。
> - ⚠️ 官方字幕是自动生成的，存在少量 ASR 误识，已在文中就地标注修正（见文末「字幕勘误」）。

---

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

## 三、字幕勘误（官方字幕为自动生成）

| 位置 | 字幕原文 | 应为 | 说明 |
|---|---|---|---|
| 做多/做空段 | `equity long-shot` | `equity long-short` | ASR 误识，全篇出现 1 次；`long-short` 出现 4 次 |
| 流程段 | `to improvise your predictability` | `to improve your predictability` | ASR 误识；`improvise`（即兴）与上下文不符 |
| 流程段 | `to make it long-short neutral` | 语义正确，指"多空中性" | 对应平台设置里的**中性化（Neutralization）** |

---

## 四、本视频的量化术语对照（已并入总纲术语表）

| 英文 | 中文 | 备注 |
|---|---|---|
| Alpha | Alpha（不译）／预测信号 | 平台专有名词，不翻译 |
| fictitious portfolio | 虚拟投资组合 | 回测里并非真实持仓 |
| long / short position | 多头／空头头寸（做多／做空） | — |
| equity long-short market-neutral | 股票多空市场中性 | 对冲基金常用策略 |
| downside protection | 下行保护 | 控制回撤方向的风险 |
| risk adjusted returns | 风险调整后收益 | — |
| long only portfolio | 纯多头组合 | 与多空组合相对 |
| exposure | 敞口 | **禁止**译"暴露" |
| spread | 价差 | 两只股票之间的差 |
| universe | 股票池 | **禁止**译"宇宙" |
| instrument | 标的 | **禁止**译"工具" |
| vector | 向量 | Alpha 输出即向量 |
| sign / magnitude | 符号／数值大小 | Alpha 的两个属性 |
| expression | （快速）表达式 | Fast Expression |
| operation / operator | 算子 | 平台共 66 个 |
| long-short neutral | 多空中性 | 对应 Neutralization 设置 |
