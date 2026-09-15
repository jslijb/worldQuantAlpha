# ⭐ Alpha Examples for Beginners

> **归档信息**
> - 页面：<https://platform.worldquantbrain.com/learn/documentation/19-alpha-examples>
> - 页面 id：`19-alpha-examples` ｜ 课程：`Creating Alphas` ｜ 预计时长：PT4M
> - 平台最后更新：2026-08-26T01:38:39.415361-04:00
> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写
> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15

---


## Operating Earnings Yield

**Hypothesis**

If the operating income of a company is currently higher than its past 1 year history, buy the company’s stock and vice-versa.

**Implementation**

Using ts_rank to identify current performance of the company compared to its own history, using the fundamental data field "operating_income".

**Hints to Implement**

Rather than comparing the value directly, can calculating a ratio that includes stock market moves, improve the signal?


**示例 Alpha 表达式**

```
ts_rank(operating_income,252)
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `SUBINDUSTRY` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |



## Appreciation of liabilities

**Hypothesis**

An increase in the fair value of liabilities could indicate a higher cost than expected. This may deteriorate the company's financial health, potentially leading to lower profitability or financial distress.

**Implementation**

Go short when there is an increase in the fair value of liabilities within a year and long when the opposite occurs using fundamental data.

**Hints to Implement**

Could observing the increase over a shorter period improve accuracy?


**示例 Alpha 表达式**

```
-ts_rank(fn_liab_fair_val_l1_a,252)
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `SUBINDUSTRY` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |



## Power of leverage

**Hypothesis**

Companies with high liability-to-asset ratios – excluding those with poor financial health or weak cashflows – often leverage debt as a strategic tool to pursue aggressive growth initiatives. By effectively utilizing financial leverage, these firms are more likely to deliver outsized returns, as they reinvest borrowed capital into high-potential opportunities.

**Implementation**

Use the ‘liabilities’ and ‘assets’ to design the ratio.

**Hint to improve the Alpha**

This ratio can vary significantly across industries. Would it be worth considering alternative neutralization settings?


**示例 Alpha 表达式**

```
liabilities/assets
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `MARKET` |
| Truncation（`truncation`） | `0.01` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |



## Earnings Yield Momentum

**Hypothesis**

Stocks whose earnings yield has been high more often over the last quarter, relative to their own history, may be undervalued thus we should long them

**Implementation**

Use EPS-to-price ratio as earnings yield proxy, compare over its own past, and compare it within its industry.

**Hint to improve the Alpha**

Use NAN HANDLING to preprocess data and boost the performance


**示例 Alpha 表达式**

```
group_rank(ts_rank(est_eps/close, 60),industry)
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `INDUSTRY` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |



## Short-Term Sentiment Volume Stability

**Hypothesis**

A high 10-day standard deviation of sentiment volume for a stock means that investor attention is unstable, with frequent spikes and drops in how much the stock is discussed. This unstable attention is often driven by short-lived news or hype and may lead to noisy, unsustainable price moves, causing the stock to underperform afterward.

**Implementation**

Take the 10-day rolling standard deviation of relative sentiment volume scl12_buzz and negate it.

**Hint to improve the Alpha**

Would observing stability over a shorter horizon be more effective for more liquid stocks?


**示例 Alpha 表达式**

```
-ts_std_dev(scl12_buzz, 10)
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `INDUSTRY` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |

