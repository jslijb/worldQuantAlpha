# CLAUDE.md — WorldQuant BRAIN 项目工作规范

> 本文件只保留**红线、执行纪律、流水线口径、目录与命令**。
> **挖矿方法论（有效打法 / 判死维度 / 参数标定 / 判决机制 / 踩坑记录）的唯一事实源 = `docs/methodology/00_总纲.md`**，细节一律看总纲，不在本文件重复。
> 最后瘦身：2026-09-19（方法论细节移交总纲；冗余脚本清理，见变更记录）。

---

## 0. 这个项目在做什么

用 WorldQuant BRAIN 平台 API 批量挖 Alpha 因子、过质量闸门与相关性闸门、提交并记账。

| 项 | 内容 |
|---|---|
| 目标 | **提升排名（IS Score 累计）**；每日 5 个高质量 Alpha（下限）+ 历史欠账；Super Alpha 提交线 100 已达成，但**账号未授权 super 模拟**（见下） |
| 高质量定义 | S+F ≥ 4.0（IS Sharpe + IS Fitness）**且** tS ≥ 1.25（验证期不崩）**且** checks 无 FAIL **且** turnover ≤ 25%（0920 加） |
| 真正的瓶颈 | **相关性墙**（详见总纲 §1、§2） |
| 运行环境 | Python `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（conda 环境 bigmodel） |
| 凭据 | `brain_credentials.txt`（项目根，JSON 格式；已 git 忽略，永不入库） |

**★ 目标函数（李工 0920 定，压倒一切的一条）**

> 原话："提交 Alpha 不是目的，提升排名才是目的，后续赚钱更是目的。你需要提升夏普率，同时降低换手率，优化之前的 Alpha 因子，不能只盯夏普率。"

- **提交数量不是目标。** 排名主杠杆是 **IS Score = 所有已提交 Alpha 的 IS 得分累计**，单条贡献与 **Sharpe / Fitness 正相关**（S=3.0 贡献 >400 分，S=1.3 贡献 <100 分）；Total Score 是 Days + IS Score + Uniqueness 三维等权。维度定义见 `docs/project/目标_排名目标.md`。
- **候选排序键 = Fitness，不是 S+F。** `Fitness = Sharpe × √(|returns| / max(turnover, 0.125))` —— 它已把夏普、收益、换手三者综合。按 S+F 排序会优先挑出**高换手炸弹**（TO 40%+、margin 仅 5~8bp），看着夏普高，实际排名贡献低、赚不到钱。
- **turnover 硬数据（2026-09-20 平台 103 条 ACTIVE 实测）**：甜点 **10%~20%**（平均 S+F 4.44）；TO<10% 呆滞（3.90，tS 1.16）；TO 20~30% 偏高（3.94）；TO>50% 失控（tS 0.00）。**margin 是换手率的镜子**：TO<20% → 15~28bp；TO>40% → 5~8bp（**差 3 倍，这就是赚钱能力**）。
- **降换手的三类杠杆（实证）**：① 用 `hump(x)` / `ts_decay_linear(x, 5)` / `quantile()` 包裹（w55_e 由 TO 14.3%→10.9%、margin 21.6→26.3bp）；② 慢速腿替代快腿（`-ts_mean(abs(returns)/volume,20)`、`-ts_rank(returns,20)`、`-ts_delta(close,20)`、`volume/ts_mean(volume,120)`）；③ 设置本身——**decay 0→10 是最大杠杆**（同表达式的 e79PvPpE decay=4/TO19.2%/F2.72 vs 0mR2K6lr decay=1/TO42.2%/F2.13）。
- **高换手族的雷参数签名（勿再有）**：`INDUSTRY + decay=0 + truncation=0.01 + nanHandling=OFF + 腿数 2~3`。
- **低换手高 F 族的参数签名（照抄）**：`decay=10 + truncation=0.08 + nanHandling=ON + SUBINDUSTRY/SECTOR + 腿数 6~8 + 至少一条慢速腿`。
- 判决工具已按此改造：`submit_exempt.py` 增 `--min-f` / `--max-to`，排序键 `S+F` → `F`。

**★ 账号状态与赚钱通道（2026-09-20 API 实测，`GET /users/self`）**：

| 项 | 实测值 | 含义 |
|---|---|---|
| `level` | **GOLD** | 账号层级 GOLD，不是最高档 |
| `onboarding.status` | **SHORTLIST** | **已在顾问候选名单上**（对应研究顾问面试流程） |
| `education.university` | `"not applicable"` | 教育信息未有效填写 |
| `employment` / `recruitment` / `resume` | **全 null** | **招聘档案三项全空** |
| `geniusLevel` | null | — |
| `dateCreated` / `dateApproved` | 2026-08-15 | 账号 8 月 15 日建好 |

- **Super Alpha 不可用**：`POST /simulations` 带 `"type": "SUPER"` → `400 {"type":["Not permissioned for super simulations"]}`。⇒ **"累计 100 提交"只是门槛之一，真正卡的是账号权限层级**（此前以为 100 条达成即可用，是误判）。
  - 顺带拿到 SUPER 模拟的必填字段（将来有权限时直接用）：`settings.selectionHandling`、`settings.selectionLimit`、`combo`（string）、`selection`（string/需为字符串）。
- 平台页面帮助语原文：`"Continue submitting Alphas — top rankers may get consultant invites every week."` ⇒ **排名直接挂钩顾问邀约**，与李工的求职主线是同一条通道。
- 收入规则：Regular Base Payment 1~60 USD/天、**每日结算上限 4 个**；Super Alpha 每日上限 1 个、与 Regular 分开计算（**当前无权限**）。前三个月核心目标是提 **Value Factor**，"50%+ Alpha 集中在单一 region/turnover/字段"会**压低**它 → 要往分散走，不要继续堆同族。

**★ 官方评分算法原文（2026-09-20 归档复核，唯一事实源）**

来源：`docs/study/learn/docs/01_discover-brain/07_scoring-algorithm-challenge-users.md`（平台 `GET /tutorial-pages/scoring-algorithm-challenge-users` 原文，非二手推断）。此前"目标_排名目标.md"里的三维等权模型是**从排行榜截图反推的估算**，本节是官方口径，冲突时以本节为准。

| 官方要点 | 原文 | 对我们的含义 |
|---|---|---|
| 计分单位 | "Score is tied to day, not to individual Alphas" | 分数按**天**结算，不是按单条 Alpha |
| 两个因子 | **Quantity Factor**（当天提交条数越多分越高）+ **Quality Factor**（当天所有 Alpha 质量因子的**平均**） | 质量是**平均**——当天多提交一条差的，会把当天整批的质量均值**拉下来** |
| 归一化 | "normalized across all the users who submitted at least one Alpha on that particular day" | 横向和别人比，不是绝对分 |
| **每日上限** | **"Maximum daily score is 2000. Typically, this involves submitting 1 to 2 alphas a day."** | **★ 单日堆数量是白干**：Quantity 在 1~2 条就饱和。我们 0920 单日提交 18 条，纯浪费 |
| 层级线 | BRONZE 1000 / SILVER 5000 / GOLD 10000 | 我们 level=GOLD |

**Quality Factor 的四个官方子项（原文列举）**：

| 子项 | 官方说法 | 我们现状（0920 实测） | 可动杠杆 |
|---|---|---|---|
| **Universe** | "smaller universes get more score" | **97.9% 是 TOP3000（最大池）→ 该项拿最低分** | 降池到 TOP1000/TOP500（**从没当得分项测过**，w241 在跑） |
| **SelfCorrelation** | "the less the better" | 有记录 74 条：**均值 0.694 / 中位 0.683**；**25 条 ≥0.70**（最差 1YwKML56 0.9687、rKj7w0Z1 0.9667、9qX3M2mq 0.9569） | **★ 降 corr 不只是"过墙"，它本身就是加分项**——与 0a 的降 corr 四杠杆同向 |
| **Fitness** | "the larger the better" | **均值仅 1.860**：F≥3.0 只有 1 条，1.5~2.0 有 49 条，F<1.5 有 21 条 | 提 F 是最大的单点杠杆（F 已含 S/收益/换手三者） |
| **Delay** | "D1 Alphas contribute more to score than D0" | delay=1 占 2196/2423（90.6%）✓ | 已达标，保持 D1 |

- ⚠ **turnover 不在官方子项清单里**，但它通过 **Fitness** 进入（`F = S × √(|ret| / max(TO, 0.125))`）→ **TO 低于 12.5% 不再有额外收益**。所以换手率的目标区间应设为 **10%~12.5%**（此前记的"TO≤20%"只是"别太差"的下限，不是最优）。低于 10% 反而常伴呆滞信号（TO<10% 档平均 S+F 3.90、tS 1.16）。
- **推论（据此调整打法）**：① **不再为凑数提交边际 Alpha**——它拉低当天质量均值、且入池后抬高后续所有候选的 selfCorr，是**负向资产**；② 单日 1~2 条**高质量**即可拿满当天 Quantity，多出来的仓位应该用来**试新轴**而不是**发变体**；③ 候选排序键维持 **Fitness**，但新增"Universe 降池"与"selfCorr 目标 <0.4"两个方向。

**流水线口径（2026-09-20 修正·重要）**：
0. **相关性判决：两条路（0920 晚复核判决书原文后确认，此前一轮"豁免线是假的"是误判）**：
   - ① **直通**：本地 max corr ≤ 0.685（缓冲线）→ 提交。平台实际 corr ≈ 本地 +0.005。
   - ② **豁免线（规则成立，未被推翻）**：corr ≥ 0.7 的候选，只要 **候选 S ≥ 1.10 × max(所有 corr≥0.7 对手的 S)** 平台就放行。
     - ⚠ **上一轮的"反例 j2Az8n0E"经判决书原文复核后不成立**：其对手为 MPaPe0oo(S2.30)/omL8Mazn(S2.28)/LLNXEe7L(S2.30)/**kqVp6wnO(S2.51)**，豁免线 = 1.1×2.51 = **2.761**，候选 S=2.60 **< 2.761** → **平台拒得正确，规则成立**。当时误判的原因：本地 corr 低估 → **漏收 kqVp6wnO** → 用 MPaPe0oo 的 2.30 算成 2.53 → 误以为"够线却被拒"。
     - 结论：**规则可以用，但前提是"对手收全"** —— 这正是 `--corr-floor` 必须压到 0.66 的原因（宁可多收）。
   - **★ 0920 22:00 修正（推翻当晚早些时候"两条路都走不通"的结论）**：豁免路**是活的**，关键在**候选 S 与 `need` 的关系是"可以动的"**。
     - 当时判"豁免 0 条"的错因：只拿**基线 decay** 的候选 S 去比 `need`，没意识到 **decay 可以调 S**。实测两条当天入池：
       | 候选 | 基线 S | 调 decay 后 S | `need` | 平台 selfCorr | 结果 |
       |---|---|---|---|---|---|
       | `x162_w164_04_MAR` d10→**d6** | 2.45 | **2.55** | 2.54 | **0.8042** | ✅ ACCEPTED |
       | `w189_01__g_bdv` d10→**d6** | 2.45 | **2.58** | 2.55 | **0.7725** | ✅ ACCEPTED |
     - 反向验证（本地 `need` 算得准，一分不差）：
       | 候选 | S | `need` | 平台 selfCorr | 结果 |
       |---|---|---|---|---|
       | `w41_b__d4` | 3.19 | 3.212 | 0.8149 | ❌ 差 0.022 |
       | `w39_i__d4` | 3.20 | 3.212 | 0.7504 | ❌ 差 0.012 |
     - ⇒ **平台真实判据 = 豁免线，不是 corr 硬阈值**：corr **0.77~0.80 照样放行**，被拒的两条 corr 反而更低（0.7504/0.8149，都在 0.77~0.82 区间）——**决定成败的是 S vs 1.1×max(对手 S)，不是 corr 高低**。
     - ⇒ **本工具算的 `need` 与平台一致**（4 例全对），可信；`--corr-floor 0.66` 的保守设定被验证是**对的**（收全对手才能算对线）。
     - ⚠ **`need` 是时变的**：池子每入池一条，相关家族的 `need` 就抬一次。**必须用当前池实时算，禁止引用历史日志里的 need**（此坑当天踩到：`w39_i`/`w41_b` 的旧 need 写 2.71/2.46，实际已是 3.212 → 误判为"够线"去打，被拒）。工具：`submit_exempt.py` 每次运行都重算，直接用它。
   - **当前有效出量路径（0920 22:00 起，两条实证）= 低靶区 + 降 decay 顶 S 压线**：
     ① 找"只撞弱靶"的候选（最高对手 S 低 → `need` 低）：工具 `_autologs/sweetspot.py`；
     ② 沿 decay 阶梯下探（基线 d10 → d8 → d6 → d5 → d4），S 上升、TO 同步上升；
     ③ **停点 = S 刚过 `need` 且仍满足 TO ≤ 20% 且 tS ≥ 1.25**（02 家族拐点在 d6：S2.55/TO19.6%/F2.18/tS1.69）；
     ④ 用 `submit_exempt.py` 或 `submit_v3.py` 直接 POST（免费精确测量）。
     - ⚠ 别贪：decay 再往下 S 只多 0.1~0.2，但 TO 从 20% 炸到 43%~67%（d4 26.3% / d2 43.1% / d1 67.4%），F 塌到 1.3~2.0 → 质量闸门崩。
   - 直通（本地 ≤0.685）仍然稳、仍然优先；**0.685~0.69 这段不要判死，直接 POST 测**（实证：本地 0.6862 → 平台 **0.6846**，偏移 **−0.0016**，平台比本地还低）。
   - 执行工具：`src/submit/submit_exempt.py '<前缀通配>' --min-f 2.0 --max-to 0.20 --limit N --tag <日期-批次> [--dry]`。**已修两个混用的阈值**：`--corr-floor 0.66` 只负责"收哪些对手进名单"，新增 `--corr-direct 0.685` 负责"能否直通"；日志现在报**真实 `corr_max`**（旧版报的是"最高 S 对手的 corr"，会看错）。
   - 对手 S 取**平台实况**（`GET /alphas/{id}` 的 is.sharpe，缓存 `data/alpha_quality_analysis/pool_s.json`），不取台账（台账 S 列常为空）。
0a. **降 corr 的四大杠杆（按实测效力排序，0920 数据）**：
   - **① 换分组为 bucket（★ 0920 22:00 已从假设升级为实证结论）**：**直接证据**——`9qX3M2mq_v2` 家族走 subindustry/sector 都卡 0.72+，改成 `bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")` 后**平台 selfCorr 0.6846 → ACCEPTED 入池**（`9qX3M2mq_v2__r_bvol` / 88jKeENW）。此前入池的 `O0N5o3Nv`（波动率桶）与 `9qjZ8oZ2`（成交额桶 `bucket(rank(ts_mean(volume*close,20)))`）同属桶分组。
     - ⚠ **不是万能**：`w162_06` 家族四变体（`__g_ind` 0.7564 / `__g_sec` 0.7593 / 本体 0.7678 / `w164_04` 0.7698）桶分组救不动 → **对低 TO / 慢腿骨架有效，对高相关家族无效**。
     - ⚠ **算子上限卡死满腿候选**：平台上限 64，而近线候选多条 `operatorCount` 已达 **63**（如 `x174_w125_d_AMIINT`、`A_SEC`），换桶需 +6 → 超限，**必须同时减腿**（少挂 1~2 条 0.5 权重的锚）才能换分组。批次 `_autologs/gen_w242.py`（11 家族 × 3 变体 = 33 组）。
     - ⚠ **算子上限卡死满腿候选**：平台上限 64，而近线候选多条 `operatorCount` 已达 **63**（如 `x174_w125_d_AMIINT`、`A_SEC`），换桶需 +6 → 超限，**必须同时减腿**（少挂 1~2 条 0.5 权重的锚）才能换分组。
   - **② 中性化换挡（有效但效力因骨架而异，不是普适 −0.09）**：`x174_w125_d_AMIINT` 骨架 SUBINDUSTRY 平台 corr 0.7367 → MARKET **0.6467**（−0.090，直通入池）；但 `w189_01` SUBINDUSTRY 0.8041 → SECTOR **0.7985**（仅 −0.006，仍撞 pwRwWoJ3，判死）。
     - ⚠ 结论修正：**A_MAR 的成功是"波动率桶骨架 + MARKET"双因素**，不能把 −0.09 当换挡的通用效力。换挡后必须实测 corr，别假设。
     - ⚠ 代价：**MARKET 伤 tS**（`w189_01__MAR` tS 塌到 1.15 不过闸）、**SECTOR 保 tS**（同骨架 `w189_01__SEC` tS 1.91 仍达标）。换挡优先试 SECTOR。
   - **③ 加腿稀释 / 系数加权**：只对新轴有效。**改良已提交骨架基本无效**——实证 qMW92Az2_v3 vs 其本体 qMW92Az2 corr **0.7886**。李工"优化之前的 Alpha 因子"这个方向受此硬约束。
   - **④ 换锚**：基本无效（候选池 97% 共享 `assets/close` 基准）。
0b. **平台判决书是唯一金标准**：
   - `POST /alphas/{id}/submit` 是一次**免费且无副作用的精确测量**：成功 → 201 入池；被拒 → 403 返回**完整判决书**（8 项 checks + `is.selfCorrelated.records` 逐条列出对手 id / corr / S / returns / turnover / fitness / margin）。
   - 被拒的 alpha 状态仍是 `UNSUBMITTED`，可改造后重投 → **把 POST 当 corr 测量仪用**，比本地估算准得多。
   - 判决书自带对手全指标 → **定向改造有靶**：撞谁、差多少、对手换手多少，一目了然。
   - 工具：`_autologs/get_verdict.py <alpha_id>` 取完整判决书（解决 `submit_v3.py` 只打 300 字符的盲区）。
1. leg_lab 离线生成候选（阈值 `--max-corr 0.55~0.57`，它只是生成器不是判决器）
2. `pnl_corr.py` 实测复核（供**直通**判定；local ≤0.685 才放行）
3. `submit_v3.py` 提交——**出现 FAIL 才是拒信**，无 FAIL 只记 UNKNOWN 不记 REJECTED
4. 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` **只追加**；池子只取自台账
5. 质量闸门、判决机制、偏移定律 → **总纲 §3、§5**
6. **每提交成功一条必须做两件收尾**：① 台账追加（三证之一）；② PnL 入 `data/alpha_quality_analysis/pnl/` 缓存、S 入 `pool_s.json` —— 否则下一轮判决池子取不全（脚本会中止）或豁免线算错。

---

## 1. 目录规范（强约束）

```
D:\Python\worldquant\
├── CLAUDE.md                  ← 本文件（红线 + 流水线口径）
├── README.md / brain_credentials.txt / .gitignore / .gitattributes
├── src/                       ★ 全部 Python 代码
│   ├── core/                  utils.py（登录/取字段）、AlphaSimulator.py（并发模拟器）
│   ├── analysis/              leg_lab.py（腿库离线拼装，生成器）、pnl_corr.py（★本地 corr 判决）、
│   │                          pool_diag.py、screen_mined.py、screen_unsubmitted.py、exempt_scan.py
│   ├── mine/                  活跃生成器：mine_batch181.py（模拟执行器）、mine_w200/w201_intraday.py、
│   │                          mine_w203~w208（轴收口实验批）、mine_neut_convert.py、mine_from_spec.py
│   ├── submit/                submit_v3.py（★提交器）、auto_submit_passers.py（★批量判决+提交）、
│   │                          run_queue_v3.py、submit_v2.py、verdict_dump.py
│   ├── ops/                   git_snapshot.py（★统一快照入口）、auto_submit_loop.py（停用）
│   ├── tools/                 fetch_alphas.py、fetch_learn_docs.py、fetch_learn_video.py、merge_video_notes.py
│   └── archive/               expr_library.py（历史表达式库）
├── data/alpha_quality_analysis/
│   ├── SUBMITTED_LEDGER.csv   ★ 台账，唯一事实源，只追加
│   ├── mined/                 模拟结果 json（{批次}_{序号}.json）
│   └── （candidates_all.csv / leg_value_rank.csv / *_matrix.json 等）
├── docs/
│   ├── methodology/           ★ 00_总纲.md = 唯一事实源；01~06 = 历史附录（只读不改）
│   ├── research/              外部论文/研报移植记录
│   ├── study/  exam/          备考材料（★面试材料，不许动）
│   ├── project/ reference/ archive/
└── _autologs/                 运行日志（临时产物，可清理）
```

**放置规则**：新挖矿脚本 `src/mine/mine_w{NNN}_*.py`（编号递增）；新结论**只写 00_总纲.md**（带日期，推翻旧结论明写"已推翻+日期"）；模拟 json 落 `mined/`；过程日志落 `_autologs/`。**禁止**根目录新增任何文件。

**路径写法**：`src/` 下脚本必须自带项目根定位（向上找 `brain_credentials.txt` 后 `os.chdir`）。

---

## 2. 代码与数据规范

- 模拟并发**上限 2**（429 退避）；长跑脚本**必须可断点续跑**（os.path.exists 跳过 + 台账去重）。
- 轮询限速 ≥1.3 秒/请求（60 请求/分钟限流；高频打 corr 端点会被 RST）。
- **终端一律 PowerShell**（Bash 工具 PATH 损坏，exit 127 静默失败）；前台 stdout 空捕获时让 python 写文件再读；PowerShell 重定向显式 `-Encoding utf8`。
- 台账读用 `utf-8-sig`（首列 BOM）；S=`row[2]`、F=`row[3]`，别拿 Fitness 当 Sharpe。
- 时间口径：`dateSubmitted` 美东；**北京 12:00 = 美东 00:00**。

---

## 3. 常用命令与版本控制

```powershell
$PY = "D:/ProgramData/Miniforge3/envs/bigmodel/python.exe"

# 本地算 self-corr（提交前必跑，直通缓冲线 0.685）
$PY src/analysis/pnl_corr.py <cid|alpha_id> [--top 8] [--refresh]

# 腿库离线拼装（候选生成器，不是判决器）
$PY src/analysis/leg_lab.py eval "L_pst:1.5, P_tr20:1.5"
$PY src/analysis/leg_lab.py search --min-s 2.1 --max-corr 0.57

# 批量判决+提交（质量过滤 -> 本地 corr -> submit_v3 -> 台账，每成功一条自动更新池子）
$PY src/submit/auto_submit_passers.py '<mined glob>' --min-sf 4.0 --min-ts 1.25 --max-corr 0.685 --limit N --tag <批次名>

# 单条提交 / 判决书 dump
$PY src/submit/submit_v3.py <alpha_id> <cid>
$PY src/submit/verdict_dump.py <alpha_id> <cid>

# git 快照（每批挖矿/提交/文档改动后必做）
$PY src/ops/git_snapshot.py --allow-public ["说明"]
$PY src/ops/git_snapshot.py --push-only --allow-public   # 推送失败重试
$PY src/ops/git_snapshot.py --no-push / --dry-run
```

**必须串行提交**（并发 POST 201 会互堵永不裁决，0914 实测）。**推送失败（502/SSL/HTTP2 framing）= 本地代理抽风，重试即可；本地提交永远先落库，不受影响。**

- **远端**：`origin` = `https://github.com/jslijb/worldQuantAlpha.git`（**Public**，李工 0915 确认），分支 `main`。`--allow-public` 只在已确认的 origin 上用；origin 换仓库必须重新确认可见性。
- **凭据保护双重防线**：`.gitignore` + `.git/hooks/pre-commit`。禁止 `git add -f` 加凭据、禁止 `--no-verify`。
- **回滚**：`git checkout <hash> -- <路径>` 取回单个文件。

### 提交纪律与代码整洁（李工 0926 定）
- **改完必提交**：任何代码 / 文档 / 台账改动完成即跑 `git_snapshot.py --allow-public` 落库（公开仓库已确认，见上）。禁止"攒一批再交"——分散改动易丢、易冲突、难回溯。
- **提交前先清理（硬纪律，三条不过不准提交）**：
  1. **去重**：功能相同的脚本合并为一个。同类批次脚本（`src/mine/mine_wNNN_*.py`）归并成参数化入口；版本迭代脚本只留最新版（如 `submit_v2.py` 之类旧版删除，禁止双版本共存）。
  2. **提公共**：多处复用的代码段（平台请求 / 判分 / 台账读写 / 指标计算）抽成 `src/core/` 下的函数或类，禁止在各脚本里复制粘贴同样的几十行。
  3. **不入库一次性脚本**：`_autologs/` 下的探索性 / 临时脚本（探针、debug、对账、一次性统计）**不进入版本历史**——需长期保留的才搬进 `src/` 对应模块；该目录定位为"运行产物"，已被跟踪的历史文件择机 `git rm --cached` 清理。
- **结构红线**：`src/` 严格按现有分层（mine / submit / analysis / core / ops / tools / pull）归类；写新功能前先想"放进哪个模块、复用哪个公共函数"，禁止在根目录或 `_autologs/` 随手丢新文件。

- **全量备份**：`D:\Python\worldquant_backup_20260915\`（勿删）。

---

## 4. 平台硬约束速查（细节与完整判死表 → 总纲 §2）

| 约束 | 内容 |
|---|---|
| 并发模拟 | 上限 2，超 429 |
| API 限流 | 60 请求/分钟；批量预检必须限速 + 退避 |
| 字段类型 | `fnd6_*` 明细多为 VECTOR（divide 不支持事件输入），选字段按 `type=MATRIX` 过滤 |
| `_v1300` 字段 | delay=0 不可用 |
| neutralization 可用值 | NONE / MARKET / SECTOR / INDUSTRY / SUBINDUSTRY（风险中性化全轴 400，0916 判死） |
| 区域 | 本账号 USA 单区（ASI/EUR/GLB/HKG/JPN/CHN 全无权限，0916 判死） |
| 判决机制 | 判决 4~9 秒出；403+is.checks = 判决书；**FAIL 才是拒信**；对手明细在 `is.selfCorrelated.records` → 提交即测量；`correlations/self` 端点弃用 |
| 本地 corr | pnl 先差分；池子只取自台账；缓冲线 0.685 |

---

## 5. 红线

1. **不删除、不覆盖台账**（`SUBMITTED_LEDGER.csv`），只追加。
2. **不删除已提交的 Alpha**。
3. **考试/考核进行中不提供答案**——含各类限次数的准入/认证测评；"开卷"与"对方未禁用 AI"均不改变判断。只做考后复盘、考前陪练。
4. **不把不同项目的技术张冠李戴**（本工作区只做 WorldQuant）。
5. 对外动作（提交、发消息、任何不可逆操作）先确认；对内动作（读、分析、整理、写文档）放手做。
6. **`docs/exam/`、`docs/study/`（面试/备考材料）不许动**。

### 执行纪律（李工 0916 定，长期有效，加压条款；0919 补两条硬规则）

7. **日目标线 = 5 条高质量（下限）~8 条（加压线）+ 历史欠账**。目标定下就要完成；完成不了给**根因和补救**，不给道歉。
8. **不许把活推给明天**：列出的待试轴必须**当天跑完并给结论**（有效/无效/有效但有上限）；一个方向当天开了头，当天必须出结论。
9. **归因平台前先自查工具**：任何"平台故障"结论必须附自证。前车之鉴：0915 报的"自相关服务宕机 434 条积压"，根因是自家 `blind_submit.py` 丢判决书——三种假判决全是工具 bug，没有一次是平台的问题。
10. **每轮汇报固定四项**：本轮提交数 / 台账总数 / 当日（美东）计数 / 剩余欠账。
11. **"不通"必须带数字**：说走不通必须给量化证据，不许"试了不行"。
12. **三条铁律**（详见总纲 §4）：先探权限再设计实验；悬而未决项用最便宜方式第一时间打掉；结论必须实测。
13. **说人话（李工 0920 定，永久有效）**：汇报不许用行话、缩写、自造概念。"近门槛家族全部有主"这种话必须说成"这些候选跟我们自己之前已经提交上去的因子太像，平台一算相关度就拒"——谁撞了谁、为什么不能再提，一句话讲明白。写完先自查：李工不带上下文能一遍读懂吗？读不懂就重写。
14. **今天能做的今天做完，禁止"明天再挖"（李工 0920 定）**：发现可执行方向（配方、突破口、新数据），**当场开跑当场提交**，不许写进"下一步计划"收工。汇报里出现"明天"字样 = 违规，除非该动作物理上依赖未到的美东日限额或李工侧未给的输入。

### ★ 每日目标的硬定义（李工 0919 定：5 个 = 确定提交，不是"觉得提交了"）

- **每日 5 个高质量 Alpha，计数只认台账**：一条提交要算数，必须**三证齐全**——① `GET /alphas/{id}` 核到 `status==ACTIVE`；② `dateSubmitted`（美东）落在当日；③ 台账 `SUBMITTED_LEDGER.csv` 追加完成。
- **以下情况一律不算数**：模拟达标 / 预检通过 / `POST /submit` 返回 201 受理 / "流程走完了应该提交了"。历史教训：0914~0915 报"积压待发"的候选，事后核查很多根本没提交成功。
- 每轮汇报的四项数字，李工可以拿台账按 `dateSubmitted` 美东日聚合独立核查——**对不上就是虚报**。
- 每日收尾必做一次台账复核脚本（读台账、按美东日聚合、报当日数与欠账），不许跳过。

### ★ 卡盘停机检查规则（李工 0919 定：卡住不许硬磨）

- **触发线：同一个目标连续 2~3 小时 0 提交 / 0 过墙，必须停下来查原因**，禁止换参数继续硬扫、禁止"再跑一批试试"。
- **连续多轮报"平台故障 / 服务不可用"= 危险信号，先默认是自己错了**。道理很直白：平台那么大一个公司，自家服务连续几天故障不解决，说不过去——0914~0915 连报两天"自相关服务宕机"，李工没看任何数据，凭直觉就觉得不对，事后证明全是自家工具 bug（假判决三种）。
- 报"平台故障"前必须过三关：① 我的工具在同一端点能拿到正确结果吗（拿已提交 alpha 当探针）；② 有平台侧独立佐证吗（状态页/官方渠道），单凭空 body 不算；③ 故障"持续"超过 4 小时了吗——超过就按自己的问题查。
- **卡住时的三查动作**（按顺序做完才许继续跑）：① 查工具——日志里有没有静默失败、丢数据、吃掉判决（如 leg_lab 丢池成员、blind_submit 丢判决书）；② 查标定——pred→real 偏移有没有漂移、池子完不完整、阈值还适不适用；③ 查假设——有没有把"待验证"当"已验证"、把旧 regime 的结论套在新数据上。
- 查完给出书面根因再恢复；查不出根因就向李工报告卡点，**不许默默继续空转**。

---

## 6. 快速导航

| 想知道什么 | 看哪 |
|---|---|
| **当前有效打法 / 判死维度 / 参数标定** | `docs/methodology/00_总纲.md`（唯一事实源） |
| 提交判决机制 / 假判决 / 踩坑记录 | 总纲 §5、§6 |
| 某个旧结论哪来的 | `docs/methodology/01~06`（历史附录，证据链） |
| 台账 / 未提交候选 | `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` 等 |
| 历史表达式 | `src/archive/expr_library.py` |
| 备考/面试材料 | `docs/exam/`、`docs/study/learn/`（先看 `00_归档索引.md`） |
| 研报移植记录 | `docs/research/` |

---

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-09-15 | 创建。项目重构（1900 散乱文件 → 分层）；纳入 git；Learn 归档链路 |
| 2026-09-16 | 判决机制破案（403+is.checks 判决书 / 三种假判决 / submit_v3）；corr 口径修正 |
| 2026-09-17 | 破墙维度全量实测（15 项判死）；本地 corr 工具链（pnl_corr / leg_lab） |
| 2026-09-18 | 偏移标定漂移修正（+0.12→+0.29，主腿占比定律）；日内几何主腿破墙（3qXd5vg0） |
| 2026-09-19 | **本文件瘦身**：方法论细节移交 `docs/methodology/00_总纲.md`（唯一事实源，旧 01~06 降级历史附录）；**代码清理**：删 79 个冗余脚本（mine_batch120~180 共 58 个、submit 旧件 6 个、一次性 tools 15 个；删前快照 37317a4 可回滚）；台账/json/判死表未动 |

---

### 附录：历史版本说明（0915~0918 详细变更见 git log 与 00_总纲 §2 日期标注）

原第 6 节"平台硬约束"大表（判死维度逐条证据、Learn 接口细节、auto_submit_passers 用法、PnL 线性近似推导等）已于 2026-09-19 移入 `docs/methodology/00_总纲.md` 与历史附录；术语译法规范保留在 `docs/exam/备考总纲_详细版.md` 术语对照表并继续同步维护。
