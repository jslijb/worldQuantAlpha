# ⭐ Alpha Examples for Bronze Users 🥉

> **归档信息**
> - 页面：<https://platform.worldquantbrain.com/learn/documentation/sample-alpha-concepts>
> - 页面 id：`sample-alpha-concepts` ｜ 课程：`Creating Alphas` ｜ 预计时长：PT2M
> - 平台最后更新：2026-08-26T00:06:12.208988-04:00
> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写
> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15

---


## Valuation based on cash flow

**Hypothesis**

A lower EV/CF usually suggests the company is becoming cheaper relative to its cash-generating ability; a higher multiple suggests it’s getting more expensive.

**Implementation**

Use ts_zscore to standardize the chang of the ratio and group_rank to control the turnover.

**Hint to Improve Alpha**

There are various types of cash flow, and switching the type used in the metric may improve its performance.


**示例 Alpha 表达式**

```
group_rank(-ts_zscore(enterprise_value/cashflow, 63),industry)
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



## Overpriced stocks

**Hypothesis**

When analyst price target estimates (est_ptp) and free cashflow estimates (est_fcf) move highly in sync over the past month (high positive correlation), it may signal that the market has already fully priced in the cash flow expectations into price targets — leaving little room for further upside.

**Implementation**

Using est_ptp to capture price estimate and est_fcf to capture free cash flow and calculate the dynamics between them with ts_corr.

**Hint to Improve Alpha**

The window of 1 year might be too long to react on the price correction. Try shorter window.


**示例 Alpha 表达式**

```
-ts_corr(est_ptp,est_fcf,252)
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP3000` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `MARKET` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |



## Volatility arbitrage

**Hypothesis**

Higher volatility is often observed during bearish markets, while lower volatility is typically seen during bullish markets. A lower Parkinson's volatility coupled with a higher implied volatility may suggest that there could be a stronger bullish sentiment for the stock in the future.

**Implementation**

Long the stock if its implied volatility significantly exceeds its historical volatility and short the opposite

**Hint to Improve Alpha**

Can you use ts_backfill to avoid missing data on certain days?


**示例 Alpha 表达式**

```
implied_volatility_call_120/parkinson_volatility_120
```

| 设置项 | 值 |
|---|---|
| 标的类型（`instrumentType`） | `EQUITY` |
| 地区（`region`） | `USA` |
| 股票池（`universe`） | `TOP200` |
| Delay（`delay`） | `1` |
| Decay（`decay`） | `0` |
| 中性化（`neutralization`） | `SECTOR` |
| Truncation（`truncation`） | `0.08` |
| Pasteurization（`pasteurization`） | `ON` |
| Unit Handling（`unitHandling`） | `VERIFY` |
| NaN Handling（`nanHandling`） | `OFF` |
| 语言（`language`） | `FASTEXPR` |
| Max Trade（`maxTrade`） | `OFF` |

