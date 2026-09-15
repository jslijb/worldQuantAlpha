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
│   │   └── learn/             ★ 平台 Learn 文档原文归档（分批收入；`00_归档索引.md` 登记批次与去重结论；
│   │                          `images/` 配图、`refs/` 外链缓存）
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
| 平台 Learn 文档原文 | `docs/study/learn/NN_文档名.md` | **原文照录、不改写**；配图 `learn_NN_*.png` 放 `images/`；每收一批同步登记 `00_归档索引.md` |
| Learn 培训视频译文 | `docs/study/learn/视频NN_标题_中英对照.md` | 字幕走 `/video-courses` 接口取，**不下载视频**；总表见 `课程视频总表.md` |
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
| **API 限流** | **60 请求/分钟**（响应头 `RateLimit-Limit: 60` / `RateLimit-Remaining`）。超限返回 **HTTP 429**（body 仅 22 字节）。corr 预检一条候选需轮询 **3~4 次请求**，47 条 ≈ 190 请求 → **批量预检必须限速（≥1.3 秒/请求）+ 429 退避**，否则全部超时并被误读为"服务故障" |
| corr 端点正确语义 | `200 + Retry-After + 空 body` = **平台正在现算，须继续轮询**（正常 3~4 次、4~6 秒即返回 records）—— **不是故障**。0915 已证伪此前的"服务停摆"结论：探针只轮询 3 次（6 秒）便放弃所致。已提交 alpha 的 `is.selfCorrelation` 一直有值，可作旁证 |
| 提交测试 | `selfCorrelation ≥ 0.7` 触发 Production Correlation 测试；通过 = max corr < 0.7 **或** Sharpe 比相关 alpha 高 10%（豁免线 = 1.10 × max(所有 corr≥0.7 对手的 S)） |
| **Learn 视频字幕** | `GET /video-courses`（需登录）直接返回官方**英文字幕**：16 课程组 / 46 视频，**27 个带字幕**（`quantcepts` 组 19 个无）。**不用下载视频、不用本地语音识别**。拉取脚本 `src/tools/fetch_learn_video.py`。**`source` 标 YouTube 的视频同样直接带 `transcript` 字段——取字幕不需要访问 YouTube，源站打不开不影响归档** |

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
| 2026-09-15 | 发现 `GET /video-courses` 接口可直接取 Learn 培训视频的**官方英文字幕**（16 课程组/46 视频，27 个有字幕），无需下载视频或本地 ASR。新增 `src/tools/fetch_learn_video.py`；归档第 2 批《在 BRAIN 上开始的 10 个步骤》、`课程视频总表.md`、`视频01_什么是Alpha_中英对照.md`；第 6 节平台约束表同步 |
| 2026-09-15 | **`introduction-alphas` 组 6/6 视频全部译完**（`视频01`~`视频06`，合计 30,107 字符字幕）。确认该组第 2~6 个视频虽 `source=YouTube`，但 `transcript` 由接口一并返回，**取字幕无需访问 YouTube**；第 6 节约束表补记该点，索引与 `课程视频总表.md` 同步 |
