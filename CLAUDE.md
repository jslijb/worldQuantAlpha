# CLAUDE.md — WorldQuant BRAIN 项目工作规范

> 本文件是项目的**唯一规范源**。任何 AI 工具/协作者动手前先读这里。
> 最后重构：2026-09-15（1900 个散乱文件 → 分层结构，历史脚本经验已提取后清除）
> **维护约定见第 4 节——本文件需要持续更新，不是一次性的。**

---

## 0. 这个项目在做什么

用 WorldQuant BRAIN 平台 API 批量挖 Alpha 因子、过质量闸门与相关性闸门、提交并记账。

| 项 | 内容 |
|---|---|
| 目标 | 每日 5 个高质量 Alpha（下限）；累计 100 个提交解锁 Super Alpha；Rank 进前 100 |
| 高质量定义 | S+F ≥ 4.0（IS Sharpe + IS Fitness）**且** testS ≥ 1.25（验证期不崩）**且** checks 无 FAIL |
| 真正的瓶颈 | **相关性墙**——不是质量（历史 1098 条里 460 条达标），是"合格因子彼此太像" |
| 运行环境 | Python `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（conda 环境 bigmodel，已装 requests/pandas/matplotlib/reportlab） |
| 凭据 | `brain_credentials.txt`（项目根，JSON 格式 `["user","pass"]`） |

---

## 1. 目录规范（强约束）

```
D:\Python\worldquant\
├── CLAUDE.md                  ← 本文件（规范源，AI 工具固定读）
├── README.md                  ← 项目入口概览
├── brain_credentials.txt      ← 凭据（脚本按相对路径读，不要移动；★已 git 忽略，永不入库）
├── .gitignore                 ← git 忽略规则（凭据/缓存/日志；.workbuddy 只留 memory）
├── .gitattributes             ← 换行符与二进制处理（文本统一 LF 入库）
│
├── src/                       ★ 全部 Python 代码只在这里
│   ├── core/                  utils.py（登录/取字段）、AlphaSimulator.py（并发模拟器）
│   ├── submit/                submit_v2.py（★提交器）、probe_corr_service.py（★corr 服务双探针）、precheck_only.py
│   ├── mine/                  mine_batch120.py、mine_batch121.py（当前活跃挖矿批）
│   ├── ops/                   git_snapshot.py（★挖矿/提交后的统一快照提交入口）、
│   │                          auto_submit_loop.py（自动重试循环，当前停用）
│   ├── tools/                 指标计算、结果汇总、字段抓取、本轮重构工具
│   └── archive/               expr_library.py（★历史表达式库，见下）
│
├── data/                      ★ 全部数据只在这里
│   └── alpha_quality_analysis/
│       ├── SUBMITTED_LEDGER.csv        ★ 台账，唯一事实源
│       ├── mined/                      1098 个模拟结果 json
│       ├── candidates_all.csv          1098 条结构化清单（含 S/F/T/tS/FAIL/band）
│       ├── candidates_unsubmitted_qualified.csv  456 条未提交达标候选
│       ├── leg_value_rank.csv          207 条单腿价值排行
│       └── *_matrix.json               字段清单（fnd6 / analyst4）
│
├── docs/                      ★ 全部 Markdown 文档只在这里
│   ├── methodology/           挖矿方法论（01_骨架与配方 / 02_参数与设置 / 03_过墙与提交 /
│   │                          04_失败模式 / 05_历史因子复盘 / 06_打法手册）
│   ├── research/              外部论文/研报移植记录
│   ├── study/                 学习材料（零基础四课、进阶指南）
│   │   └── learn/             ★ 平台 Learn 归档（`00_归档索引.md` = 总入口/官方结构↔本地对照）
│   │                          ├── docs/          官方 documentation 全文（29 页，按官方课程分目录）
│   │                          │   ├── NN_<课程id>/MM_<页面id>.md
│   │                          │   ├── images/<页面id>/    该页配图
│   │                          │   └── README_官方文档结构.md  逐页清单
│   │                          ├── 视频合集_*.md   视频课程（一个课程组合并一个文件）
│   │                          ├── 课程视频总表.md  16 课程组 / 69 视频全量清单
│   │                          └── _手稿存档/      早期手工粘贴稿（已被官方原文取代）
│   ├── exam/                  考试与备考资料（含 images/ 截图）
│   ├── project/               平台规则、SDD 工程文档、数据集参考、报告
│   ├── reference/             官方 PDF + 知识图（images/）
│   └── archive/               过时文档
│
└── _autologs/                 运行日志（临时产物，可随时清理）
```

### 放置规则（新增文件时照此归位）

| 新增什么 | 放哪 | 说明 |
|---|---|---|
| 新挖矿脚本 | `src/mine/mine_batch{NNN}.py` | 编号递增，不复用旧编号 |
| 新提交/预检脚本 | `src/submit/` | 提交逻辑一律走 `submit_v2.py`，不要另起炉灶 |
| 一次性分析/维护脚本 | `src/tools/` | 用完可留档 |
| 模拟结果 json | `data/alpha_quality_analysis/mined/` | 脚本产出直接落这里 |
| 新方法论文档 | `docs/methodology/{已有子目录}/` | 子目录按主题，不新建顶层目录 |
| 论文/研报移植记录 | `docs/research/` | 命名 `{来源}_{主题}.md` |
| 备考/考试材料 | `docs/exam/` | 截图放 `docs/exam/images/` |
| 平台 Learn 文档页 | `docs/study/learn/docs/<NN>_<课程id>/<MM>_<页面id>.md` | **一页一文件，按官方课程目录分层**；`fetch_learn_docs.py all` **全量抓取**（幂等可重跑），`page <id>` 抓单页；**原文照录、不改写**；配图落 `docs/images/{page_id}/` |
| Learn 视频课程译文 | `docs/study/learn/视频合集_课程名.md` | **一个课程组合并成一个文件**（`merge_video_notes.py`）；字幕走 `/video-courses` 接口取，**不下载视频**；全量清单见 `课程视频总表.md` |
| 手工粘贴的 Learn 材料 | `docs/study/learn/_手稿存档/` | 官方原文到位后移入此处，**不再新增**；主目录只留官方归档 |
| 过程日志/临时文件 | `_autologs/` | 不要落根目录 |

**禁止**：根目录新增任何 .py / .md / 数据文件（除本文件、README.md、brain_credentials.txt）。

### 路径写法约定
`src/` 下的脚本**必须自带项目根定位**（因为脚本不在根目录了）：

```python
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
```

之后所有相对路径（`brain_credentials.txt`、`data/alpha_quality_analysis/mined`）照常工作。

---

## 2. 代码规范

- 全部代码集中在 `src/`，**不再往根目录放脚本**。
- 新脚本一律加第 1 节的根定位代码块。
- 模拟并发**上限 2**（超过报 `429 CONCURRENT_SIMULATION_LIMIT_EXCEEDED`），必须 `max_workers=2` + 429 退避重试。
- 长跑脚本必须**可断点续跑**：产出用 `os.path.exists` 跳过、提交前用台账去重。
- 后台命令约 2 分钟会被截断，长任务用 `run_in_background` 或分片。
- 轮询限速：`<1.3 秒`高频打 corr 端点会被服务器 RST（WinError 10054）；间隔不低于 `Retry-After`，并捕获 `ConnectionError`。

---

## 3. 数据规范

- **`data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` 是唯一事实源**。所有"提交了几个"的问题以此为准。
- 台账**只追加，不删除、不覆盖**。追加时用 `utf-8-sig` 读（首列带 BOM，否则 `DictReader` 的 id 键全空、去重失效——0913 翻车过一次）。
- 时间口径：`dateSubmitted` 自带 `-04:00`，美东时间。**北京 12:00 = 美东 00:00**；北京 03:00 ≈ 美东前一天 15:00。
- 模拟结果 json 落 `mined/`，文件名 `{批次}_{序号}.json`（如 `w121_d.json`）。

---

## 4. 文档规范与维护约定

### 本文件（CLAUDE.md）什么时候必须更新
1. **目录结构变了**（新增/移动/删除顶层目录或子目录 → 同步第 1 节树形图）
2. **新增了归位规则**（某类文件该放哪 → 同步第 1 节表格）
3. **平台约束发生变化**（并发上限、字段权限、API 行为 → 同步第 6 节）
4. **出现新的术语译法**（→ 同步第 7 节）
5. **红线变化**（→ 同步第 8 节）
6. 维护完在文件末尾「变更记录」追加一行。

### 方法论文档什么时候必须更新
- 跑完一批实证（≥5 条候选）→ 把结论补进 `docs/methodology/` 对应文件
- 有新发现推翻旧结论 → **必须显式标"修正 X 月 X 日结论"**，不要悄悄改
- 文档里所有数字必须能对应 `data/` 下的 CSV，禁止凭印象写计数

### 写作要求
- 结论必须有实证来源（写清批次号、样本数、对照条件）
- 区分"已验证"与"未验证"，未验证的标明"未实测"
- 不用自造术语；量化术语按第 7 节译法

---

## 5. 常用命令与版本控制

```bash
PY="D:/ProgramData/Miniforge3/envs/bigmodel/python.exe"

# 探测平台自相关服务是否恢复（双探针，必做前置）
$PY src/submit/probe_corr_service.py

# 提交某个前缀的达标候选（自动去重 + 质量过滤 + corr 预检 + 提交 + 记账）
$PY src/submit/submit_v2.py auto w114_

# ★ 提交并读「对手明细表」（推荐：先测 corr，再决定要不要真交）
$PY src/submit/verdict_dump.py <alpha_id> <cid>   # 落盘 _autologs/verdict_{id}.json + 打印对手表

# ★ 批量扫提交（把提交当 corr 测量仪；一次一个、串行、被拒无副作用）
$PY src/submit/corr_probe_sweep.py --file _autologs/sweep_list.txt

# corr 预检不可用时改走盲提交（一次一个；PENDING 即停手防互堵）
$PY src/submit/blind_submit.py <alpha_id> <cid>

# ★★ 本地算 self-corr（0916 新增，筛选成本归零，**发提交之前一律先跑这个**）
$PY src/analysis/pnl_corr.py <cid|alpha_id> [--top 8] [--refresh]
$PY src/analysis/pool_diag.py pool                 # 全池互相拥挤度：谁最"与众不同"
$PY src/analysis/pool_diag.py near <alpha_id>      # 某条的最近邻明细
$PY src/analysis/pool_diag.py matrix <id...>       # 指定几条的互相关矩阵
$PY src/analysis/screen_unsubmitted.py             # 把 456 条历史积压候选全量筛 corr
$PY src/analysis/leg_lab.py check                  # 验 PnL 线性性（预测 vs 实测）
$PY src/analysis/leg_lab.py pair                   # 腿两两互相关
$PY src/analysis/leg_lab.py eval "L_pst:1.5, P_tr20:1.5"
$PY src/analysis/leg_lab.py search --min-s 2.1 --max-corr 0.67

# 只读 corr 预检（绝不提交/不写台账），用于实验判读
$PY src/submit/corr_only.py w122_

# 只预检不提交
$PY src/submit/precheck_only.py

# 汇总 mined 结果
$PY src/tools/summarize_mined.py

# ★ 提交并推送（每批挖矿/提交后必做，见下）
$PY src/ops/git_snapshot.py --allow-public
$PY src/ops/git_snapshot.py --allow-public "本批说明"   # 追加一行自定义说明
$PY src/ops/git_snapshot.py --dry-run                  # 只看将要提交什么，不真提交
$PY src/ops/git_snapshot.py --push-only --allow-public # 已有本地提交待推时用（本次无变更也推）
$PY src/ops/git_snapshot.py --no-push                  # 只提交本地，不推送
```

**提交判定链**：质量闸门（S+F≥4.0 & testS≥1.25 & 无 FAIL）→ corr 预检（max corr<0.7 直通；否则豁免线 = `1.10 × max(所有 corr≥0.7 对手的 Sharpe)`，候选 S 达线也可提交）→ `POST /alphas/{id}/submit` → `GET /alphas/{id}` 核 `status==ACTIVE` → 追加台账。

⚠️ **必须串行提交**：同账号并发提交会互堵（0914 实测 4 个 POST 201 后永不裁决）。同骨架变体一次只提一个（互撞率 0.82–0.95）。

### 版本控制（git）

- **远端**：`origin` = `https://github.com/jslijb/worldQuantAlpha.git`，分支 `main`。提交后自动推送（`git push -u origin HEAD`）。
- **远端可见性（0915 实测）**：该仓库是 **Public 公开仓库**。李工已于 0915 明确确认并完成首次全量推送（8 个提交 / 1342 文件），**自动化推送固定带 `--allow-public`**。
  - ⚠️ 红线：`git_snapshot.py` 对公开仓库默认拦截（退出码 4），这是防"手滑误推"的闸门。**只在已确认的 origin 上、且李工显式同意时**才加 `--allow-public`；**origin 一旦换成别的仓库，必须重新确认可见性**，不得默认放行。
  - 若日后改回 Private，`--allow-public` 对私有仓库不生效、无副作用，命令无需改动。
- **何时提交**：① 每挖完一批 Alpha（`mine_batch{NNN}.py` 跑完）② 每完成一轮提交（台账有新记录）③ 完成一批文档/代码改动。一句话——**一次有意义的产出 = 一次提交**。
- **怎么提交**：统一走 `src/ops/git_snapshot.py`，它会自动识别变更、生成提交信息、无变更时静默跳过（不产生空提交）。
- **信息格式**：自动生成，形如
  - `mine(w122): 新增 9 条候选 / 台账 +3`
  - `submit: 台账 +5 / 文档 1 项`
  - 前缀含义：`mine` 挖矿 / `submit` 提交 / `code` 代码 / `docs` 文档 / `chore` 杂项
- **凭据保护（双重防线）**：
  1. `.gitignore` 首节挡 `brain_credentials.txt`（主防线）；
  2. `.git/hooks/pre-commit` 二次拦截：文件名黑名单 + 小微文件内容检测。
- **禁止**：`git add -f` 强加凭据；`git commit --no-verify` 绕过钩子。凭据一旦进入历史对象极难清除。
- **回滚**：`git log --oneline` 看历史；`git checkout <hash> -- <路径>` 取回单个文件；`git diff` 看未提交改动。
- **不进版本库的内容**：凭据、工具缓存（`.codegraph`/`.codeartsdoer`/`.arts`/`.freebuff`）、运行日志（`*.log`）、`.workbuddy` 除 `memory/` 外的部分。
- **另有全量备份**：`D:\Python\worldquant_backup_20260915\`（0915 重构前快照，勿删）。

---

## 6. 平台硬约束（实测）

| 约束 | 内容 |
|---|---|
| 并发模拟 | **上限 2**，超过报 429 |
| 字段类型 | `fnd6_*` 明细多为 VECTOR（事件型），`divide` 不支持事件输入。选字段前按 `type=MATRIX` 过滤 |
| `_v1300` 字段 | **delay=0 不可用**（unknown variable） |
| 算子 | 共 66 个（清单 `data/alpha_quality_analysis/operators.json`）。**无** `ts_skewness`/`ts_kurtosis`（写 `ts_std_dev`，不是 `ts_stddev`） |
| analyst 权限 | 账号**无独立 analyst 数据集**，**`rating` 字段 404**。等价评级字段全在 analyst4 且全为 VECTOR，**必须 `vec_avg` 聚合** |
| coverage | USA/TOP3000/delay1 恒为 0.5，无区分度；选字段看 **alphaCount 越低越不易撞车** |
| **API 限流** | **60 请求/分钟**（响应头 `RateLimit-Limit: 60` / `RateLimit-Remaining`）。超限返回 **HTTP 429**（body 仅 22 字节）。corr 预检一条候选需轮询 **3~4 次请求**，47 条 ≈ 190 请求 → **批量预检必须限速（≥1.3 秒/请求）+ 429 退避**，否则全部超时并被误读为"服务故障"。⚠️ **0915 实测：本轮探针+预检共约 380 次 corr 端点请求，之后相关判决一直是 `PENDING`** —— 探测本身就是积压的成因之一，别再打 |
| corr 端点正确语义 | `200 + Retry-After + 空 body` = **平台正在现算，须继续轮询**，**不是故障**。⚠️ **0915 二次修正**：当前实际状态是**相关计算在账号侧排队积压**，90~180 秒量级的连续轮询（实测 51 次/90 秒、180 秒预算）**都拿不到 records**，且**全程零 429**（所以也不是限流封禁）。`_autologs/corr_ready_0915.txt` 一次性快扫为空 = 一条算好的都没有 |
| **★ 提交判决机制（0916 定案）** | **判决 4~9 秒就出，不存在排队积压**。`POST /alphas/{id}/submit`（201）→ 轮询 `GET /alphas/{id}/submit`：`200+Retry-After+空 body`=计算中（约 4 秒）；**`403 + {"is":{"checks":[...]}}` = 判决书**（含 SELF_CORRELATION 数值）；alpha 变 ACTIVE = 入池。旧 `blind_submit.py` 只认顶层 status/stage 键，**把判决书当空数据丢弃** → 0914~0915 的"假 PENDING/积压"全部由此而来；判决过期后端点 404，重 POST 可再取。**提交器用 `src/submit/submit_v3.py` / `run_queue_v3.py`，别再用 blind_submit**；`correlations/self` 端点彻底弃用 |
| **⚠️ 第三种假判决：无 FAIL 的 403 回执被误判为"被拒"（0916 晚，QPbP6aRQ 实测）** | submit 端点的 403 body 里，checks 可能**带 PASS 与数值、却一条 FAIL 都没有**——那是"检查已跑完且都过"的回执，alpha 几秒后变 ACTIVE。旧逻辑「有 result 就算判决 → REJECTED」把它误判成拒信，**导致一条真入池的 alpha 漏记台账、裁决档案留错档**（QPbP6aRQ 实际 ACTIVE/selfCorr=0.6949，却记成 REJECTED）。**唯一正确判据 = 出现 `FAIL` 才算拒信**；无 FAIL 一律继续轮询等 ACTIVE，等到超时也只记 `UNKNOWN`、不记 REJECTED（已修入 submit_v3.py）。附带修正：selfCorr **不论 PASS/FAIL 都要取值**（旧版只在 FAIL 分支里取 → 台账 corr 常为空） |
| **★★ 判决书里的对手明细表（0916 PM 发现）** | `403` 判决体除 `is.checks` 外还有 **`is.selfCorrelated.records`**，逐条列出撞到的每个 alpha 的 **id / correlation / sharpe**（schema: id,name,instrumentType,region,universe,correlation,sharpe,returns,turnover,fitness,margin）。→ **豁免线 = 1.10 × max(所有 corr≥0.7 对手的 S)，必须逐条算**。实测 w132_h 撞 4 条：kqoq0zed .9339/2.02、6Xr2eQaJ .7544/2.27、akLp3pzW .7031/2.78、e79PvPpE .7016/3.13 → 线取 3.443（**单个低 S 对手救不了**）。工具 `src/submit/verdict_dump.py`。**提交即测量**：一次 POST（3~5 秒）拿到完整对手表 |
| **★ 质量与相关性同源（0916 实证）** | 引擎腿 `ts_av_diff(cash/*,45)` + `ts_av_diff(cashflow_op/*,45)` **既是质量引擎也是相关性来源**：加回 → SF 3.85→4.30 但 corr 0.6999→**0.961**；去掉 → SF 掉到 3.38~3.50。当前前沿 = **SF 4.11 ↔ corr 0.7993**（w141_a，7 腿骨架 + /cap）。另：**aC<30 无数据"只对 fnd6 极冷字段成立**——`fundamental2` 的 `authorized_stock_buyback_amount`（**aC=8**）有效，是池内最强 `0mR2K6lr` 的核心腿 |
| `neutralization` 取值 | 可选 `NONE` / `MARKET` / `SECTOR` / `INDUSTRY` / `SUBINDUSTRY`；**`STATISTICAL` 不可用**（提交报 400 "Neutralization STATISTICAL is not available"） |
| **★★★ 风险中性化全轴判死（0916 晚实测，一次探针）** | 逐个 POST 探测：`SLOW_AND_FAST` / `SLOW` / `FAST` / `CROWDING` / `STATISTICAL` 全部 **400 "Neutralization X is not available."**；`RAM` 是 **400 "not a valid choice"**（连取值都不合法）。→ **PPA/PPAC 要求的"风险中性化之一"本账号一个都没有**，PPAC 通道对本账号关闭（且 PPAC 另有"唯一字段 ≤3、算子 ≤8"门槛，我们的 4~6 腿表达式本就不符）。**"Slow+Fast 中性化"这条从 0914 就挂着的"保命杠杆"到此正式判死，不必再试。** 可用的投影维度只有 `NONE / MARKET / SECTOR / INDUSTRY / SUBINDUSTRY` 五种分组型 |
| **★★★ 区域轴判死：本账号 USA 单区（0916 晚实测）** | 逐个 POST 探测：`ASI`(MINVOL1M) / `EUR`(TOP2500) / `GLB`(TOPDIV3000) / `HKG`(TOP800) / `JPN`(TOP1600) 全部 **400 `Region X is not available.`**。<br>→ 手册里"同一 alpha 在 USA corr 0.85、到 EUR 可能 0.6"这条**多区域破墙路走不通**（账号无权限）。**76 条已提交全是 USA，不存在"另一个空池"**。<br>→ **结论：可开采的维度只剩 USA 内的表达式本身。** |
| **★ 提交通道核实（0916 晚）** | ① `GET /alphas/{id}/check` 可用（已提交的返回 `ALREADY_SUBMITTED: FAIL`）；② **`GET /alphas/{id}/submit` 在 alpha 变 ACTIVE 后仍返回 200 + 完整 8 项 checks**（含 `value`/`limit`），是读回真实判据的口子；③ **检查项里没有 `REGULAR_SUBMISSION`** —— 流传的"每日最多 4 个 Regular Alpha"对本账号不生效（0916 当日实际入池 16 条全 ACCEPTED）。8 项 = LOW_SHARPE / LOW_FITNESS / LOW_TURNOVER / HIGH_TURNOVER / CONCENTRATED_WEIGHT / LOW_SUB_UNIVERSE_SHARPE / SELF_CORRELATION / MATCHES_COMPETITION |
| **★★★ 破墙维度总表（0916 晚收官，逐项实证）** | **已判死**：<br>① 换字段/换锚（`/cap` 归一成市值因子，batch155 换 4 个全新 fnd6 仍 0.78）<br>② 换区域（本账号 USA 单区，全部 400）<br>③ 风险中性化 Slow+Fast / STATISTICAL / CROWDING / RAM（全部 400）<br>④ PPA/PPAC 通道（要求风险中性化 + 唯一字段≤3，本账号双不符）<br>⑤ 换 universe TOP1000/500、truncation、delay D0（早期已证伪）<br>⑥ 结构级改造（隔夜/日内拆分、条件符号切换、换手距离，batch104 质量崩 SF 0.11~1.15）<br>⑦ 新数据轴单独成腿（option9/model51/news18/pv13 单腿 SF 1.1~3.4，加进组合压不下 corr）<br>⑧ vec_avg 分析师评级轴（SF ≤0.88）<br>⑨ 456 条历史积压（最低 corr 0.6934，无一直通）<br>**有余量但会饱和**：<br>⑩ 中性化投影（−0.14~−0.27 一次性下移，**一个几何吃 1~2 口就满** —— MARKET 池被 `levpXXGl`/`YPbLZK2W` 占住后，后续 MARKET 候选接 0.71~0.88）<br>⑪ 换分组粒度（单腿 corr 改善 ~0.17，但低相关空间未打开）<br>**唯一还开着**：<br>⑫ **USA 内发现新的"高质量单腿"字段**（当年 fnd6_xrent / cashflow_op 就是这么破的）—— **0917 已关闭**：option8/socialmedia12/model16/news12（b165/b166）与 analyst4 全量二扫（PEAD 4 包装 + 0 阶 30 字段 + 覆盖数延伸，b177）全部不出种子 → **可及 14 个数据集已全部测绘完毕**<br>**0917 新增判死**：<br>⑬ 腿稀释量产（单腿 ≈−0.02；双腿 −0.08~+0.11 符号不定、加通用价量腿反而更像池子质心；赢家 gJbkQ31Q 进池即成头号撞点——**任何腿组合必须先实测真值 corr，pred 不可外推**）<br>⑭ decay 拉大（22/32/44 对 8 条擦线候选 12/12 反升 +0.02~0.03，平滑推向池子共同慢分量）<br>⑮ 逐腿 group_rank→group_zscore / group_neutralize（14/14 质量摧毁，最好 SF 3.46）<br>**→ 本地可及空间已见底；唯一解锁路径 = 平台侧新权限（多区域 / 新数据集）** |
| **★★ 中性化设置轴 = 一次性的"救急"杠杆，不是量产杠杆（0916 晚 batch160 一手实证）** | **事实**：已提交 74 条的中性化分布 = SUBINDUSTRY 48 / INDUSTRY 26 / **MARKET 0 / SECTOR 0 / NONE 0**。换中性化 = 换 PnL 的**投影维度**，零成本、不动表达式、不加新腿。实测（6 表达式 × 3 中性化 = 18 条）：<br>**① 有效**：`d5b5voEJ`（SUBINDUSTRY，本地 corr 0.7467 卡死）→ MARKET 版 SF **4.71** / tS 1.50 / 本地 corr **0.6067** → 提交实测 **selfCorr 0.6015 ACCEPTED**（降 0.14）。<br>**② 无效**：`qMxMV8NA`→MARKET（`ZYbPGzr1`）SF 4.73/tS 1.58 但 corr **0.8274**，撞的正是新入池的 `levpXXGl`。<br>**③ SECTOR 看表达式**：`d5b5voEJ`→SECTOR SF **5.18** / tS 1.58 但 corr 0.8850（撞 levpXXGl）；`N1a18988`→SECTOR 0.6996（边缘）、`MPaPVYpM`→SECTOR 0.7552。<br>**④ NONE 全线崩**（SF 2.15~2.20 + LOW_SHARPE）→ 排除。<br>**机制（PnL 对测量已证）**：换中性化对「表达式 ↔ 池子」的相关性有 **一次下移（实测 −0.14 ~ −0.27，随表达式而异，不是固定 0.14）**——`mLmLW6E6` SUB 本地 **0.8931** → MARKET 版（`YPbLZK2W`）本地 **0.6239**（**−0.27**），提交实测 **selfCorr 0.6028 ACCEPTED**。但它**不改变表达式之间的相似度**——`d5b5voEJ` vs `qMxMV8NA` 在 SUBINDUSTRY 下**本来就 0.8492**，换 MARKET 后 0.8274（几乎不变）。<br>→ **它是"救急"工具不是量产杠杆**：只能把**原本卡在 0.70~0.78 的候选**往 0.60~0.68 推一把；**一个几何只能吃一口**（第一条 MARKET 版入池后，其余 MARKET 候选会撞它）。<br>→ **正确用法**：挑「与其他候选相似度最低」的卡死候选换中性化；一条入池后**立刻停下重测**，别整批照搬。脚本 `src/mine/mine_batch160.py`（6 卡死候选 × 3 中性化）/ `mine_batch161.py`（台账 SF≥4.5 换 MARKET）。⚠️ 与早期"INDUSTRY/SECTOR 中性化**单独用**无效"不矛盾：那条说的是**当候选筛选条件用**（不动信号） |
| `data-fields` API 参数 | 正确写法：`/data-fields?instrumentType=EQUITY&region=USA&delay=1&universe=TOP3000&limit=50&dataset.id=<ds>&offset=<n>`。**用 `dataset=` 会返回 `["Invalid query"]`**；`tooltip` 无 coverage 时不要依赖它 |
| **★★★ 库存：22 条"表达式达标但被 corr 全封"的候选 = 中性化轴的靶场（0916 晚盘点）** | **事实**：`_autologs/_blocked_cands.json` —— 跑出过、**SF 4.22~6.05 且 tS≥1.25 且无 FAIL**、却因 corr 从未提交的候选共 **22 条**（w162/w164/w165/w166 四批），本地 corr 全在 **0.7065~0.8931**（中位 0.76）。**它们全是 SUBINDUSTRY**，所以全部可做中性化转换。<br>**换算判据**：目标 = 把 corr 压到 ≤0.68。下移量实测跨度 −0.14~−0.27 → **corr ≤0.77 的那批（约 15 条）有较大把握**，≥0.82 的那批需靠 SECTOR/all 运气。<br>**产出脚本**：`src/mine/mine_batch162.py`（22 表达式 × MARKET/SECTOR = 44 条）；**批量判决+提交** `src/submit/auto_submit_passers.py '<glob>' --min-sf 4.0 --min-ts 1.25 --max-corr 0.685 --limit N`（每成功一条就重算池子，自动绕开刚入池的）。<br>⚠️ **一个表达式只吃一口**：MARKET 版入池后，同表达式的 SUB/SECTOR 版必然被它撞死（实测 0.89~0.95）——扩产只能靠 **更多不同表达式** |
| **★★★ 腿库饱和的定量证据 + 近门槛簇（0916 晚二轮，一手实测）** | **① 饱和已到顶**：池子 76 条（唯一）已把「**fnd6 锚 + /cap\|/assets 缩放 + 现有价量腿几何**（`-ts_rank(returns,5/10/20)`、`-ts_mean(abs(returns)/volume,20)`、`-ts_delta(close,20)`、`volume/ts_mean(volume,60/120)`）」这一族吃干。实测：`x162_*` 中性化变体 **12/12 撞墙**（corr 0.6864~0.8771，撞的全是 0916 新入池的 `levpXXGl`/`kqoq0zed`/`QPbP6aRQ`/`YPbLZK2W`/`mLmwpAKK`/`pwRwWoJ3`）、`w166_*` **2/2 撞墙**（0.7223 / 0.8392）。→ **只要新候选还在这套几何里，corr 必 ≥0.686，加中性化也救不动**。<br>**② 近门槛簇**：同一族的本地 max corr 密集落在 **0.6864~0.6928**（距直通线 0.685 只差 **0.0014~0.008**）——说明差的是"一点点构成差异"，而不是方向错。定向抢救走「**加第 5 条腿稀释**（第 5 腿必须用池里没有的几何）」+「**换缩放基准**（/cap → /sales、/revenue、/ebit，分母替换是李工已验证的 #1 杠杆，池子 76 条全是 /cap\|/assets）」两条合并。<br>**③ 四个外部数据集判死（f165 28 条 + f166 12 条单腿）**：`option8`（历史/Parkinson 波动率，SF 0.09~0.23）、`news12`（SF −0.48~0.87）、`model16`（全部 **S≈−0.87**，是一个整体负向因子，翻转后也弱）、`socialmedia12`（12 个 MATRIX 字段 SF −0.21~1.10）→ **四条轴关闭，不要再建字段发现批**。<br>**④ 唯一还值得挖的**：`analyst4`（**1105 个 MATRIX 字段**，无需 vec_avg，覆盖率 0.86~1.0）—— 池子里只用了 4 个评级字段，「**预期分歧度 `(high-low)/\|mean\|`**」「**预期修正 `ts_av_diff(mean,45)`**」「**覆盖机构数变化 `ts_av_diff(number,45)`**」三条几何池内**零条**，是本轮唯一新开的方向（`src/mine/mine_batch171.py`）。 |
| **★ `auto_submit_passers.py` 标准用法（0916 晚固化）** | `python src/submit/auto_submit_passers.py '<mined文件glob>' --min-sf 4.0 --min-ts 1.25 --max-corr 0.685 --limit N --tag <批次名>`<br>链路：捞 mined 里过质量闸门的候选 → **按 SF 降序** → 逐条本地 corr 对池子 → 达标调 `submit_v3.py` 提交 → **每成功一条把新 id 塞回池子**（后续候选自动重判，天然避免同族扎堆）。<br>两道安全阀（缺一会误判）：① `/recordsets/pnl` 限流时按 `Retry-After` 退避重试（否则整批误报"取不到"）；② **池子取不全即 `SystemExit` 中止**（池子缺条 → corr 被低估 → 会误放行）。<br>⚠️ 它**只对池子**做判决，同一批内互相的相似度靠"提交后更新池子"隐式覆盖。 |
| 提交测试 | `selfCorrelation ≥ 0.7` 触发 Production Correlation 测试；通过 = max corr < 0.7 **或** Sharpe 比相关 alpha 高 10%（豁免线 = 1.10 × max(所有 corr≥0.7 对手的 S)） |
| **★★ 本地算 self-corr（0916 PM，筛选成本归零）** | `GET /alphas/{id}/recordsets/pnl` 返回该 alpha 的 **累计 PnL**（schema 仅 date+pnl）→ **必须先差分成日 PnL**，不差分任意两条都 0.99 相关。差分后本地算的 max corr 与平台判决值误差 **±0.02**（平台 ≈ 本地 **+0.006~+0.017**，实测 4 样本：le8EAJLO .6934→.6997；w154_b .8707→.8769；akLp3pzW .8053→.8036；kqoq0zed .6827→.6999）→ **判直通要留缓冲：本地 ≤ 0.685**。工具 `src/analysis/pnl_corr.py`。**能在不提交、不污染池子的前提下测任意候选的相关性** |
| **★★ PnL 近似线性（0916 PM）** | alpha 信号 = Σ wᵢ·group_rank(腿ᵢ)；subindustry 去均值与 decay 均为线性算子，trunc 只削尾部 → **PnL(Σ wᵢ·腿ᵢ) ≈ Σ wᵢ·PnL(腿ᵢ)**。实测：预测（锚腿 PnL + 价量腿 PnL）vs 实测 w154_b = **corr 0.9903**（预测 S 2.197 / 实测 2.140）。→ **只跑单腿建库，任意组合的 S 与 corr 离线可算**（`src/analysis/leg_lab.py`，numpy 向量化 `corr = Mmat@w / √(wᵀGw)`，260 万组合秒级）。⚠️ 算 S 必须用**原始日 PnL**（先扣均值则均值≈0、S 恒为 0）；**G 与 Mmat 必须同尺度**（都用原始 PnL），否则相关差 ~0.017 |
| **⚠️ 台账列序（易错，0916 踩过）** | `id,expr,S,F,T,R,DD,selfCorr,dateSubmitted,decay,neutralization,batch` → **S 是 `row[2]`，`row[3]` 是 Fitness**。把 Fitness 当 Sharpe 用会**把豁免线算低四成**（曾虚报 177 条"够豁免"，实际 0 条）。**豁免线的 S 一律取台账 row[2]** |
| **⚠️ PnL 线性预测会系统性低估 maxcorr（0916 晚实测，必须留余量）** | leg_lab 的线性预测（Σwᵢ·PnL(腿ᵢ)）**不是精确值**：实测「预测 PnL vs 实测 PnL」corr 只有 **0.83~0.96**（腿多/权重杂时更差），导致 **预测 maxcorr 系统性低估真实值 +0.05~+0.19（均值 ≈ +0.12）**。16 条样本：w164_01 .5989→.7510(+.152)、w164_00 .6249→.8156(+.191)、w162_07 .6516→.8064(+.155)、w164_07 .6233→**0.6746(+.051，唯一过线)**。→ **纪律：搜索阈值压到 `--max-corr 0.55~0.57`（不要用 0.65），且实跑后必须用 `pnl_corr.py` 实测复核（本地 ≤0.685）才能提交**。`leg_lab` 只是候选生成器，**不是判决器** |
| **⚠️ `POST /simulations` 负载结构（0916 晚踩过）** | 正确写法：`{'type':'REGULAR', 'settings':{...12 项设置...}, 'regular': <表达式>}` —— **`regular` 必须在顶层，不能塞进 `settings`**。塞进 settings 会返回 `400 {"settings":{"regular":["Unexpected property."]},"regular":["This field is required."]}`（batch159 首跑 24 条全灭即此因）。照 `mine_batch156/157.py` 的 `run_one` 写 |
| **⚠️ 池子只能取自台账** | 算 max corr 时**不得从 `data/alpha_quality_analysis/pnl/` 缓存目录取"池子"**——该目录混着数百条未提交候选/实验腿，混进来会**把 max corr 虚高压死**（曾把 433 条未提交候选当池子 → 搜出 0 个可用组合）。正确做法：池子 = `SUBMITTED_LEDGER.csv` 里的 8 位 id |
| **Learn 文档接口** | 平台 Learn 是**两套独立内容**：①**文档** = `GET /tutorials`（目录树，**7 课程/29 页**）+ `GET /tutorial-pages/{page_id}`（正文 `content` 块数组）；②**视频课程** = `GET /video-courses`。**`/tutorials` 无分页**：`next=None`、`offset=20` 起返回空，**29 页即全量**（已与平台 Documentation 页面的 7 个分组逐一核对：9+5+3+3+5+3+1）；正文里的 `/learn/documentation/...` 链接反查也**没有目录树外的页面**（唯一例外 `another-sample-alpha` 是官方自己的死链）。抓取脚本 `src/tools/fetch_learn_docs.py`（文档，`tree`/`page`/**`all` 全量**）/ `fetch_learn_video.py`（视频）/ `merge_video_notes.py`（同组视频合并） |
| **文档页 content 块类型** | 实测共 **6 种**（漏一种就丢内容）：`TEXT`(HTML→MD)、`HEADING`、`IMAGE`(独立块，**value.url 需登录态下载**)、`TABLE`、**`EQUATION`**(LaTeX，原样保留)、**`SIMULATION_EXAMPLE`**(表达式 + 12 项完整模拟设置)。⚠️ 图片**大多数不在 TEXT 的 HTML 里，而是独立 `IMAGE` 块**——只解析 TEXT 会漏掉绝大部分配图（0915 首轮即此坑，漏 81 张） |
| **Learn 视频字幕** | `GET /video-courses?limit=100`（需登录）直接返回官方**英文字幕**：**16 课程组 / 69 视频，50 个带字幕**（仅 `quantcepts` 组 19 个无）。**不用下载视频、不用本地语音识别**。⚠️ **接口默认只返 10 条，必须带 `?limit=100`**，否则漏掉后半程课程组（0915 曾误记为"46 视频/27 字幕"，即此因）。**`source` 标 YouTube 的视频同样直接带 `transcript` 字段——取字幕不需要访问 YouTube**；文档页内嵌的 YouTube 视频也可用 `uid` 反查本接口取字幕 |

---

## 7. 术语译法规范（量化行业习惯，禁止字面直译）

| 英文 | ✅ 正确 | ❌ 禁止 |
|---|---|---|
| Pasteurization | 池外标的置空（按池过滤） | 消毒 |
| Margin | 单位成交盈亏（PnL/成交额，bps） | 保证金 |
| Production Correlation | 在产 Alpha 相关性 | 生产相关性 |
| Instrument / Universe | 标的 / 股票池 | 工具 / 宇宙 |
| Book size | 账面规模（多空双边名义敞口，默认 2000 万） | — |
| Truncation | 单票权重上限 | 截断 / 去极值 |
| Lookback Days | 回溯窗口（天） | — |
| Fitness | 适应度（综合质量分） | 体能 |
| IS Ladder Sharpe | IS 分段夏普稳定性 | — |
| Region / Test Period | 市场区域 / 验证期 | — |

新增术语须同步维护本表，并同步 `docs/exam/备考总纲_详细版.md` 的术语对照表。

---

## 8. 红线

1. **不删除、不覆盖台账**（`SUBMITTED_LEDGER.csv`），只追加。
2. **不删除已提交的 Alpha**。
3. **考试/考核进行中不提供答案**——含各类限次数的准入/认证测评；"开卷"与"对方未禁用 AI"均不改变判断。只做考后复盘、考前陪练。
4. **不把不同项目的技术张冠李戴**（本工作区只做 WorldQuant）。
5. 对外动作（提交、发消息、任何不可逆操作）先确认；对内动作（读、分析、整理、写文档）放手做。

### 8.1 执行纪律（李工 0916 定，长期有效，加压条款）

6. **日目标线 = 8 条高质量**（S+F≥4.0 + tS≥1.25 + 无 FAIL）。**当日目标 = 8 + 历史欠账**。目标定下就要完成；完成不了给**根因和补救**，不给道歉。
7. **不许把活推给明天**：收尾报告里**禁止**出现"下一条路我看好 X""方向有三个"这类句子——列出的待试轴必须**当天跑完并给结论**；跑不完就说清还差什么（配额/算力/权限），不许默默顺延成"明日计划"。**一个方向只要当天开了头，就必须当天出结论（有效/无效/有效但有上限），不允许"跑了一半留到明天"。**
8. **归因平台前先自查工具**：任何"平台故障/服务不可用"结论，必须附一条自证——**我的工具在同一端点上能拿到正确结果**。前车之鉴：0915 报的"自相关服务宕机导致 434 条积压"，最终根因是自己的 `blind_submit.py` 只认顶层 status 键（**403 判决书被当空数据丢掉**）；后续发现的**三种"假判决"全是工具 bug，没有一次是平台的问题**。**先怀疑自己的代码。**
9. **每轮汇报固定四项**：**本轮提交数 / 台账总数 / 当日（美东）计数 / 剩余欠账**。缺一项视为未汇报。
10. **"不通"必须带数字**：说某个方向走不通时，必须给出量化证据（如"低相关组合 S 天花板 1.98""NONE 中性化 SF 2.15 全崩"），不许用"试了不行""效果不好"这种没有数字的句子。

---

## 9. 快速导航

| 想知道什么 | 看哪 |
|---|---|
| 三条最强骨架长什么样 | `docs/methodology/01_骨架与配方/01_黄金骨架库.md` |
| 参数该取多少 | `docs/methodology/02_参数与设置/01_参数甜点表.md` |
| 挖出来提交不了（相关性） | `docs/methodology/03_过墙与提交/01_相关性墙破法.md` |
| 模拟结果挂 FAIL 了 | `docs/methodology/04_失败模式/01_checks_FAIL全解.md` |
| 历史挖出过什么 / 还能不能用 | `docs/methodology/05_历史因子复盘/` |
| **历史上那些低分因子怎么救** | `docs/methodology/05_历史因子复盘/02_低质量因子升级动作.md` |
| 有哪些现成的达标候选没提交 | `data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv` |
| 历史上所有表达式 | `src/archive/expr_library.py` |
| 平台规则/数据集说明 | `docs/project/` |
| 备考/考试资料 | `docs/exam/` |
| 平台 Learn 文档原文（面试备考） | `docs/study/learn/`，先看 `00_归档索引.md` |

---

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-09-15 | 创建。完成项目重构：1900 个散乱文件 → 分层结构；411 个历史脚本提取经验后清除（表达式存入 `src/archive/expr_library.py`，方法论存入 `docs/methodology/`）；建立本规范文件 |
| 2026-09-15 | 纳入 git 版本控制：新增 `.gitignore`（凭据/缓存/日志不入库，`.workbuddy` 只留 memory）、`.gitattributes`（文本统一 LF）、`.git/hooks/pre-commit`（凭据拦截钩子）、`src/ops/git_snapshot.py`（统一快照提交入口）；第 5 节扩写为「常用命令与版本控制」 |
| 2026-09-15 | 钩子源文件版本化到 `src/ops/git-hooks/pre-commit`（`.git/hooks/` 不入库，换机器需按第 5 节命令重建） |
| 2026-09-15 | 关联远端 `origin` = github.com/jslijb/worldQuantAlpha；`git_snapshot.py` 增加自动推送与**公开仓库拦截**（新增 `--no-push` / `--allow-public` 参数） |
| 2026-09-15 | 首次全量推送完成（8 提交 / 1342 文件，凭据零泄漏）；`git_snapshot.py` 新增 `--push-only`（已有本地提交待推时用）；记录远端为 Public 及放行规则 |
| 2026-09-15 | 进入面试备考阶段。新增 `docs/study/learn/`（平台 Learn 文档原文分批归档：第 1 批《欢迎来到 WorldQuant BRAIN》+ 9 张配图 + 9 条外链缓存），配套 `00_归档索引.md` 登记批次与去重结论；第 1 节树形图与放置规则表同步 |
| 2026-09-15 | 发现 `GET /video-courses` 接口可直接取 Learn 培训视频的**官方英文字幕**（全量实为 16 课程组/69 视频/50 带字幕），无需下载视频或本地 ASR。新增 `src/tools/fetch_learn_video.py`；归档第 2 批《在 BRAIN 上开始的 10 个步骤》、`课程视频总表.md`；第 6 节平台约束表同步 |
| 2026-09-15 | **`introduction-alphas` 组 6/6 视频全部译完**（合计 30,107 字符字幕）。确认该组第 2~6 个视频虽 `source=YouTube`，但 `transcript` 由接口一并返回，**取字幕无需访问 YouTube**；第 6 节约束表补记该点 |
| 2026-09-15 | **打通 Learn 文档链路**：`/tutorials` 取官方目录树（7 课程/29 页）、`/tutorial-pages/{id}` 取正文（TEXT/HEADING/TABLE + 图片）。新增 `src/tools/fetch_learn_docs.py`、`src/tools/merge_video_notes.py`；归档第 3 批 `about-brain-platform`（含 2 图）；**6 个视频译文合并为 `视频合集_Alpha入门培训系列.md` 并删除单文件**；修正视频总量 **46/27 → 69/50**（此前漏带 `limit=100`）；`00_归档索引.md` 重写为「官方结构 ↔ 本地归档」对照 |
| 2026-09-15 | **官方 documentation 全部 29 页一次抓完**（`fetch_learn_docs.py all`，幂等可重跑）：88 图 / 24 个示例表达式 / 12 条公式 / 6 表格，落 `docs/study/learn/docs/` 并按官方课程分目录；**补上此前漏解析的 `IMAGE`/`EQUATION`/`SIMULATION_EXAMPLE` 三种块**（首轮只解析 TEXT 导致 81 张图全丢）；手工粘贴的 3 篇移入 `_手稿存档/`；第 1 节树形图、放置规则表、第 6 节约束表同步 |
| 2026-09-16 | **判决机制破案（0916 上午）**：所谓"排队积压"是 `blind_submit.py` 丢判决 bug——判决书是 submit 端点的 **403 + is.checks JSON**（顶层无 status/stage 键），4~9 秒即出；脚本只认顶层键 → 假 PENDING 两天。写 `submit_v3.py`（正确取判决）+ `run_queue_v3.py`（串行队列），9 条同骨架候选全部实测被拒（corr 0.7265~0.9919，落 `SUBMIT_VERDICTS.csv`）→ **w125 系 0.5 降权家族整族封死**，豁免线 3.06~3.80 无人够得着；出路 = corr<0.70 直通（真不同骨架，冷锚先验覆盖） |
| 2026-09-15 | **修正 corr 取数口径**：能确凿拿到 corr 数值的**唯一**入口 = alpha 提交成功后读 `GET /alphas/{id}` 的 `is.selfCorrelation`（w122_a `akLp3pzW`=0.8036，ACTIVE）。⚠️ 反向修正：`is.checks.SELF_CORRELATION=PENDING` 是**所有未提交 alpha 的默认占位符**，不是"正在计算"信号（5 条未触碰候选对照全为 PENDING）。`correlations/self` 在账号排队积压下 90~180 秒均返回空 body、**全程零 429**（=积压非故障、非封禁）；连续探测本身会加剧积压（本轮探针+预检约 380 次）。盲提交 `883wqwVX` POST 200/201 后 59 轮无裁决 → 复现 0914 互堵模式。第 5/6 节同步，`docs/methodology/03_过墙与提交/01_相关性墙破法.md` 增第八节 |
