# 视频 02｜Making an Alpha: Simulation Settings（制作 Alpha：模拟设置）— 中英逐段对照

> **归档信息**
> - 课程页：https://platform.worldquantbrain.com/learn/courses/introduction-alphas/making-alpha-simulation-settings
> - 课程组：`introduction-alphas`（Introduction to Alphas 系列，共 6 个视频）
> - 视频标题：**Making an Alpha: Simulation Settings** ｜时长 **4 分 03 秒** ｜语言：英文
> - 视频源：YouTube（uid `-HM9LogpgY4`）
> - 字幕来源：**平台官方 transcript**（经 `GET /video-courses` 取得，非本地 ASR），抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译（universe→股票池、long/short→多/空、neutralization→中性化、exposure→敞口、turnover→换手率）；译文中括号内英文为原词。
> - ⚠️ 官方字幕是自动生成的，本视频未发现影响语义的 ASR 误识（详见文末「字幕勘误」）。

---

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

## 三、字幕勘误（官方字幕为自动生成）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 4 段 | `it helps remove any major fluctuations…` | 句首 `it` 小写，系自动断句所致，非笔误，译文按正常句首处理 |
| 第 8 段 | `the days your Alpha looks back in the past` | 口语化表达，语义清楚，未改动 |

**本视频未发现影响语义的 ASR 误识。**

---

## 四、本视频的量化术语对照

| 英文 | 中文 | 说明 |
|---|---|---|
| region | 区域 | 交易市场范围（USA / CHN / EUR 等） |
| universe | 股票池 | 按流动性等条件筛出的可交易标的集合 |
| Delay | 延迟 | 数据时点；Delay-1 = 用昨天数据，Delay-0 = 用当天数据 |
| Decay | 衰减 | 对过去若干天的 Alpha 值做加权求和，降换手、抗离群 |
| neutralization | 中性化 | 扣掉分组均值，使多空敞口对冲 |
| `IndNeut` | 行业中性算子 | 在表达式里做中性化，可自定义分组 |
| Truncation | 截断 | 限制单只股票的最大权重上限 |
| exposure | 敞口 | 在某个标的/风险因子上的净头寸 |
| turnover | 换手率 | 成交价值 / 持仓价值，衡量交易成本 |
| lookback days | 回溯天数 | Alpha 表达式往回看的历史长度 |
| tradable volume | 可交易量 | 决定信息被消化的速度 |

---

## 五、与本视频相关的面试考点

- **为什么高流动性池子更难做 Alpha？** 可交易量大 → 信息消化快 → 定价更充分、alpha 更难榨取；但成本低，所以做出来更值钱。这是"难度换价值"的权衡。
- **Delay-0 和 Delay-1 的差别**：数据时点不同，Delay-0 用当天数据、通常换手更高。
- **Decay 是降换手的主要手段之一**，与 `hump`、`trade_when` 同属"减少无谓换手"的工具族。
- **Truncation 与 Check Weight 测试的关系**：设 ≤0.1 基本可以保证通过权重检查（详见视频 06）。
- **回溯天数必须 ≥ 表达式实际回溯窗口**，否则平台会报错（例如用了 `ts_mean(x, 60)`，lookback 至少 60）。
- **中性化两种做法**：面板设置 vs 表达式里的 `IndNeut` / `group_neutralize`，可自定义分组。
