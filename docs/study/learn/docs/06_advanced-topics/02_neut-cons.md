# Neutralization 🥉

> **归档信息**
> - 页面：<https://platform.worldquantbrain.com/learn/documentation/neut-cons>
> - 页面 id：`neut-cons` ｜ 课程：`Advanced Topics` ｜ 预计时长：PT5M
> - 平台最后更新：2026-08-26T03:47:37.627939-04:00
> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写
> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15

> 📝 该视频在课程库中**有官方字幕**：`introduction-quantitative-finance` → `creating-quant-alpha`（Creating a Quant Alpha，4994 字符），可直接翻译。见 `课程视频总表.md`

---

**I. Basic Neutralization:**

Neutralization is an operation in which the raw Alpha values are split into groups, and then normalized (the mean is subtracted from each value) within each group. The group can be the entire market, or the groups could be made using other classifications like industry or sub-industry.

This is done to focus on the relative returns of stocks within the group, and minimize risk exposure to the returns of the group. As a consequence of neutralization, the portfolio is half long, half short, and may guard the portfolio from market or industry shocks.

> 🎬 **内嵌视频**（193s ~ 262s）：<https://www.youtube.com/watch?v=A3RNoYAz_9U&t=193s>

For example, while trading, we don't want to bet in the direction of market, in order to minimize "market risk". This is done by taking equal long and short positions, i.e. amount invested in long positions is roughly equal to that in short positions. This is called "market neutralization". In order to do this in BRAIN platform, we set Neutralization = market (or industry or sub-industry, as desired) in the simulation settings.

In addition to market neutralization, Sector, industry, and subindustry neutralization are present on BRAIN. Examining the hierarchy on the BRAIN, a sector is a super set of an industry, which in turn is a super set of a subindustry. For example, industrials is a sector that includes the machinery industry, within which the agricultural and farm machinery subindustry resides.

Suppose we have Alpha = -ts_delta (close, 5), where Alpha is the vector of values. Setting neutralization = market, would make the mean of the Alpha vector equal to zero, i.e. the Alpha vector would undergo the change: Alpha = Alpha - mean(Alpha).

This new vector is then normalized and scaled to booksize. The portfolio thus formed would contain equal money invested in long and short positions, and can be used to calculate that day's PnL.

When you simulate an Alpha, the platform automatically performs some operations in Setting on your submission. "Neutralization in Simulation Settings" neutralizes your alpha as the last step in the operations. This ensures that your Alpha is long short neutral.

“Neutralization in Simulation Settings” and ‘group_neutralize(x, group)’ use the same operation.

When to use group_neutralize: You can use group_neutralize(x, group) when you want to apply neutralization in a more granular fashion on your Alpha with different values of group.

What settings to use with group_neutralize: If you use `group_neutralize(x, group)` as the last operator, you can set “None” in Neutralization, “0” in Decay and “0” in Truncation in Simulation Settings ( value 0 will disable decay and truncation operators) . You can insert a decay/truncation operator directly in your alpha expression before group_neutralize.

Are ‘group_neutralize(x, group)’ and “Neutralization in Simulation Settings” interchangeable?

Yes, for example:

Suppose we have Alpha = -rank(ebit/capex), where Alpha is the vector of values.

alpha1 = -zscore(ebit/capex) with industry in Neutralization “0” in Decay and “0” in Truncation in Simulation Settings

alpha1 = group_neutralize(-zscore(ebit/capex),industry) “None” in Neutralization, “0” in Decay and “0” in Truncation

Tips:

- Always pick a value for neutralization; only leave it as None if neutralization is manually incorporated in the Alpha.
- Try larger stock groups for more liquid universes that have less number of stocks since we want to have the decent number of stocks in each group
- Try smaller stock groups for illiquid universes
- Use ‘country’ and ‘exchange’ neutralization options for EUR, ASI regions

**Below are some of the recommended neutralization based on the dataset category. We highly recommend you to try these in your research**

Dataset
Market
Sector
Industry
Subindustry
Remarks



Fundamental Datasets


✔️

Fundamentals of a company can affect stock price in a different way depending on the industry, so an industry neutralization is recommended. 


Analysts Datasets


✔️

Analyst datasets provide an estimate of future fundamental data, hence an industry neutralization is recommended here as well


Model Datasets
✔️
✔️
✔️
✔️
Model datasets can be extremely variable depending on the subcategory of the dataset available. Try experimenting with different neutralization categories based on those subcategories to find the best result. 


News Datasets



✔️
News could have very different impact on different companies, based on their subindustry. Impact of a CEO change can be different for Twitter and Apple Inc even though both are in the broader Tech industry. Hence, try neutralizing for subindustry.


Option Datasets
✔️
✔️


For Options datasets, we suggest neutralizing for Market or Sector, because the impact of options on a stock price is almost similar across broader industries.


Price Volume Datasets
✔️
✔️


Generic ideas work well across all instruments, using Industry or Subindustry neutralization could reduce the performance. 


Social Media Datasets


✔️
✔️
Social media impact could have different impact on different companies, based on the subindustry, so try neutralizing at the subindustry level.  You can also try neutralizing at the industry level as well depending on how broadly applicable the news is.


Institutions Datasets

✔️
✔️

Depends on the type of institution datasets available, who provides them, and its implications. Test out neutralizations for Sector or Industry.


Short Interest Datasets


✔️

Industry neutralization is recommended for Short Interest datasets. Try others as well!


Insider Datasets


✔️
✔️
Insider news will not necessarily affect each company in a similar way, since it is based on the industry or subindustry. Hence, neutralize for those categories with these datasets.  


Sentiment Datasets


✔️
✔️
Similar to insider/social media, sentiment could have different impact on different companies, based on the industry or subindustry, so neutralize for those categories.


Earnings Datasets


✔️

For Earnings datasets, Industry neutralization recommended, similar to Fundamental datasets


Macro Datasets
✔️
✔️
✔️

Sector/Market/Industry are macro-economic activities, so neutralizing Macro datasets for those categories will be best. There is not much difference across subindustries.
