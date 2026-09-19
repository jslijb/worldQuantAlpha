# CLAUDE.md — WorldQuant BRAIN 项目工作规范

> 本文件只保留**红线、执行纪律、流水线口径、目录与命令**。
> **挖矿方法论（有效打法 / 判死维度 / 参数标定 / 判决机制 / 踩坑记录）的唯一事实源 = `docs/methodology/00_总纲.md`**，细节一律看总纲，不在本文件重复。
> 最后瘦身：2026-09-19（方法论细节移交总纲；冗余脚本清理，见变更记录）。

---

## 0. 这个项目在做什么

用 WorldQuant BRAIN 平台 API 批量挖 Alpha 因子、过质量闸门与相关性闸门、提交并记账。

| 项 | 内容 |
|---|---|
| 目标 | 每日 5 个高质量 Alpha（下限）+ 历史欠账；累计 100 个提交解锁 Super Alpha；Rank 进前 100 |
| 高质量定义 | S+F ≥ 4.0（IS Sharpe + IS Fitness）**且** tS ≥ 1.25（验证期不崩）**且** checks 无 FAIL |
| 真正的瓶颈 | **相关性墙**（详见总纲 §1、§2） |
| 运行环境 | Python `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（conda 环境 bigmodel） |
| 凭据 | `brain_credentials.txt`（项目根，JSON 格式；已 git 忽略，永不入库） |

**流水线口径（2026-09-17 起）**：
1. leg_lab 离线生成候选（阈值 `--max-corr 0.55~0.57`，它只是生成器不是判决器）
2. `pnl_corr.py` 实测复核，**本地 ≤ 0.685 才可提交**（缓冲线）
3. `submit_v3.py` 提交——**出现 FAIL 才是拒信**，无 FAIL 只记 UNKNOWN 不记 REJECTED
4. 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` **只追加**；池子只取自台账
5. 质量闸门、豁免线（1.10 × max(corr≥0.7 对手的 S)，S 取台账 row[2]）、判决机制、偏移定律 → **总纲 §3、§5**

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
