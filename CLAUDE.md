# CLAUDE.md — WorldQuant BRAIN 项目工作规范

> **定位：本文件只存强约束**——红线、执行纪律、提交硬闸、流水线强制项、平台硬边界。
> 方法论（有效打法 / 判死维度 / 参数标定 / 判决机制细节）唯一事实源 = `docs/methodology/00_总纲.md`，本文件不重复。
> 变更历史 = git log，本文件不设变更记录表。
> **本文件的任何修改必须先获李工审批**（0926 定）。

---

## 1. 项目与目标（唯一口径）

用 WorldQuant BRAIN 平台 API 批量挖 Alpha 因子、过质量闸门与相关性闸门、提交并记账。

| 项 | 口径 |
|---|---|
| 目标 | **challenge 榜 rank 进前 10**（0921 拍板）；`leaderboard.isScore` 即比赛分口径，禁止再质疑 |
| 日常硬线 | **每美东日提满 5 条**（下限）+ 历史欠账；**绝不空仓**（Days 会主动流失，断签不可逆） |
| 排名口径（0926 定） | isScore = 合并池表现分（PERFORMANCE）：动态重算、**会掉**、非逐条求和；低 corr 互补候选的边际贡献 > 高 selfCorr 条。证据链 → `.workbuddy/memory/2026-09-26.md` |
| 排序键 | 候选排序键 = **Fitness**，不是 S+F（`F = S×√(|ret|/max(TO,0.125))` 已综合夏普/收益/换手）；TO 甜点 **10%~12.5%**（低于 12.5% 无额外收益）。降换手 / 降 corr 的具体杠杆 → 总纲 §1、§3.3 |
| 时间口径 | `dateSubmitted` 按美东；**北京 12:00 = 美东 00:00** |
| 运行环境 | Python `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（conda bigmodel） |
| 凭据 | `brain_credentials.txt`（项目根，git 已忽略，永不入库） |

## 2. 账号权限硬边界（2026-09-20 API 实测）

- level=**GOLD**；onboarding=**SHORTLIST**（已在顾问候选名单）。**当前处于顾问面试阶段**：资格赛"日上限 2000 攒 10000 积分"是第一阶段（已通关，历史）；通道四步 = 积分 10000 → 笔试 → 面试 → 背调（约 1 个月）。**后续挖因子与 10000 积分无关**。
- **Super Alpha 无权限**（`POST /simulations` 带 `type:SUPER` → 400）；"累计 100 提交"只是门槛之一，卡的是账号权限层级。将来有权限时 SUPER 必填字段：`settings.selectionHandling`、`settings.selectionLimit`、`combo`、`selection`。
- 区域：USA 单区（ASI/EUR/GLB/HKG/JPN/CHN 全无权限，0916 判死）。
- 收入规则：Regular 1~60 USD/天、每日结算上限 4 个；前三个月核心目标是提 Value Factor——避免 50%+ Alpha 集中在单一 region / turnover / 字段。

## 3. 提交质量标准（李工 0926 定死；全文唯一标准，修改必须先获李工审批）

**四条硬闸，全部满足才可提交，缺一不交：**

| # | 指标 | 线 |
|---|---|---|
| 1 | Sharpe + Fitness | **S+F ≥ 4.0** |
| 2 | 检测夏普 tS | **tS ≥ 1.25** |
| 3 | 换手率 TO | **TO ≤ 20%** |
| 4 | 平台检查 | **无任何 FAIL** |

- **本标准锁死**：任何修改（放宽或收紧）必须先获李工审批；自动化与会话一律不得自行放宽或另立口子。
- 每日任务书等指令中与本节冲突的质量判据（含 0922 修订的"tS≥1.0、TO≤50% 可直接交"）**自 0926 起作废**，一律以本节为准。
- 0925~0926 曾按放宽口子交贴线货（TO 44~46%、tS 1.08、selfCorr 0.69），合并表现分净掉 177（8923→8746）——这是本节锁死的原因，留档防再犯。

## 4. 执行流水线（强制顺序）

1. **候选生成**：`leg_lab` / specs 批次离线生成（阈值 `--max-corr 0.55~0.57`——它只是生成器，不是判决器）。
2. **本地复核**：`pnl_corr.py` 实测（PnL 先差分，池子只取自台账），直通缓冲线 = 本地 ≤ 0.685。
3. **相关性判决两条路**（实证与细节 → 总纲 §3.3）：
   - **直通**：本地 max corr ≤ 0.685 → 提交；**0.685~0.69 这段不判死，直接 POST 测**。
   - **豁免**：corr ≥ 0.7 的候选，**候选 S ≥ 1.10 × max(所有 corr≥0.66 对手的 S)** → 平台放行。`need` 是时变的，**必须用当前池实时算，禁止引用历史日志里的 need**；对手必须收全（`--corr-floor 0.66` 宁可多收）。
4. **提交前三道体检**：`check_fail_hist` / `one_corr` / `pair_now`。
5. **提交**：`judge_now.py` 重判 → `submit_v3.py` 执行，**必须串行**（并发 POST 201 会互堵永不裁决，0914 实测）。**出现 FAIL 才是拒信**（403 全 PASS 无 FAIL = 过）；POST 后 status=None 须 GET 核实 ACTIVE（卡单 ≠ 失败）。POST 是免费精确测量仪：被拒的 alpha 仍是 UNSUBMITTED，可改造重投；判决书工具 `get_verdict.py`。
6. **收尾两件（每成功一条必做）**：① 台账追加；② PnL 入 `data/alpha_quality_analysis/pnl/` 缓存、S 入 `pool_s.json`——否则下一轮判决池子取不全（脚本中止）或豁免线算错。
7. **频控**：每骨架每美东日只提 1 条；同日多条先 `pair_now.py` 排自撞。

## 5. 红线

1. **不删除、不覆盖台账**（`SUBMITTED_LEDGER.csv`），只追加。
2. **不删除已提交的 Alpha**。
3. **考试/考核进行中不提供答案**——含各类限次数的准入/认证测评；"开卷"与"对方未禁用 AI"均不改变判断。只做考后复盘、考前陪练。
4. **不把不同项目的技术张冠李戴**（本工作区只做 WorldQuant）。
5. 对外动作（提交、发消息、任何不可逆操作）先确认；对内动作（读、分析、整理、写文档）放手做。
6. **`docs/exam/`、`docs/study/`（面试/备考材料）不许动**。

## 6. 执行纪律（李工定，长期有效）

7. **日目标线 = 5 条高质量（下限）~8 条（加压线）+ 历史欠账**。目标定下就要完成；完成不了给**根因和补救**，不给道歉。
8. **不许把活推给明天**：列出的待试轴必须**当天跑完并给结论**（有效/无效/有效但有上限）。
9. **归因平台前先自查工具**：任何"平台故障"结论必须附自证。前车之鉴：0915 报的"自相关服务宕机 434 条积压"，根因是自家工具丢判决书——三种假判决全是工具 bug，没有一次是平台的问题。
10. **每轮汇报固定四项**：本轮提交 id+指标 / 台账总数（唯一 id 口径）/ 当日（美东）计数 / 剩余欠账。李工可拿台账按 `dateSubmitted` 美东日独立核查——对不上就是虚报。
11. **"不通"必须带数字**：说走不通必须给量化证据，不许"试了不行"。
12. **三条铁律**（详见总纲 §4）：先探权限再设计实验；悬而未决项用最便宜方式第一时间打掉；结论必须实测。
13. **说人话（0920 定，永久有效）**：汇报不许用行话、缩写、自造概念。"近门槛家族全部有主"必须说成"这些候选跟我们已提交的因子太像，平台一算相关度就拒"。写完自查：李工不带上下文能一遍读懂吗？
14. **今天能做的今天做完，禁止"明天再挖"（0920 定）**：汇报里出现"明天"字样 = 违规，除非该动作物理上依赖未到的美东日限额或李工侧未给的输入。

### ★ 每日目标的硬定义（李工 0919 定：5 个 = 确定提交，不是"觉得提交了"）

- 计数**只认台账**，一条提交算数必须**三证齐全**：① `GET /alphas/{id}` 核到 `status==ACTIVE`；② `dateSubmitted`（美东）落在当日；③ 台账追加完成。
- 模拟达标 / 预检通过 / POST 返回 201 / "流程走完了"——**一律不算数**。
- 每日收尾必做台账复核（读台账、按美东日聚合、报当日数与欠账），不许跳过。

### ★ 卡盘停机检查规则（李工 0919 定：卡住不许硬磨）

- **同一目标连续 2~3 小时 0 提交 / 0 过墙，必须停下查原因**，禁止换参数硬扫。
- 连续多轮报"平台故障"= 危险信号，**先默认是自己错了**。报障前过三关：① 工具在同一端点能拿到正确结果吗（拿已提交 alpha 当探针）；② 有平台侧独立佐证吗（单凭空 body 不算）；③ 故障"持续"超 4 小时了吗——超过就按自己的问题查。
- 卡住时三查（按顺序做完才许继续）：① 查工具（静默失败/丢数据/吃判决）；② 查标定（偏移漂移/池子完整性/阈值适用性）；③ 查假设（有没有把"待验证"当"已验证"）。
- 查完给书面根因再恢复；查不出就报李工卡点，**不许默默空转**。

## 7. 代码与数据规范

- 模拟并发**上限 2**（429 退避）；长跑脚本**必须可断点续跑**（os.path.exists 跳过 + 台账去重）。
- 轮询限速 ≥1.3 秒/请求（60 请求/分钟限流；高频打 corr 端点会被 RST）。
- **终端一律 PowerShell**（Bash 工具 PATH 损坏，exit 127 静默失败）；前台 stdout 空捕获时让 python 写文件再读；PowerShell 重定向显式 `-Encoding utf8`。
- 台账读用 `utf-8-sig`（首列 BOM）；id 在第 0 列、S=`row[2]`、F=`row[3]`，别拿 Fitness 当 Sharpe。
- Retry-After 退避 `min(ra, 15~20)`；认证请求必须带重试（偶发 ProxyError/SSL EOF）。

## 8. 目录与放置规则

> 完整目录布局以会话内项目结构快照与 `git ls-files` 为准，本节只管**往哪放**。

- 台账：`data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`（唯一事实源，只追加）；模拟 json 落 `data/alpha_quality_analysis/mined/`。
- 方法论结论**只写** `docs/methodology/00_总纲.md`（带日期；推翻旧结论明写"已推翻+日期"）；`docs/methodology/01~06` 是历史附录，只读不改。
- 新批次配方一律加进 `src/mine/specs.py`（build_wNNN 函数，经 `gen_combos.py` 统一入口跑），**禁止新建独立 mine_wNNN 脚本**。
- 过程日志与一次性脚本落 `_autologs/`（git 忽略，不进版本历史；需长期保留的搬 `src/` 对应模块）。
- **禁止根目录新增任何文件**；`src/` 下脚本必须自带项目根定位（向上找 `brain_credentials.txt` 后 `os.chdir`）。
- **specs 迁移纪律（0926 定）**：老批次脚本删除前必须 ① specs 输出 == 原文输出逐字节比对（当前数据下重跑两边 diff）；② 腿名解析语义保真——w200 系传 `alias=`、w204/w205 传 `plain8=False`、w210 系传 `extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False`（L_int 本名 e7b76jRO 与映射 x180_leg_int XgbQZkp1 是两个 id，顺序不可颠倒）。

## 9. 常用命令与版本控制

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

- **远端**：`origin` = `https://github.com/jslijb/worldQuantAlpha.git`（**Public**，李工 0915 确认），分支 `main`；origin 换仓库必须重新确认可见性。
- **凭据保护双重防线**：`.gitignore` + `.git/hooks/pre-commit`。禁止 `git add -f` 加凭据、禁止 `--no-verify`。
- **回滚**：`git checkout <hash> -- <路径>` 取回单个文件。全量备份：`D:\Python\worldquant_backup_20260915\`（勿删）。

### git 提交纪律与代码整洁（李工 0926 定）

- **改完必提交**：任何代码 / 文档 / 台账改动完成即跑 `git_snapshot.py --allow-public` 落库。禁止"攒一批再交"。
- **提交前先清理（三条不过不准提交）**：
  1. **去重**：功能相同的脚本合并为一个；同类批次脚本归并成参数化入口；版本迭代脚本只留最新版（禁止 v2/v3 双版本共存）。
  2. **提公共**：多处复用的代码段（平台请求 / 判分 / 台账读写 / 指标计算）抽成 `src/core/` 下的函数或类，禁止复制粘贴。
  3. **不入库一次性脚本**：`_autologs/` 的探索性 / 临时脚本不进版本历史；已被跟踪的历史文件择机 `git rm --cached` 清理。
- **结构红线**：`src/` 严格按现有分层（mine / submit / analysis / core / ops / tools / pull）归类；禁止在根目录或 `_autologs/` 随手丢新文件。

## 10. 平台硬约束速查（细节与完整判死表 → 总纲 §2）

| 约束 | 内容 |
|---|---|
| 并发模拟 | 上限 2，超 429 |
| API 限流 | 60 请求/分钟；批量预检必须限速 + 退避 |
| 字段类型 | `fnd6_*` 明细多为 VECTOR（divide 不支持事件输入），选字段按 `type=MATRIX` 过滤 |
| `_v1300` 字段 | delay=0 不可用 |
| neutralization 可用值 | NONE / MARKET / SECTOR / INDUSTRY / SUBINDUSTRY（风险中性化全轴 400，0916 判死） |
| 判决机制 | 判决 4~9 秒出；403+is.checks = 判决书；**FAIL 才是拒信**；对手明细在 `is.selfCorrelated.records`；`correlations/self` 端点弃用（200 空 body），corr 自己拉 PnL 算 |
| 本地 corr | pnl 先差分；池子只取自台账；缓冲线 0.685 |

## 11. 快速导航

| 想知道什么 | 看哪 |
|---|---|
| 当前有效打法 / 判死维度 / 参数标定 / 评分机制 | `docs/methodology/00_总纲.md`（唯一事实源） |
| 提交判决机制 / 假判决 / 踩坑记录 | 总纲 §5、§6 |
| 某个旧结论哪来的 | `docs/methodology/01~06`（历史附录，证据链） |
| 台账 / 未提交候选 | `data/alpha_quality_analysis/` |
| 历史表达式 | `src/archive/expr_library.py` |
| 备考/面试材料 | `docs/exam/`、`docs/study/learn/`（先看 `00_归档索引.md`） |
| 研报移植记录 | `docs/research/` |
