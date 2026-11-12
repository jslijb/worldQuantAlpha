# 支持论坛镜像地图（2026-10-08 建档）

> 通道：`http://61.182.4.91:8765/wiki/`（第三方镜像，全站 22179 文档，其中 support 论坛帖子 408 篇全文 markdown）。
> 抓取模板：`http://61.182.4.91:8765/wiki/view?path=raw/articles/worldquant-brain-support-forum/raw/{post_id}-{slug}.md`
> 纪律（李工 1008 定）：**不搬全站，只按地图逐篇批、逐篇抓、逐篇消化**（EXTERNAL_SOURCES.md 流水线）。
> 清单全文：`_autologs/forum_mirror_post_list.txt`（408 行，id+slug 原样，抓哪篇拼哪个）。

## 一、镜像站资产盘点

| 资产 | 数量 | 说明 |
|---|---|---|
| support 论坛帖子全文 | **408 篇** | 官方 BrainTips 57 + 灵感启示录子帖 20 + SuperAlpha 2 + 顾问 24 + 讨论/问答 305 |
| concepts/external-research 笔记 | ~1000 篇 | 别人整理的研究笔记库（未盘点，先不碰） |
| 【Alpha灵感启示录】主帖 19273239621399 | 138 条子帖目录 | 见第三节 |

## 二、优先抓取清单（1008 已全部抓完消化，正文存 `_autologs/ex_*.txt`）

> **消化结果（1008，登记 EX-009~018）**：10 篇全清。**A 类 3 篇**（EX-011 线性组合三宗罪→同尺度判据生效；EX-015 自定义/双重中性化→新 corr 轴待实证；EX-016 regression_neut 反转正交化手术→待实证；另 EX-017 字段体检六探针模板已生效）；B 类 4 篇（EX-010 等价替换顺序、EX-014 ts_mean/ts_decay_exp_window 平滑、EX-018 关系数据、EX-013 对照零增量）；D 灌水 3 篇（EX-009 提问帖、EX-012 GPT 教程已覆盖）。
> **EX-006（25830696529815"对于alpha的骨干重要讨论"）不在镜像**：408 篇清单无此 id（快照 2026-08-15，帖更新），直拼 slug 404——仍缺正文，等李工贴。

### P0 · 直击相关性墙与产线结构
| # | post_id | 标题 | 为什么是它 |
|---|---|---|---|
| 1 | 19609241215511 | Reducing production correlation without reducing Sharpe or Fitness much | **我们唯一出量瓶颈就是 corr 墙**，官方口径对照我方五配方 |
| 2 | 8046468280727 | Brain Tips: how do you reduce correlation of a good alpha | 同上，官方技巧清单 |
| 3 | 15238236356375 | Why is linear combination of expressions in one alpha not recommended | **我方产线全是加权多腿组合**——官方说"不推荐"的理由必须搞清（过闸风险/OS 隐患） |
| 4 | 20457074342807 | Generate insights from a research paper using GPT | 李工 idea 原子化思路的官方版，直接并进 idea_atoms.md 流程 |

### P1 · 优化杠杆（提 S / 压 TO / 中性化）
| # | post_id | 标题 | 用途 |
|---|---|---|---|
| 5 | 8833033953559 | 5 ways to potentially increase returns of an alpha | S 杠杆对照 |
| 6 | 14588500172567 | Improve your alphas with signal smoothing | TO 杠杆（我方 decay 跷跷板经验对照） |
| 7 | 13914677572887 | Improve your alphas with custom neutralization | 自定义中性化（我方只试过 MARKET/SECTOR/INDUSTRY/SUBINDUSTRY） |
| 8 | 9672576065943 | How does regression_neut work | **我方"风险中性化"曾判死——对照官方文复核判死依据** |

### P2 · 新数据集开荒准备（下一步换池弹药）
| # | post_id | 标题 | 用途 |
|---|---|---|---|
| 9 | 11807866133911 | 6 ways to quickly evaluate a new dataset | fundamental2/option9/news18 开荒方法论 |
| 10 | 14264016776087 | Using relationship data for equity | **关系型数据我方 14 数据集清单里没碰过** |

## 三、【Alpha灵感启示录】主帖 138 条子帖 · 方向分类（原文目录已存 `_autologs/forum_mirror_19273239621399.txt`）

### 3.1 我方可直接对照消化（USA-D1 范围、未判死）
| 方向 | 子帖（主帖行号） | 状态 |
|---|---|---|
| **隔夜/日内拆分**（⭐密集推荐区） | Overnight returns daytime reversals(123) / 隔夜拉锯战渔利因子⭐(124) / 隔夜与日内拉锯战暗藏的信息(144,165) / 日内对隔夜的过度反应(157) | **未碰**。open/close/vwap 可拼隔夜收益，与反转骨架不同源 |
| **JACKPOT / 博彩偏好** | JACKPOT因子(132) | 未碰 |
| **GTS Factor** | GTS Factor(159) | 未碰 |
| **Betting Against Beta** | Betting Against Beta(155) | 未碰（低 beta 组合，需 beta 字段核对） |
| **非线性因子收益** | Non-Linear Factor Returns in US Equity(133) | 未碰 |
| **企业生命周期/预期误差** | 企业生命周期、预期误差与未来股票收益(146,149) | 未碰 |
| **盈利不确定性+关注度** | 盈利不确定性和公司关注度(134) | 未碰 |
| **商誉/过度自信** | 商誉、过度自信与股票回报(153) | 未碰（需商誉字段，fnd6 待核） |
| **员工信息分散** | 员工间的信息分散与股票回报率(114) | 未碰（需内部人数据） |
| **质量/估值框架** | 基于 return 的公司质量测度(106) / 企业倍数新证据(122) / 高估值与融资决策(143) | 未碰（小心与我方质量族同源毒化） |

### 3.2 已榨干/已判死（跳过，别再烧模拟）
| 方向 | 子帖 | 判死依据 |
|---|---|---|
| 期权族 8 篇 | IV spread(113,127,131,148) / smirk(119,158) / 期权需求(26,102,145) / 期限结构 | option8 S 天花板 2.24 已榨干，两口已吃（6XKr8RwG/QPK3n9Zw） |
| 新闻情绪 5 篇 | News Momentum(105) / 新闻动量反转(111) / Slowly Incorporated News(115) / Brain Tips 新闻优化(23,142) | news 事件结构组死 S≤0.96（EX-004 实证） |
| 应计+现金流 | 回到基本面应计倒U(21,135) | **配方六已吃**（-(ebit-cashflow_op)/assets 主腿，家族 corr 最低但同族互毒 0.95+） |
| 分析师部分 | 分析师建议和回报率(100) / Are Analyst Short-Term Trade Ideas Valuable(156) | anl4 修正动量弱判死；EX-003 已消化同类 |
| 换手率家族 | 500日换手率半方差(30,169) / UTR(17,53) / tps_turbo(20,82) | 换手率=毒药主题（工作记忆§13） |

### 3.3 无权限区域（不碰）
- CHN 全组（34~95 行，~60 条）：我方仅 USA 区域
- ASI-D1 / GLB / KOR-D1（166~181）：无权限
- Super Alpha 组（182~187）：consultant 403
- 🔒 顾问专属标注的子帖：等顾问权限

### 3.4 General 总结 4 篇（方法论富矿，后续按需）
- 从价量看技术指标总结(189) / 流行基本面指标汇总(190) / 市场异常总结(191) / 投资因素总结(192)
- **193 行"对于alpha的骨干重要讨论" = EX-006（李工 1007 发的那篇）**——现在知道它在主帖 General 组里，镜像可抓

## 四、使用纪律

1. **抓一篇消化一篇**：走 EXTERNAL_SOURCES.md 流水线（登记 EX-NNN → 分类 → A 类四步实证 → 回写原子库），消化完才准抓下一篇。
2. 本地图只维护状态，不存正文；正文抓下来存 `docs/external/EX-NNN_<短名>.md`。
3. 镜像站是第三方私货（61.182.4.91，scraped 2026-08-15），**内容可能与 forum 现版有出入**，关键表达式必须回平台实测，不认镜像原文为真。
4. 408 篇全清单在 `_autologs/forum_mirror_post_list.txt`，李工随时点名抓哪篇。
