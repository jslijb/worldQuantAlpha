# Tasks — WorldQuant Alpha 挖掘系统任务清单

> 执行清单。写代码最终参考本文件。spec.md 变更后同步更新。

## 当前状态：✅ 已提交 21 个 ACTIVE Alpha（2026-09-03 提交 5 个，当日目标达成）

## 已完成任务

- [x] **T1** 项目整理：删除 17 个临时脚本
- [x] **T2** 建立 SDD 文档体系（docs/spec.md, design.md, tasks.md, pitfalls.md）
- [x] **T3** 编写项目 README
- [x] **T4** 挖掘一个新 Alpha 因子并提交
- [x] **T5** 记录挖掘结果到 pitfalls.md / README
- [x] **T6** 为 utils.submit_and_confirm 编写单元测试（8 个测试全通过，FR-7.1）
- [x] **T9** 实现提交三连确认函数 `submit_and_confirm`（utils.py）
- [x] **T10** 探测全部 12 个数据集（fundamental6/2、analyst4、option8/9、model16/51、news12/18、socialmedia8/12、pv1/13）
- [x] **T11** 2026-09-03 每日任务：提交 5 个新 Alpha（目标达成）
  - #17 akLqqmm6：cash/assets 趋势 + 反转 + 量价相关 dec=8
  - #18 A10MYm3d：ebit/ev 趋势 + 反转 + 量价相关 dec=8
  - #19 QP3XalpK：应计异象 + 价格趋势
  - #20 wpYgReRx：资产周转率 + 价格趋势
  - #21 MP1mQRro：应计 + 周转率 + 价格趋势（S=1.91 F=1.74）

## 进行中任务

（暂无）

## 待办任务

- [ ] **T7** 用新成功公式继续挖第 22 个+：`gr(新基本面) + gr(-ts_av_diff(close,20))` dec=8（见 pitfalls.md 新成功公式）
- [ ] **T8** 将挖掘脚本整理为可复用模块（参数化候选列表，消除硬编码）
- [ ] **T12** 每日提交任务持续：每天至少 1 个，维持 Days of Submission
- [ ] **T13** 关注 Research Consultant 权限（解锁高级数据集后重新扫描）

## 历史任务（已完成的挖掘记录）

| 日期 | Alpha ID | 表达式 | Sharpe | Fitness | 状态 |
|------|----------|--------|--------|---------|------|
| 08-15 | 58p2XdxX | liabilities/assets | 1.55 | 1.34 | ✅ ACTIVE |
| 08-27 | wpjoxbbd | group_neutralize(ts_rank(cf/ev,60),industry) dec=4 | 1.37 | 1.00 | ✅ ACTIVE |
| 08-27 | rKj7w0Z1 | group_rank(ts_rank(cf/ev,60),industry) dec=6 | 1.60 | 1.24 | ✅ ACTIVE |
| 08-30 | RR79x16n | liabilities_curr/assets | 1.47 | 1.16 | ✅ ACTIVE |
| 08-30 | 9qX8Nr6r | liabilities_curr/cap | 1.26 | 1.49 | ✅ ACTIVE |
| 08-30 | vRjG1Jzw | group_rank(ts_av_diff(cf/ev,60),industry) delay=1 | 1.79 | 1.27 | ✅ ACTIVE |
| 08-30 | QP7z069Q | signed_power(liabcurr/assets,0.5) | 1.64 | 1.38 | ✅ ACTIVE |
| 08-30 | 1YwKML56 | group_rank(ts_av_diff(cf/ev,60),industry) delay=0 | 2.21 | 1.75 | ✅ ACTIVE |
| 08-31 | 1YwRK1wW | gr(liabcurr/assets)+gr(-ts_rank(close,20)) | 2.11 | 1.31 | ✅ ACTIVE |
| 08-31 | 9qX3M2mq | gr(liabcurr/assets)+gr(-ts_rank(close,10)) | 2.49 | 1.45 | ✅ ACTIVE |
| 08-31 | kqjpepz8 | gr(liabcurr/assets)+gr(-ts_rank(close,5)) | 2.74 | 1.42 | ✅ ACTIVE |
| 09-02 | N1QxNQK7 | gr(liabcurr/cap)+gr(-ts_rank(close,5)) | 2.06 | 1.17 | ✅ ACTIVE |
| 09-02 | e79kPeEM | gr(liabcurr/assets)+gr(cf/ev趋势)+gr(-ts_rank(close,5)) | 3.02 | 1.79 | ✅ ACTIVE |
| 09-02 | qMW92Az2 | gr(liabcurr/cap)+gr(cf/ev趋势)+gr(-ts_rank(close,10)) | 2.32 | 1.60 | ✅ ACTIVE |
| 09-02 | E5v15JPJ | gr(liabcurr/assets)+gr(-ts_corr(close,volume,20)) | 1.67 | 1.14 | ✅ ACTIVE |
| 09-02 | le8ddYbe | gr(liabcurr/assets)+gr(-ts_corr)+gr(cf/ev趋势) | 2.41 | 1.87 | ✅ ACTIVE |
| **09-03** | **akLqqmm6** | **gr(cash/assets趋势)+gr(-ts_rank(close,5))+gr(-ts_corr) dec=8** | **1.71** | **1.23** | **✅ ACTIVE** |
| **09-03** | **A10MYm3d** | **gr(ebit/ev趋势)+gr(-ts_rank(close,5))+gr(-ts_corr) dec=8** | **1.90** | **1.46** | **✅ ACTIVE** |
| **09-03** | **QP3XalpK** | **gr(应计异象)+gr(-ts_av_diff(close,20)) dec=8** | **1.27** | **1.07** | **✅ ACTIVE** |
| **09-03** | **wpYgReRx** | **gr(rev/assets)+gr(-ts_av_diff(close,20)) dec=8** | **1.54** | **1.41** | **✅ ACTIVE** |
| **09-03** | **MP1mQRro** | **gr(应计)+gr(周转率)+gr(-ts_av_diff(close,20)) dec=8** | **1.91** | **1.74** | **✅ ACTIVE** |

> 09-03 详细失败记录（~130 个被拒候选）见 pitfalls.md 第七轮挖掘。

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-28 | 初始创建，整理项目结构 |
| 2026-08-30 | 更新记录：提交 3 个新 Alpha，新增待办 T6~T8 |
| 2026-09-04 | 重大更新：累计 21 个 ACTIVE；09-03 单日提交 5 个达成目标；新成功公式（价格趋势替代 rev5+corr20）；T6 完成；新增 T12/T13 |