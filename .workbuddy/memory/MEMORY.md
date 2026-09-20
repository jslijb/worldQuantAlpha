# WorldQuant Brain 项目长期记忆

> 只记**长期有效**的口径与结论。平台硬约束、目录结构、接口坑、常用命令 **以根目录 `CLAUDE.md` 为准**——动手前先读它。
> 当日数值 / 进度 / 欠账写 `.workbuddy/memory/YYYY-MM-DD.md`。

## 范围与角色
- 本工作区**只做 WorldQuant**；AI Agent 那摊（金融智能体平台 / chat_bi / rag_pdf）属别的项目。助手名「阿衡」，称呼「李工」。
- **考试红线**：考核进行中不提供答案（含限次数的准入/入驻测评；"开卷"与"对方未禁用 AI"均不改变判断）。只做考后复盘、考前陪练。不评判用户、不贴标签。
- 交付条款写明"禁止 AI / 禁止合成数据"的活：**判断做，代写·造数不做**。前后不一致算自己的账，不拿旧例当理由。

## ⭐ 执行纪律（李工 0916 定，永久有效）
- **目标定下就要完成；完成不了给根因和补救，不是道歉。**
- **缺资源、缺灵感 → 直接开口要**。
- **不能一直欠账、不能说"明天就干"**。
- **挖到就提交**。"不越级"约束已作废（"越级"仅指别瞎刷接口）。
- **每轮汇报必含**：本轮提交数、台账总数、当日（美东）计数、剩余欠账。跑得久不算功劳，入池数才算。
- **质量闸门只升不降**：S+F ≥ 4.0 + tS ≥ 1.25 + 无 FAIL。

## 口径
- 每日 5 个高质量是**下限不是上限**；不删除已提交的；欠账顺延（当日目标 = 5 + 历史欠账）。
- **高质量** = S+F ≥ 4.0 + tS ≥ 1.25 + corr < 0.7 或豁免（豁免线 = 1.10 × max(该候选自己 corr≥0.7 的对手 S)，**随候选而变**）。
- **台账** `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` 是唯一事实源（S=`row[2]`、F=`row[3]`），只追加。累计满 100 → 启动 Super Alpha。**计数口径 = 唯一 id 数**（0919 实证：YP57jVzo 曾重复记账 2 行，平台核实仅提交一次，已追加更正行）。0920 起有效提交 **87**（zq8jl99K 入池），Super Alpha 差 13。
- **美东口径**：北京 12:00 = 美东 00:00；dateSubmitted 自带 -04:00。
- **算子权限坑（0920 实测）**：本账号 **`ts_min`/`ts_max` 不可用**（报 inaccessible operator）——区间极值条件用 `close/ts_delay(close,N)-1` 替代；`hump(x,0.01)` 两参也报错（只收 1 参）。

## 提交判决机制（0916 定案，取代"排队积压"叙事）
- 判决 **4~9 秒就出**。`POST /alphas/{id}/submit` → 轮询同端点：`403 + is.checks` = 判决书；alpha 变 ACTIVE = 入池。
- **三种"假判决"都踩过**：① 旧 `blind_submit.py` 只认顶层 status/stage → 判决被当空数据丢弃（"假 PENDING"两天）；② `SELF_CORRELATION=PENDING` 是未提交 alpha 的默认占位符；③ **403 回执带 PASS 与数值却无 FAIL → 是"都过"的回执，不是拒信**（QPbP6aRQ 因此被误记 REJECTED，实际已入池）。
  → **唯一判据：出现 `FAIL` 才是拒信**。提交器 `src/submit/submit_v3.py`（已修）。
- **⛔ `correlations/self` 端点弃用**。判决书 `is.selfCorrelated.records` 自带对手明细（id/corr/sharpe）→ **提交即测量**。

## 相关性墙（真正的瓶颈）
- **墙是自己砌的**：瓶颈是候选池自身同质，不是外部竞争。池内 assets 97% / close 97% / volume 83% 共享，SUBINDUSTRY 93% → corr 天然 0.74~0.93。
- **★ 杠杆优先级**：**缩放基准（/cap vs /assets）> 分组（subindustry / industry / 分桶）> 锚选择**。**换锚基本无效**——`/cap` 把锚归一成同一个"市值"因子（batch155：换 4 个全新 fnd6 字段仍 0.78）。
- **★ 引擎腿 = 质量引擎 = 相关性来源，同一条腿**：加回 `ts_av_diff(cash/x,45)`+`ts_av_diff(cashflow_op/x,45)` → SF 3.85→4.30 但 corr 0.6999→0.961；去掉 → corr 降、SF 掉到 3.38~3.50。
- **相关是动态的**：同一表达式曾从 0.616 → 0.9879，只因中途提交了相似因子。**提交后必须对剩余池重新预检**，同构候选严禁扎堆。
- **⚠️ auto_submit_passers 重算盲区（0920 实测）**：刚提交的 alpha PnL recordset 未发布、进不了重算池 → **同批同骨架兄弟本地 corr 虚低、本地放行、平台 403 拦截**（判决书 selfCorrelated.records 自带对手）。对策：一条提交成功 → 同批同骨架候选全部冻结，次日换新锚组骨架再挂事件腿。submit_v3 的 POST-403 分支只打 300 字符就退出且不落档，用 `_autologs/full_verdict.py` 重取全文后手工补 SUBMIT_VERDICTS.csv。
- **★ 两个本地工具把筛选成本打到零**（0916）：
  - `src/analysis/pnl_corr.py`：用 `/alphas/{id}/recordsets/pnl`（**累计，必须先差分**）本地算 self-corr，不提交不污染池。与平台误差 **±0.02**（平台 ≈ 本地 +0.006~+0.017）→ **直通留缓冲：本地 ≤ 0.685**。
  - `src/analysis/leg_lab.py`：腿库离线拼装（PnL 对腿近似线性），任意权重组合离线算 S 与 corr。
  - ⚠️ 池子**只能取自台账**，不得取自 `pnl/` 缓存（混入未提交候选会把 corr 虚高压死）。
  - ⚠️ **leg_lab 系统性低估 maxcorr +0.05~+0.19（均值 +0.12）**（预测 PnL vs 实测 PnL corr 仅 0.83~0.96）→ 搜索阈值压到 `--max-corr 0.55~0.57`，**实跑后必须 `pnl_corr.py` 复核才提交**。它是候选生成器，不是判决器。
- **腿库饱和（0916 晚）**：池子到 70 条后，「L 锚 + P 价量腿」里 `max corr ≤0.50 且 S≥2.25` 只剩 **5 个**（≤0.66 时曾 777k 个）。
- **拥挤腿**：CASH45 / CFEV45 / PV / TXTUB / XRENT / PTPR。

## 已验证有效的过墙配方
| 手法 | 实例 | 关键 |
|---|---|---|
| 加腿稀释 / 独有锚 / 换价量腿 | w60_h .6548 / w64_h .6605 / w68_b .6948 / w77_a .6598 | **一个配方只能吃一口**，锚必须独有 |
| 腿系数加权改 PNL 构成 | w85_a .754→.6803 | 独有锚全权 + 共享 PV 降权 **0.5**（甜点）。⚠️ 非普适杠杆 |
| 7 腿配方（Research16） | w121_d `3q9NMgk6` SF5.30/tS2.26 | 3 fnd6 锚 + 引擎腿 + PV + 评级腿 |
| w124_e 三锚扩产 | w125_h 4.78 / w126_h 4.77 | ⚠️ 整族 0916 全灭（0.73~0.99） |
| /cap 缩放破墙 | `kqoq0zed` corr 0.6999 直通 | 质量天花板 ~3.93；**PV = 质量引擎** |
| **本地 corr 筛积压** | `le8EAJLO` SF4.24 | 456 条积压 12 分钟筛完，命中即提交 |
| **leg_lab 离线拼装** | `pwRwWoJ3` **SF6.91** / `9qjqm3Q9` 5.69 / `O0N0R5NY` 5.47 | 只跑单腿建库，组合离线算 |
| **★ 中性化投影（救急，只吃 1~2 口）** | `levpXXGl`(MARKET,.6015) / `omL8Mazn`(SECTOR,.6994) / `YPbLZK2W`(MARKET,.6028) | **下移 −0.14~−0.27，一个几何进 1~2 条就饱和**；MARKET 伤 tS、**SECTOR 保 tS**；只救 corr 0.70~0.72 的近门槛 |
| **★ 第 5 腿加挂（0920，当前主力）** | `zq8jl99K` **SF4.67/tS1.50** corr .6801 直通 | 已验证达标结构**原样不动**（2.0 argmin 主腿 + 双基本面锚 + 0.5 引擎），第 5 腿加挂事件条件化腿 0.5~0.75（evh60a/ev60nb）。24 试 10 过质量闸门。**事件腿不能顶替锚**（w213b 实测 tS 全塌）；**一骨架每美东日只能提交 1 条**——同骨架兄弟互 corr 0.85~0.95（LLNXPaea 被 zq8jl99K 拦在 0.9143） |

**共性 = 必须有独有成分腿。老族价量腿（`-ts_rank(returns,20)` / Amihud `-ts_mean(abs(returns)/volume,20)`）是没被挤爆的几何。**

## 破墙维度总表（0916~0917 全量实证收官，详见 `CLAUDE.md` §6）
**判死 15 项**：①换字段/换锚（`/cap` 归一成市值因子）②**换区域（本账号 USA 单区，ASI/EUR/GLB/HKG/JPN 全 400）**③**风险中性化（SLOW_AND_FAST/SLOW/FAST/CROWDING/STATISTICAL 全 400；RAM 取值非法）**④PPA/PPAC（需风险中性化 + 唯一字段≤3，双不符）⑤universe/truncation/D0 ⑥结构级改造（batch104 SF 0.11~1.15）⑦新数据轴单独成腿 ⑧`vec_avg` 评级轴（SF≤0.88）⑨456 条积压（最低 corr 0.6934，直通 0）⑩换分组粒度（单腿改善 0.17 但空间未打开）⑪顶层 zscore/rank（丢中性化好处）⑫新字段轴全关（0917：option8/socialmedia12/model16/news12 + analyst4 PEAD+0阶30字段+覆盖数，全部不出种子）⑬**腿稀释量产（x174/175：单腿≈−0.02 不可外推，双腿符号不定；赢家进池即成新撞点）**⑭**decay 拉大（x176：12/12 反升 +0.02~0.03）**⑮**逐腿 group_zscore/group_neutralize 替换（x178：14/14 质量摧毁）**。
**→ 可及 14 个数据集已全部测绘完毕，本地可及空间见底；唯一解锁 = 平台侧新权限（多区域 / 新数据集），待李工在平台操作。**
**四条通用教训**：**①先探权限再设计实验**（换区域诱人但没权限）②**悬而未决的"待验证"用最便宜方式第一时间打掉**（Slow+Fast 挂了三天，一次探针就判死）③**本地 corr 精度 ±0.02 内、缓冲线 0.685 有效**（.6996→平台 .6994）④**归因平台前先自证工具**。

## 已证伪（勿再试）
- TOP1000/500 换池；INDUSTRY/SECTOR 中性化单独用；truncation 放开；PV 腿微调；D0 独立性。
- 纯复制冠军骨架换锚（0.78-0.88）；单锚嫁接稀释不够（0.78-0.89）。
- 全新 fnd6 腿当**主腿**质量全灭（cash45/cfoev45 是质量引擎，不能丢）。
- 新信号族单独用无 Sharpe（PCR/情绪/评分/新闻 w72/w73 全灭）；**option9/model51/news18/pv13 单腿 SF 仅 1.1~3.4，加进组合也压不下 corr**（batch158）。
- 强 trade_when 门控伤质量；`rank(ts_regression(...))>0.6` 无增量。
- **新信号轴只能叠加、不能顶替 PV 腿**（两次实证：顶替后 tS 2.08→0.28~1.13 + LOW_SUB_UNIVERSE_SHARPE）。
- **"冷字段=可挖"不成立**：aC<30 的 fnd6 极冷字段平台**无数据**（不报错照常出分）。**假达标判据：多条不同锚指标完全相同（连小数都一样）= 锚无数据**。`fnd6_matrix.json` 的 aC 不可靠；`data-fields` 的 coverage 返回 None。用 `COLD_FIELD_WHITELIST.csv`。
- ⚠️ 上条**不外推到 fundamental2**：最强 `0mR2K6lr`(S=3.45) 与 w103_g 家族用的正是 fundamental2 冷字段（`authorized_stock_buyback_amount` aC=8 等）。
- 平台 NOT FOUND：`xoptepsq` / `fnd6_newqv1300_xrent` / `fnd6_newqv1300_pncepsq`。
- **纯骨架（全 0.5 共享腿）无提交价值**：线性缩放不改截面排序，corr ≈1.0。
- **事件条件化 argmin 腿（0920 w213/w213b）**：单腿全弱（S −0.23~0.74，"老低点做多"方向为负判死）；**顶替基本面锚当佐腿 → tS 全塌（0.96~−0.05）、SF≤3.89 全灭**。只能当第 5 腿加挂（见配方表）。裸 argmin 几何（不条件化）单腿最强 1.36。

## 研报移植结论
### 球队硬币帖（0914，详 `docs/research/`）
- CHN 无权限（region=CHN count=0、TOP500 亦 0）→ 不可复现。
- **可移植 4 招**：①隔夜/日内拆分（`open/ts_delay(close,1)`）②条件符号切换（`group_mean(x,1,market)`）③换手距离 ④**Slow+Fast Factors 中性化（从未测过）**。
- 元教训：优秀量价因子 PnL 殊途同归 → 破局 = 叠加其他数据 + **不同数理方法处理同一数据**。

### Research Paper 16：分析师短期交易（0915）
- Birru/Gokkaya/Liu/Stulz, *JF* 77(3):1829-1875 (2022)。论文自家 S+F 仅 1.86/2.08/2.69 → **只移植结构，不照搬**。
- **两条铁律**：① `ts_mean` 对**离散字段**降换手无效，须先连续化（rank/zscore/vec_avg）；② **`? : NaN` 是 CONCENTRATED_WEIGHT 头号成因**，改 `if_else(cond,·,0)`。降换手：`trade_when` 第三参用 **-1**；`hump(x,0.01)` 优于 ts_mean。
- **字段权限**：无独立 analyst 数据集、`rating` 404。4 个评级字段全在 analyst4 且**全为 VECTOR，必须 `vec_avg`**：`anl4_fs_detail_rec_v4_nd_estimate`(24)、`anl4_basicdetailrec_ratingvalue`(574)、`anl4_eaz2lrec_ratingvalue`(5886)、`anl4_total_rec`(2646)。
- 市值分桶中性化非普适杠杆；撞墙的是离散度/估值轴，**评级偏离度轴可用**。

## 关键事实
- selfCorr ≥ 0.7 触发 Production Correlation 测试；通过 = max corr < 0.7 或 Sharpe 高 10%。
- Sharpe ≈ 15.8 × IR；Fitness = Sharpe × √(|R| / max(T, 0.125))。
- **参数决定生死**：`ts_av_diff(...,45)` SF **6.19** vs 30/60 的 **1.33**；量能窗口 **120>60>90**。
- **包装决定换手**：裸 `rank(x)` SF2.38/T0.469 → `group_rank(x,subindustry)` SF5.89/T0.152（全过率 26.2%→54.4%）。
- **结构甜点**：5–6 腿；给腿加 0.5 权全过率 67%→18.2%。最强腿 = `group_rank(fnd6_xrent/assets,subindustry)`（77.3%）；最强字段签名 = `cashflow_op+enterprise_value+fnd6_xrent`（95.2%）。
- 历史：460/1098 达标（41.9%）只提交 60 个 → **456 条从未提交**；瓶颈是相关性墙不是质量。
- **★ 换分组粒度 = 尚未开采的一类杠杆**：`group_rank(ts_av_diff(cashflow_op/enterprise_value,45), **industry**)` 单腿 **SF 3.36 / 无 FAIL**，几何与 subindustry 版不同 → 池里没有。脚本 `src/mine/mine_batch159.py`。

## 备考 / 面试
- **研究顾问面试 + 背调约 10 月中旬落定**，期间正常挖矿 + 攒 Rank。
- **材料三块**：①《零基础学量化》四小时课程（**占 80% 以上**）②Learn 文档 ③平台常用内容（算子 / Simulation Settings / 回测结果 / 数据）。
- 既有：28 份中文归档 +《备考总纲_详细版》（`docs/exam/`）+ `docs/study/`；Learn 归档落 `docs/study/learn/`，索引见 `00_归档索引.md`。**收齐后进入对练（模拟题除外）**。
- 归档硬约束：**仅用李工给的资料**，不掺外部知识；仅当他明确给链接时才联网。
- 考纲覆盖 14/14 已核；缺口是"能背≠能讲" → 待办：①自己的 Alpha 整理成 3 分钟故事 ②按考纲口述对练 ③数值速查卡。
