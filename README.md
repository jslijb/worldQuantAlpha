# WorldQuant BRAIN Alpha 挖掘项目

通过 WorldQuant BRAIN 平台 API 批量挖掘、验证、提交 Alpha 因子。

## 快速开始

```bash
PY="D:/ProgramData/Miniforge3/envs/bigmodel/python.exe"

$PY src/submit/probe_corr_service.py     # 1. 探测平台相关性服务状态
$PY src/submit/submit_v2.py auto w114_   # 2. 提交指定前缀的达标候选
$PY src/tools/summarize_mined.py         # 3. 汇总挖矿结果
```

## 核心口径

| 项 | 标准 |
|---|---|
| 高质量因子 | S+F ≥ 4.0 **且** testS ≥ 1.25 **且** checks 无 FAIL |
| 提交闸门 | 上述质量关 + corr 预检（max corr<0.7，或候选 S ≥ 1.10×热对手 S） |
| 每日目标 | 5 个（下限），历史欠账顺延 |
| 当前瓶颈 | **相关性墙**——历史上 1098 条模拟里 460 条质量达标，卡在"彼此太像" |

## 目录结构

```
worldquant/
├── CLAUDE.md              ★ 项目规范源（AI 工具先读这里）
├── README.md              本文件
├── brain_credentials.txt  平台凭据（已 git 忽略，不入库）
├── .gitignore             git 忽略规则
├── .gitattributes         换行符/二进制处理
│
├── src/                   ★ 全部代码
│   ├── core/              公共库（utils、AlphaSimulator）
│   ├── submit/            提交器 + corr 探针 + 预检
│   ├── mine/              当前挖矿批次
│   ├── ops/               运维脚本
│   ├── tools/             分析工具
│   └── archive/           expr_library.py（历史表达式库）
│
├── data/                  ★ 全部数据
│   └── alpha_quality_analysis/
│       ├── SUBMITTED_LEDGER.csv   ★ 台账（唯一事实源）
│       ├── mined/                 1098 个模拟结果
│       └── candidates_*.csv       候选清单 / 未提交达标候选 / 单腿价值排行
│
├── docs/                  ★ 全部文档
│   ├── methodology/       挖矿方法论（6 个子目录）
│   ├── research/          论文/研报移植
│   ├── study/             学习材料
│   ├── exam/              备考与考试资料
│   ├── project/           平台规则与工程文档
│   ├── reference/         官方 PDF 与知识图
│   └── archive/           过时文档
│
└── _autologs/             运行日志
```

## 先看这几篇

- **想挖新因子** → `docs/methodology/01_骨架与配方/01_黄金骨架库.md` + `02_参数与设置/01_参数甜点表.md`
- **模拟结果挂 FAIL** → `docs/methodology/04_失败模式/01_checks_FAIL全解.md`
- **提交撞相关性墙** → `docs/methodology/03_过墙与提交/01_相关性墙破法.md`
- **想捡历史的低分因子回来改造** → `docs/methodology/05_历史因子复盘/02_低质量因子升级动作.md`
- **要现成的达标候选** → `data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv`
- **想知道历史上跑过哪些表达式** → `src/archive/expr_library.py`

完整文档索引见 `docs/README.md`。

## 版本控制

项目已用 git 管理，分支 `main`，远端 `origin` 指向 GitHub 仓库。**提交后自动推送。**

```bash
$PY src/ops/git_snapshot.py              # 自动识别变更 → 提交 → 推送远端
$PY src/ops/git_snapshot.py --dry-run    # 只看将要提交什么，不真提交
$PY src/ops/git_snapshot.py --no-push    # 只提交本地，不推送
git log --oneline                        # 查看提交历史
git status --short                       # 查看未提交改动
```

**提交约定**：每挖完一批 Alpha 提交一次，每完成一轮提交/文档改动提交一次。脚本自动生成提交信息（形如 `mine(w122): 新增 9 条候选 / 台账 +3`），无变更时静默跳过、不产生空提交。

**⚠️ 公开仓库拦截**：本项目含 1098 条 alpha 表达式与提交台账，属核心资产。脚本推送前会探测远端可见性，**检测到公开仓库即拦截**并告警；确需公开要显式加 `--allow-public`。

**凭据安全**：`brain_credentials.txt` 由 `.gitignore`（主防线）+ `.git/hooks/pre-commit`（二次拦截）双重挡住，永不入库。

**不进版本库**：凭据、工具缓存、运行日志（`*.log`）、`.workbuddy` 除 `memory/` 外的部分。

## 环境

- Python：`D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`（conda 环境 bigmodel）
- 并发模拟上限 **2**（平台限制，超过报 429）
- 运行脚本必须在项目根目录（脚本自带根定位代码，可直接从任意位置调用）

---

*最后重构：2026-09-15。规范以 `CLAUDE.md` 为准。*
