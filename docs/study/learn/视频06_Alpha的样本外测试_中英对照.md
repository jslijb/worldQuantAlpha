# 视频 06｜OSTests in an Alpha（Alpha 的样本外测试）— 中英逐段对照

> **归档信息**
> - 课程页：https://platform.worldquantbrain.com/learn/courses/introduction-alphas/ostests-alpha
> - 课程组：`introduction-alphas`（Introduction to Alphas 系列，共 6 个视频）
> - 视频标题：**OSTests in an Alpha** ｜时长 **8 分 31 秒** ｜语言：英文
> - 视频源：YouTube（uid `b9VQEoCvBVU`）
> - 字幕来源：**平台官方 transcript**（经 `GET /video-courses` 取得，非本地 ASR），抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译（subuniverse→次小股票池、rank Sharpe→排序后夏普、truncation→截断、forward bias→前视偏差）；译文中括号内英文为原词。
> - ⚠️ 官方字幕是自动生成的，本视频有两处 ASR 误识（`falling`→`following`、`di-delay` 词义不明），已在文中就地标注。
> - 📌 **本视频是提交前的"验收清单"**，10 项测试的通过条件与改进手段，与考纲「提交测试」一节直接对应。

---

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

## 三、字幕勘误（官方字幕为自动生成）

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

## 四、本视频的量化术语对照

| 英文 | 中文 | 说明 |
|---|---|---|
| production | 生产环境 | Alpha 通过测试后被实盘使用 |
| base test | 基础测试 | 8 项，`OSTEST-PENDING` 阶段 |
| performance test | 表现测试 | 2 项，`OSTEST2-PENDING` 阶段 |
| `OSTEST-FAIL` | 测试失败状态 | 至少一项基础测试未通过 |
| check weight test | 权重检查 | 单股最大权重 < 10% |
| truncation | 截断 | 控制单股权重上限；设 < 0.1 可过权重检查 |
| subuniverse | 次小股票池 | 下一个更小的标准股票池 |
| superuniverse | 次大股票池 | 下一个更大的标准股票池 |
| rank Sharpe | 排序后夏普 | 多空两侧分别 `rank` + `power(·,3)` 后缩放回原规模 |
| forward bias | 前视偏差 | 使用了比模拟日更近期的数据 |
| expression Alpha | 表达式 Alpha | 用 Fast Expression 写的 Alpha |
| correlation test | 相关性测试 | 唯一性测试 |
| uniqueness test | 唯一性测试 | 检查与已有 Alpha 是否雷同 |
| WebSim Alpha | 外部 WebSim Alpha | 平台侧用于比对的已有 Alpha 池 |
| PnL / position / trade correlation | PnL / 持仓 / 交易相关性 | 三种相关性口径 |
| CheckCorrAll | 全局相关性检查 | 耗时 ≥ 3 个周末 |
| IS Sharpe / OS Sharpe | 样本内 / 样本外夏普 | 剔除随机噪声 |
| new high test | 新高测试 | 累计 PnL 曲线创新高 |
| overfitting | 过拟合 | 会导致 OS Sharpe 不达标 |

---

## 五、十项测试速查表（面试可直接背）

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
