# Scoring Algorithm for Challenge Users

> **归档信息**
> - 页面：<https://platform.worldquantbrain.com/learn/documentation/scoring-algorithm-challenge-users>
> - 页面 id：`scoring-algorithm-challenge-users` ｜ 课程：`Getting Started` ｜ 预计时长：-
> - 平台最后更新：2026-08-25T23:35:55.862589-04:00
> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写
> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15

---


## Scoring Algorithm for Challenge Users

This page provides details on the scoring mechanism used to calculate Challenge scores. This page will be used to communicate and detail any changes that may be made to the scoring algorithm over time. All BRAIN platform users are advised to regularly check this page.


## User on-boarding algorithm description

- Score could be accumulated by submitting [Alphas](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=A-,Alpha,-An)
- Score is tied to day, not to individual Alphas
- [In-Sample](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=details.-,In-sample%20(IS),-In) performance of Alphas is taken into consideration while calculating scores.
- User onboarding algorithm provides rough estimation of which scoring system to expect after becoming a [consultant](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=Dataset.-,Consultant,-WQBrain)
- Scores will update once everyday.
- Each day all user Alphas are being accumulated and several factors are being calculated:

- **Quantity Factor:**

- Larger the number of Alphas submitted during a day, larger will be the score

- **Quality factor:**

- Quality factor is calculated as an average of the quality factor of all Alphas submitted during the day
- The quality factor considers several sub factors for each Alpha:

- [Universe](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=U-,Universe,-Universe) (smaller universes get more score)
- [SelfCorrelation](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=details%C2%A0*).-,Self%20correlation,-Maximum) (the less the better)
- [Fitness](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=ratios.-,Fitness,-Fitness) (the larger the better)
- [Delay](https://support.worldquantbrain.com/hc/en-us/articles/4902349883927-Click-here-for-a-list-of-terms-and-their-definitions#:~:text=days-,Delay,-An) (D1 Alphas contribute more to score than D0 Alphas)

- Values of both factors are being normalized across all the users who submitted at least one Alpha on that particular day
- Final daily score is a function of normalized Quantity and Quality Factors (the larger one’s factor values the more score one gets)
- Maximum daily score is 2000. Typically, this involves submitting 1 to 2 alphas a day.
- To reach qualification levels one needs to score:

- For BRONZE level 1000
- For SILVER level 5000
- For GOLD level 10000

We expect to update this page at least a few times a year. Please ensure you review it periodically. We will send out BRAIN platform announcements notifying you of any changes. Please make sure you log in and read all BRAIN platform announcements regularly.
