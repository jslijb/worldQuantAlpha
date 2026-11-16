# WorldQuant Brain 项目长期记忆

> **本文件的唯一读者是"下一个会话的我"。**
> 写入标准见 §〇2。**跨阶段不自动继承**：任何"已验证配方"必须标【数据集归属 + 提交日期】。
> 规则全文在项目根 `AGENTS.md`（本文件与它冲突时，**以 AGENTS.md 原文为准**）。
> 当日数值一律写 daily log；本文件只留跨日仍成立的判据。

---

## 〇、研究顾问阶段定位与记忆准入标准

### 〇1 阶段定位（李工 11-13 19:30 确认，至今有效）
- 阶段 = **WorldQuant 研究顾问**。`GET /users/self` → `level=GOLD`、`onboarding=FORMS_APPROVED`；
  `activities` 出现 `base-payment / other-payment / referrals` ⇒ 顾问报酬项已生效。
- 顾问通道规则原文在 `docs/learn/documentation/consultant-information__getting-started-finding-consultant-alphas-read-first.md`：
  门槛 = 高 Sharpe/Fitness + **Production Correlation** + **IS Ladder Sharpe**；IS 窗口 5 年 → **10 年**；
  官方明示"USA 区域可能很难在生产相关性测试中胜出"；特赦通道 = max corr<0.7 **或** Sharpe 比每个 corr>0.7 的在产 Alpha 高 10%。
- **顾问阶段 ≠ 用户/学生阶段**：学生阶段只要 S/F 过线，研究顾问阶段多两道墙（PROD + Ladder Sharpe）。
  台账 360 条里有 346 条是学生阶段写法（混数据集），**在顾问阶段一条都不可复用**。

### 〇2 什么内容才进记忆文件（准入闸门，11-16 立）
**进 MEMORY.md 必须同时满足 4 条**，缺一条只能进 daily log：

| # | 条件 | 反例（只能进 daily log） |
|---|---|---|
| 1 | **跨日仍成立**（明天还管用） | "今天 12 条批全灭 S 0.11~0.67" → daily log |
| 2 | **有出处**（实测输出/文件原文/平台返回，三者之一） | "感觉新数据集没用" → 无出处，不进 |
| 3 | **能变成动作**（可执行的判据/阈值/红线） | "这条路可能更好" → 不可执行，不进 |
| 4 | **标了阶段与日期**（哪个阶段、哪天实测） | "group_rank 配方" → 无归属，禁用 |

**daily log 的定位**：当日流水，只追加不覆盖，**只作追溯，不是判据**。
过期日志（>30 天）蒸馏进 MEMORY.md 后删除；本项目 git 已跟踪，可 `git checkout` 恢复。
**归档文件（_archive_*.md）一律不作判据** —— 11-16 已删 614K 归档（09-05~10-10 学生阶段），git 可逐份恢复。

### 〇2b ★ VF 目标的正确含义（11-16 论坛原文验证，凌驾本文件其他条目）
- **终极目标是提升 VF，不是过门数**。论坛 VF 复盘帖 44645223044247（814 Regular + 269 Super 实测）：
  atom 比例 高 VF **81.7%** → 低 VF **50.5%**（VF 0.97→0.39）；
  「**VF 下跌不是从"某条 alpha 的 Fitness 变低"开始的，而是从"提交集合里 atom 变少"开始的**」。
- **平台自己的 Genius 六维 Tie-Breaker 就按这个设计**（主帖 44770798147735 原文）：
  「每条 Alpha 平均使用的不同字段数（Avg distinct Fields / Alpha）**越低越好**（单字段 ATOM 可压到 1），
  而全季度总计使用的不同字段数（Total distinct Fields）**越高越好**」。
- **多样性 = 一批 alpha 里各数据集使用次数均衡**（批次层面），
  **不是**"一个 alpha 里用多种数据集"（那是 ATOM 禁止的混血）⇒ ATOM 与多样性**同向不冲突**。
- **量价 ATOM = 平台会收、VF 会降**（占满最拥挤格子：量价 4 字段占台账引用 25.4%；存量池 360 条
  已提交，其中 45 条 SELF≥0.70、25 条 ≥0.80）。**终极目标是 VF，不是过门数。**
- **我们台账的账（360 条实测）**：atom 比例 2.8%（9月0.7%/10月0.6%）｜每条平均 7.73 字段（≤2 仅 3.9%）
  ｜字段池 252/4375｜Top8 字段占引用 50.1%｜`group_rank` 1926 次 ⇒ **全部与 VF 方向相反**。
- **代码级执行**：`_grid/diversity.py:gate_vf()` 门7(单alpha字段数≤2)/门8(每批≥2新字段)/门9(atom占比≥50%)，
  接入 `_autologs/sim_run.py`（不合规 exit 6）。

### 〇2c ★ 正确方向：单字段 + 反复变换 + 横截面排序（受控实验证实）
- 形态实验（option9，同字段同设置，只改形态）：`group_rank(ts_av_diff(oi_10,20)-ts_av_diff(oi_360,60),subindustry)` **S0.86**
  ｜group_scale(比值) 0.50 ｜group_rank(ts_zscore(比值)) 0.43 ｜group_rank(比值) 0.42 ｜group_zscore(比值) 0.32
  ｜**只有比值无差分 S−0.09**。
- ⇒ **必须有"差分"（时序变化）；时序归一化不是压制源；换 idea（期限差 vs 比值）S 从 0.42→0.86，
  换算子只在 0.32~0.50 摆动 ⇒ 算子+参数是"训练调参"，idea 决定信号。**
- ⇒ **不是"更多字段"，是"单字段 + 反复变换 + 横截面排序"**（论坛主帖 4 条单字段模板同特征）。
- **深浅对照（12 条，同字段同设置只改深度）**：option9 −0.01｜social12 +0.21｜mmp −0.51｜anlrev +0.40
  ｜aieq +0.23｜model109 −0.61 ⇒ **3 涨 3 跌，"挖深"本身不产生 alpha**。

### 〇3 事实条款（李工 11-15 17:01，置顶，凌驾本文件其他一切条目）
**所有回答必须基于事实，不得自编。**
- 数字/条数/比例/指标/日期/平台返回，写出来必须有出处：本次命令真实输出 / 文件原文 / 平台 API 返回。
  三者都没有 → 写"未核实/不知道"，**不许给一个看起来合理的数**。
- 汇总行必须从明细逐行数出来，不许脑补（0922 栽过"7/2/2"）。
- 引用项目规则前先 grep 原文，不凭记忆复述。
- 说"跑过了/通了"必须能指出日志文件与其中的关键返回；没有日志就是没跑过。
- 承认"我错了"要写进文档并改代码，不能只在对话里道歉。

### 〇4 研究顾问方法论四原则（李工 11-14 总结，最高优先）
1. **Alpha atom 类型分散**（量价/基本面/分析师/事件/情绪都铺）。
2. **数据集分散**——每日新数据集/新字段开荒，不死磕老集。
3. **算子分散——由机器强制，不靠自觉**：`group_rank` 11-15 起禁 10 天（`_grid/op_ban.py` 代码级拦截）；
   外壳轮换 `_grid/transforms.py`（13 族）；批次多样性 `_grid/diversity.py` 硬门。
   **已实证换外壳只重掷 corr、几乎不抬 S**（同核三壳 2.29/2.28/2.27）⇒ 真多样性必须落在数据集与 idea 上。
4. **idea 来源优先级**：李工灵感 > 论文 > 开源社区 > 互联网；只有①②挖不到才轮③④。
   李工的灵感与论文不可能挖不到——挖不到先反思代码层（字段/算子/参数/实现），**不得判 idea 死刑**。

---

## 一、纪律（最高优先）

- ★★★ **每日配额唯一口径（11-15 李工二次纠正，覆盖一切旧说法）：4 条常规 REGULAR + 1 条超级 SUPER**
  （依据 AGENTS.md §1 原文）。**"每日 6 条"作废**——那是我的错误口头记忆，任何场合不得再出现。
  代码默认提交上限必须是 4（regular），SUPER 另 1（`SUPER_ALPHA_SUBMISSION_LIMIT=1`，`src/core/knowledge.py:77`）。
- **每日配额上限制**：当天有多少做多少，**不设历史欠账、不跨日顺延、不追补**。
  每轮汇报必含：提交 id+指标 / 台账总数（唯一 id 口径）/ 当日美东计数；**入池才算数**。
- **算子硬禁令（11-15 12:55 李工令）**：`group_rank` 2026-11-15~11-24 全面禁用，代码级拦截在 `_grid/op_ban.py`，
  不得绕过、不得改阈值。替代池见 `_grid/transforms.py`。
- **多样性硬门（11-15 13:02 李工令）**：提交模拟前必过 `_grid/diversity.py` 的 gate。
  ⚠ **11-16 复核：这道门有致命缺口——`idea` 维度是用 cid 前缀凑的**（`parse_alpha` 里 `idea = cid.split('_')[0]`），
  台账 212 种 batch 前缀 ⇒ 实际几乎不设限；且 `DIMS` **没有 field 维度、没有骨架维度**。
  ⇒ 门形同虚设，是"旧骨架照抄不报错"的根因。修法见 §十。
- **质量门（11-12 划代，旧自设门全部作废）**：唯一门 = 平台门（F≥1.0 / TO≤70% / 无任何 FAIL /
  SELF≤0.70 / PROD≤0.70）；S 无下限，4.2/1.58/0.65 等旧闸不得再用于拦截。
  提交通道：本地模拟 → PROD/SELF 预检（≤0.69 留缓冲）→ POST。

### ★★★ 11-16 低 S 归因（三条实测，判死"字段不行"这个借口）
李工问"S 低你想过是为什么？idea 没问题就是用错数据/算子？"——用 11-15 已模拟 95 件逐条实测回答：
1. **S 低 = 形态/idea 层做错，不是数据层。** 同一字段 `beta_prediction_dispersion`、同一 idea 族，
   只换模板，S 从 **−0.26 到 +1.12**（摆幅 1.38）；option9 同数据集不同 idea，S 从 **−0.60 到 +1.45**。
   ⇒ **同一批数据、同一批字段，形态排位决定生死。禁止再用"字段不行/数据冷门"解释低 S。**
2. **S 与"能不能进池"是两个独立闸门。** `SUBMIT_VERDICTS.csv` 250 条真实判决：157 ACCEPTED /
   93 REJECTED，**93 条里 92 条 failChecks 唯一 = SELF_CORRELATION，LOW_FITNESS 出现 0 次**；
   ACCEPTED 且在台账的 157 条 S 最低 **1.410**、中位 2.320、最高 3.390（S<1.0 的 0 条）。
   ⇒ **历史上凡死掉的都死在相关性，没有一条死在 S/F。** 我说的"S 低导致提交不了"不成立——
   S 低的件是在**本地预筛**就被拦了，从未走到 POST。
3. **"相关性高是正常的"是现状不是出路。** 台账 320 条 SELF 中位 0.6467，**0.50~0.70 占 82.5%**
   （正是论坛说的"SC 0.7 是平台让你交的线、不是 VF 愿意给你分的线"的打折区），
   ≥0.70 有 45 条、≥0.80 有 25 条。论坛 Pyramid 帖给出两条**独立**杠杆：
   降 PROD → 去冷门数据集（"Lower alpha count usually means an easier prod corr"）；
   降 SELF → 换 idea/形态。
- challenge 无结束日期（perpetual）；isScore 是合并池动态重算的"表现分"非累计积分，
  低 F/高 selfCorr 提交会稀释分数（0926 净 −177 实证）。对账锚点 `_autologs/_isscore_history.csv`。
  ⚠ 11-16 取数断链：`/competitions/challenge` Not found、`/users/self/score` 404 ⇒ isScore/rank 暂无 API 通道。

## 二、平台硬边界与顾问专属门槛

- FAIL 6 种：LOW_FITNESS / LOW_SHARPE / LOW_SUB_UNIVERSE_SHARPE / CONCENTRATED_WEIGHT / HIGH_TURNOVER / LOW_TURNOVER。
- 平台线 F≥1.0 / TO≤70% / 无 tS 检查；带任何 FAIL 不交。常规提交 S≥1.58 / F≥1.0 / 2Y≥1.58。
- **GLB 附加**：AMER / EMEA / APAC 各 ≥1.0（当前短板分区 = EMEA）。**CHN**：S≥2.07 + LOW_ROBUST_UNIVERSE_SHARPE（0.4×S）。
- **高 S 特赦**：仅对稀疏区有效（KPgepR9k S7.54/PROD0.788 PASS；WjlK1b2k S8.26/PROD0.8856 **被拒**）。
  ⇒ **S 高不保 PROD**，0.82+ 密集区必死。
- **判据链只有一条**：`POST /alphas/{id}/submit` → 轮询 `GET /submit`，403 body 的 checks 是唯一真值。
  GET /check 空 body ≠ PASS；落盘 `is.checks` 里基础项不达标标 **WARNING**（提交时按 FAIL 拒），**勿当合格**。
- **CLUSTER_TEST=ERROR/WARNING 不拦截**（11-16 实测 5 条 ERROR + 4 条 WARNING 照常入池）⇒ 只有 `result==FAIL` 才算数。

## 三、相关性墙（唯一出量通道）

- ★ 相关性判死**只认平台返回值**。本地换算系数、cmax≤0.65 等旧口径已作废，仅存档。
  ⚠ `fast_corr.py` 有 bug 不可信；提交前用 **GET /correlations/prod 与 /self 免费预检**（实测 12 条对账 EXACT delta=0），≤0.69 放行。
- ★ `GET /alphas/{id}/check`：未提交 alpha 即返平台 SELF_CORRELATION，**不耗提交配额**；
  首调常空 body，轮询 1~2 轮出值；**只有 result==FAIL 才算 FAIL**（每条恒有 1 个 SELF_CORRELATION=PENDING）。
- 豁免路线实测不可靠（blblxz5M 超 need 仍被拒），不得当常态；平台硬阈值 0.7。
- 每次入池后 corr 地貌全变（JjQPJPLA 0.6875→0.9991），历史判决作废；`corr_predict.py` 每次现算，无需清缓存。
- **低 corr 与高 tS 结构性冲突**：f2 无人区最低 corr 料 tS 仅 0.04~0.18。
- 存量池真值 = **360 条**（台账行数 = 平台 OS stage count，AGENTS.md §勘误已对平）。
  ⚠ **11-16 勘误**：此前记的"存量池 445 条全死、平台 corr 最低 0.7754"**两个数都错**——
  445 出自 `_autologs/_plat_check.txt` 的"待测445 条"（待测候选数，非存量池）；
  0.7754 是 `_corr_model2.txt` 里 55 对样本的**下界**，不是全池最低（台账实有 45 条 ≥0.70）。
- 工具：`corr_predict.py`（**提交前必跑**）/ `plat_sweep.py` / `corr_poll.py` / `corr_pair.py`+`corr_model2.py`。
- ★ **`_grid/corr_gate.py` 是当前唯一的"机制去重"有效判据**（取代 `mech_gate.py`，见 §十）。

## 四、ATOM 红线（平台硬规则，违反=追责）

- **ATOM = 单数据集**：整条表达式只用一个 dataset 的字段，外加 6 个豁免分组字段
  （country/exchange/market/sector/industry/subindustry）。
  - 提交前必过 `src.core.atom.judge()`，返回 False 一律不得 POST（AGENTS.md §1）。
  - 字段归属以平台 `/data-fields` 的 `dataset.id` 为准；归属不明先查 API 再判。
  - GLB 易混：`tm_*`=`techindi_model`、`tcm_*`=`tech_chart_model`，跨用即破坏 ATOM。
  - **SUPER Alpha 不受 ATOM 约束**（是已提交 Alpha 的组合）。
- **混数据的代价**（论坛 `docs/forum/atom_pack/` 原文）：Pyramid 倍率按最低者结算；混 3 类及以上计 0。
  VF 复盘帖实测：atom 比例 81.7%→50.5% 时 VF 从 0.97 掉到 0.39。
- **隐式破 ATOM 三坑**：`convert()`/`inst_pnl()` 底层引 pv1；`cap/close/returns/vwap` 属 pv1，
  拿来 bucket 或 vector_neut 即破功。同数据集内分桶要用**本数据集自己的市值字段**。
- ⚠ **平台标签只证明"没混数据集"，不证明"没用 pv1"**（踩坑 E-12）：11-15 四条 `classifications` 全含
  `DATA_USAGE:SINGLE_DATA_SET`，但全是 pv1 一个字段。⇒ **ATOM 合规 ≠ 有多样性**，这两件事要分开看。
- **台账 60 条抽查：带 ATOM 分类 0 条** —— 存量全是混合写法，别再从老台账拉"强引擎"当料（E-09）。

## 五、已验证的"能过门"样本（活样板，只有 5 条非 pv1 单数据集）

| id | 数据集 | S / F / TO | 机制 | 日期 |
|---|---|---|---|---|
| `QPK3n9Zw` | option8 | 2.20 / 2.36 / 0.05 | call-put 波动率偏斜 + 期限结构（比值 & 期限差） | 10/07 |
| `1YwKML56` | fundamental23 | 2.21 / 1.75 | 现金流/估值比值 | 08/27~29 |
| `d5al5ljw` | pv1 | 2.51 / 1.74 | GLB 波动/动量双腿（industry 组） | 11/15 |
| `LLKlxA7m` | pv1 | 2.51 / 1.85 | 同上（sector 组） | 11/15 |
| `YPaWd16q` | pv1 | 2.50 / 1.73 | 同上（exchange 组） | 11/15 |
| `WjlWKLPj` | pv1 | 2.85 / 2.01 | 同上（sector+country 交叉组，最强件） | 11/15 |

**共同点**：都是**同族字段做比值/期限差/双腿对冲**，不是字段堆砌。
**对照反例**：11-15 那 12 条新数据集 ATOM 批（S −0.40~0.67 全灭）= 三个**互不相关**字段
zscore/rank 等权相加 ⇒ 字段堆砌 = 噪声。

> ★ **判据：每条候选必须能用一句话说清"在赌什么"。说不清机制 = 噪声，不许进批。
> 多样化从来不是不能提交，不能提交的是"没有 idea 的多样化"。**

## 六、机制去重：唯一有效的判据是 PnL，不是字段

- ★ **`mech_gate.py` 的字段 Jaccard 判据已被实测推翻**（11-15 21:3x，`_grid/replay_corr.py`，341 条真实 PnL）：
  - 字段同源 20 条：两两 PnL corr 中位 **0.2718**，组合 Sharpe **4.176**
  - 字段跨源 20 条：两两 PnL corr 中位 **0.3309**，组合 Sharpe **3.747**
  - ⇒ 字段同源反而更分散；"字段跨源"策略组合 Sharpe 五组最差（3.494 < 随机 4.090）。
  - **字段集合不是 PnL 相关的代理** ⇒ 判重必须直接看 PnL。
- ⇒ **`_grid/corr_gate.py` 取代 `mech_gate.py`**：等权加入第 N 条后组合 Sharpe 不降的充要条件
  `rho < b/a + (b²−a²)/(2a²)·(w/(1−w))·(σb/σa)`，w 很小时退化为 `rho* = b/a`；
  实测 400 对真实 PnL，门槛预测 ΔS 符号一致率 **100%**。
  ⚠ **`corr_gate.py` 目前只做事后解释，没接进提交通道**（`now_submit.py` 只查平台 prod/self）。
- **`mech_gate.py` 保留用途**：只做"字段重复度粗筛"，帮人看像不像旧件，**不得用它放行或拦截**。

## 七、池内同质度（11-16 全量实测，非估计）

台账 360 条，`src/core.atom.judge()` + `fields_of()` 逐条解析：

| 指标 | 实测值 |
|---|---|
| 不同算子骨架签名 | **256 个**（Top 骨架最多 8 条；Top12 骨架合计约 71 条 ≈ 19.7%） |
| 不同字段集合 | **345 个** |
| 用过的不同字段 | **258 个 / 平台可用 4375 = 5.9%** |
| 字段引用总次 | 3181 次；**Top8 字段占 50.1%** |
| 引用最多字段 | assets 317(10.0%) / subindustry 281(8.8%) / close 245(7.7%) / returns 192(6.0%) / volume 175(5.5%) / cashflow_op 170(5.3%) / enterprise_value 113(3.6%) / cash 101(3.2%) |
| 字段对 Top3 | assets+cash 50 条 / assets+annual_intangible 39 条 / assets+cap 37 条 |
| 数据集组合 Top1 | fundamental23+fundamental6+pv1 = **98 条（27.2%）** |
| pairwise corr 中位 | 0.358 ⇒ n_eff≈2.7 |

**GLB pv1 字段池只有 9 个**（adjfactor/adv20/cap/close/country/currency/cusip/dividend/exchange），
台账已用 close 245 次、cap 95 次，未用过的仅 4 个
⇒ **GLB 量价这条路在字段层面已经走到头**，不是"再换几个分组参数"能救的。

## 八、Universe / 市场 / 权限

- 可用（11-14/11-15 实测）：USA(TOP3000/TOP1000/TOP500) / GLB(MINVOL1M/TOP3000) / EUR(TOP2500) /
  ASI(MINVOL1M) / CHN(TOP2000U) / JPN(TOP1600/TOP800)。
  摘除：KOR / TWN / ASI TOP1500(E-06) / EUR MINVOL1M(E-07) / CHN TOP2000 & COUNTRY 中性化(E-07)。
- TOP2000 死；TOP1000 有效(F 掉 1.2~1.65)；**TOP3000→TOP500 是唯一实测能独立降 corr 的杠杆**
  （0.6081→0.4944，tS 1.64→2.03），代价 SF→2.94。一池一家族只吃一口。
- **EUR 裸原子可用**：`-ts_rank(close/open-1,20)` 四外壳零 FAIL、S2.05~2.11。
- 14 数据集 4375 字段（fundamental2=766 未开荒）。字段归属 **region 相关**（见 §十 bug）。

## 九、算子与字段边界

- 平台无权限/不可用：`ts_skewness/kurtosis/co_skewness/co_kurtosis/moment/entropy/median/returns/theilsen/
  triple_corr/min/max`、`regression_neut/vector_neut/floor/tanh/sigmoid/s_log_1p/ts_decay_exp_window/ts_median/scale_down`；
  `arc_tan` 不可用；期权快照 event 字段 FASTEXPR 不支持。
- 残差显式 `y − ts_regression(y,x,d,rettype=3)`。向量字段须 `vec_avg/vec_sum`。算子上限 64。
- **`? : NaN` 是 CONCENTRATED_WEIGHT 头号成因 → 一律用 `if_else`**。
- 拥挤腿：CASH45/CFEV45/PV/TXTUB/XRENT/PTPR。
- **group_rank 翻符号陷阱**：`group_rank(-x,g)` ≠ `-group_rank(x,g)`（rank 输出恒为正均匀分布）。
  正确翻法 = 负号放 group_rank 整体外面。
- **CHN TOP2000U STATISTICAL 符号不对称（判死）**：`group_rank(ts_delta(returns,5),subindustry)` S −7.33，
  整体取负只回 +0.4 ⇒ 负 S 巨信号在 CHN STATISTICAL 不可靠。

## 十、已知 BUG 与门的缺口（11-16 实测，**待修**）

| # | 问题 | 证据 | 修法 |
|---|---|---|---|
| B1 | **`atom.py` 字段映射跨市场串味**：`setdefault` 把 USA/EUR/GLB 各市场缓存合并成一锅 | `cashflow_op` USA=fundamental6 / EUR=fundamental23（平台 `/data-fields` 实测） | 字段映射按 region 分桶 |
| B2 | **`diversity.py` 的 `idea` 维度是 cid 前缀凑的** | `parse_alpha` 里 `idea = cid.split('_')[0]`；台账 212 种 batch 前缀 | idea 改为**显式 `idea_id` 字段**，缺失即拒 |
| B3 | **`DIMS` 缺 field 与骨架维度** | `DIMS = (dataset, idea, operator, universe, neutralization, decay, truncation)` | 加 `field` + `skeleton` 两维 |
| B4 | **`corr_gate.py` 没接进提交通道** | `now_submit.py` 头部自述"不走本地 corr_gate 先行" | 提交前必跑 corr_gate 判重 |
| B5 | **无"新字段"检查** | 258/4375 = 5.9% 字段池 | 每批至少 N 个台账未用过的字段 |

## 十一、工具与工程坑

- 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`：**唯一事实源**，只追加，utf-8-sig，id 第 0 列。
  核对口径：OS count vs 台账行数差 1 → 先查最新 SUPER 是否漏记。
- **批次唯一生产入口 = `_grid/batch_gen.py`**（11-15 建）：只许给【内核+外壳族名】，机器拼装+校验+直方图，
  人不许直接手写完整表达式（手打必然回到肌肉记忆=group_rank）。硬约束 4 条：单数据集 / 算子禁用 /
  ≥min_shells 外壳覆盖 / 算子直方图最大占比>50% 拒绝产出。
- `sim_run.py`（`_autologs/`）：通用模拟器，吃 JSON[{cid,code}]，落 `data/alpha_quality_analysis/mined/<cid>.json`。
  ⚠ 端点 POST /simulations（非 /alphas）；payload `regular` 必须字符串；settings 照抄 `mined/le8T2_t0.05_03.json`；
  **并发上限 conc=2~3**；单条可 >15 分钟，必须后台跑。
- 后台必须 `run_in_background=true`（nohup 不保活）；长批次 > log 2>&1；Retry-After 退避 min(ra,15~20)；认证带重试。
- `/alphas/{id}/correlations/self` 不可用(200 空body)，corr 自己拉 PnL 算；PnL 缓存 `pnl/*.json`；新模拟延迟数分钟，空判 sleep 重跑。
- **OLD_SIMULATION 只认当天模拟**：存量 16066 条 mined 里只有当天 87 条可用。
- Python 统一 bigmodel env：`D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（系统 python 无 requests）。
- 工具：`judge_now / pair_now / screen_pool_corr / find_passers / near_miss / axis_surgery / diverse_pick /
  smallpool_now / tab / dump_set / corr_gate / mech_gate(仅粗筛) / replay_corr / replay_vf / replay_ds`。
- 外部素材：`EXTERNAL_SOURCES.md`(EX-NNN 登记)、`idea_atoms.md`、`idea.md`(原子库+组合登记簿)、`atoms.md`(踩坑明细)。
  论坛镜像 `http://61.182.4.91:8765/wiki/`(408 帖)。发批前必查 `idea.md` + `atoms.md`。
- 未碰可试方向：隔夜/日内拆分⭐(裸信号弱只配配腿)、JACKPOT、GTS、BAB、非线性因子、企业生命周期、
  盈利不确定性、商誉/过度自信、员工信息分散。

## 十二、备考与顾问事务

- 顾问通道：10000 分 → 笔试 ✓ → 面试中；Super Alpha 已解锁(OS>100)。
- 备考 28 份 `docs/exam`、`docs/study`；缺口"能背≠能讲"。
- 顾问日配额 = 首 4 常规 + 1 超级（**上限非任务量**）；日酬 = f(Quality+Quantity, SelfGrowth, Value)，
  **Value 惩罚与已有池相关性相关** ⇒ 质量 + 低 corr 是杠杆。
- 每周自检（周一 09:00 自动化）：复盘全部已提交 Alpha（成功共性/失败模式/优化措施/VF 提速），
  报告落 `docs/research/weekly_alpha_review_*.md`，验证过的经验回写 AGENTS.md 与 idea.md。
