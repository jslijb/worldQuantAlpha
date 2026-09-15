# 视频 04｜Alpha expression to PnL Chart（从 Alpha 表达式到 PnL 曲线）— 中英逐段对照

> **归档信息**
> - 课程页：https://platform.worldquantbrain.com/learn/courses/introduction-alphas/alpha-expression-to-pnl
> - 课程组：`introduction-alphas`（Introduction to Alphas 系列，共 6 个视频）
> - 视频标题：**Alpha expression to PnL Chart** ｜时长 **11 分 22 秒** ｜语言：英文
> - 视频源：YouTube（uid `bXOirnDpZsM`）
> - 字幕来源：**平台官方 transcript**（经 `GET /video-courses` 取得，非本地 ASR），抓取日期 2026-09-15
> - 译法：按量化行业习惯翻译（rank→排序/排名、neutralization→中性化、book size→账面规模、in-sample→样本内、out-of-sample→样本外）；译文中括号内英文为原词。
> - ⚠️ 官方字幕是自动生成的，本视频有若干处幻灯片朗读错位（列标签与文字顺序被打乱），已在译文中按逻辑还原，并在文末「字幕勘误」逐条列出。
> - 📌 **本视频是六条里信息密度最高的一条**，它把"表达式 → 权重 → 持仓 → PnL"的完整机制拆成七步演示，是理解回测原理的核心。

---

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

## 三、字幕勘误（官方字幕为自动生成）

| 位置 | 字幕原文 | 说明 |
|---|---|---|
| 第 3 段 | `We simulate the expression "rank of negative returns" with market neutralization, delay-1, and decay-0 settings for now. - **Column B**: The eight stocks…` | **幻灯片朗读错位**：列标签 B / C 的说明被拼进了同一段。译文已按"表达式 → 列定义"的顺序拆分还原 |
| 第 3 段 | `rank of negative returns` | 视频中是对幻灯片的**口头引用**，实际表达式为 `rank(-returns)` 一类的形式（负号 + 排序），此处保留口语原样 |
| 第 5 段 | `the average of the numbers in cell D12` | 直接朗读了表格单元格坐标，译文照录 |
| 第 7 段 | `This means we have a position of minus $4.4 million…` | 口语化表达，即 -440 万美元（空头）；译文补注了"即做空" |
| 第 13 段 | `videos four and five` | 指该系列内的后续视频，译文补注了对应的中文标题 |

**未发现其他影响语义的 ASR 误识。**

---

## 四、本视频的量化术语对照

| 英文 | 中文 | 说明 |
|---|---|---|
| rank | 排序算子 | 把输入值排序并映射到 0~1 均匀分布 |
| reversion idea | 均值回归想法 | 赌今天跌的明天反弹 |
| evaluate | 求值 | 表达式在每个标的上的计算 |
| alpha vector | Alpha 向量 | 每只股票一个取值 |
| neutralization | 中性化 | 减去分组均值，使向量和为 0 |
| scaled / normalized | 缩放 / 归一化 | 使绝对值之和为 1 |
| normalized vector of weights | 归一化权重向量 | 可直接乘以资金规模 |
| fictitious book of $20 million | 2000 万美元虚拟账本 | 平台的固定名义资金规模（book size） |
| book size | 账面规模 | 用于把权重换算成美元头寸 |
| long-short market neutralization | 多空市场中性化 | 多空对冲，赚价差而非方向 |
| in-sample period (IS) | 样本内区间 | 可见的回测区间 |
| out-of-sample period (OS) | 样本外区间 | 模拟窗口不可见，提交后由平台检验 |
| cumulative PnL chart | 累计 PnL 曲线 | 回测输出的主图 |
| decay | 衰减 | 新旧权重做加权平均，越近权重越大 |
| overly reactive | 反应过度 | 换手过高的成因之一 |
| robust alpha | 稳健的 Alpha | IS 与 OS 双通过 |

---

## 五、与本视频相关的面试考点

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
