# ops_playbook.md — 运维细节手册

> 从 CLAUDE.md 移出的操作性细节（0928 瘦身）。查什么用 grep key 定位本文件对应小节；CLAUDE.md 只留红线与索引。

## 1. 常用命令

```powershell
$PY = "D:/ProgramData/Miniforge3/envs/bigmodel/python.exe"

# 本地算 self-corr（提交前必跑，直通缓冲线 0.685）
$PY src/analysis/pnl_corr.py <cid|alpha_id> [--top 8] [--refresh]

# 腿库离线拼装（候选生成器，不是判决器）
$PY src/analysis/leg_lab.py eval "L_pst:1.5, P_tr20:1.5"
$PY src/analysis/leg_lab.py search --min-s 2.1 --max-corr 0.57

# 批量判决+提交（质量过滤 -> 本地 corr -> submit_v3 -> 台账）
$PY src/submit/auto_submit_passers.py '<mined glob>' --min-sf 4.0 --min-ts 1.25 --max-corr 0.685 --limit N --tag <批次名>

# 单条提交 / 判决书 dump
$PY src/submit/submit_v3.py <alpha_id> <cid>
$PY src/submit/verdict_dump.py <alpha_id> <cid>

# git 快照（每批挖矿/提交/文档改动后必做）
$PY src/ops/git_snapshot.py --allow-public ["说明"]
$PY src/ops/git_snapshot.py --push-only --allow-public   # 推送失败重试
```

## 2. 代码与数据规范

- 模拟并发上限 2（429 退避）；长跑脚本必须可断点续跑（os.path.exists 跳过 + 台账去重）。
- 轮询限速 ≥1.3 秒/请求（60 请求/分钟限流；高频打 corr 端点会被 RST）。
- 终端一律 PowerShell；前台 stdout 空捕获时让 python 写文件再读；PowerShell 重定向显式 `-Encoding utf8`。
- 台账读用 `utf-8-sig`（首列 BOM）；id 在第 0 列、S=`row[2]`、F=`row[3]`，别拿 Fitness 当 Sharpe。
- Retry-After 退避 `min(ra, 15~20)`；认证请求必须带重试（偶发 ProxyError/SSL EOF）。
- Python 统一 `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`。

## 3. 目录与放置规则

- 台账：`data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`（唯一事实源，只追加）；模拟 json 落 `data/alpha_quality_analysis/mined/`。
- 方法论原子 → `docs/methodology/atoms.md`（唯一事实源）；`00_总纲.md` 及 01~06 为历史叙述/附录，只读不改。
- 运维细节 → 本文件。
- 新批次配方一律加进 `src/mine/specs.py`（build_wNNN 函数，经 `gen_combos.py` 统一入口跑），禁止新建独立 mine_wNNN 脚本。
- 过程日志与一次性脚本落 `_autologs/`（git 忽略）；需长期保留的搬 `src/` 对应模块。
- 禁止根目录新增任何文件；`src/` 下脚本必须自带项目根定位（向上找 `brain_credentials.txt` 后 `os.chdir`）。

### specs 迁移纪律（0926 定）

老批次脚本删除前必须：① specs 输出 == 原文输出逐字节比对；② 腿名解析语义保真——w200 系传 `alias=`、w204/w205 传 `plain8=False`、w210 系传 `extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False`（L_int 本名 e7b76jRO 与映射 x180_leg_int XgbQZkp1 是两个 id，顺序不可颠倒）。

## 4. 版本控制

- 远端：`origin` = `https://github.com/jslijb/worldQuantAlpha.git`（Public，李工 0915 确认），分支 `main`；origin 换仓库必须重新确认可见性。
- 凭据保护双重防线：`.gitignore` + `.git/hooks/pre-commit`。禁止 `git add -f` 加凭据、禁止 `--no-verify`。
- 回滚：`git checkout <hash> -- <路径>` 取回单个文件。全量备份：`D:\Python\worldquant_backup_20260915\`（勿删）。

### git 提交纪律与代码整洁（李工 0926 定）

- 改完必提交：任何代码/文档/台账改动完成即跑 `git_snapshot.py --allow-public`。禁止攒一批再交。
- 提交前先清理（三条不过不准提交）：
  1. 去重：功能相同的脚本合并；版本迭代脚本只留最新版。
  2. 提公共：多处复用的代码段抽成 `src/core/` 函数或类，禁止复制粘贴。
  3. 不入库一次性脚本：`_autologs/` 探索性脚本不进版本历史；已被跟踪的历史文件择机 `git rm --cached` 清理。
- 结构红线：`src/` 严格按现有分层（mine / submit / analysis / core / ops / tools / pull）归类；禁止在根目录或 `_autologs/` 随手丢新文件。

## 5. 平台硬约束速查

| 约束 | 内容 |
|---|---|
| API 限流 | 60 请求/分钟；批量预检必须限速 + 退避 |
| 字段类型 | `fnd6_*` 明细多为 VECTOR（divide 不支持事件输入），选字段按 `type=MATRIX` 过滤 |
| `_v1300` 字段 | delay=0 不可用 |
| neutralization 可用值 | NONE / MARKET / SECTOR / INDUSTRY / SUBINDUSTRY（风险中性化全轴 400） |
| 判决机制 | 判决 4~9 秒出；403+is.checks = 判决书；FAIL 才是拒信；对手明细在 `is.selfCorrelated.records`；`correlations/self` 端点弃用（200 空 body），corr 自己拉 PnL 算 |
| 本地 corr | pnl 先差分；池子只取自台账；缓冲线 0.685 |
| 账号拉取 | count=唯一总数口径（只读 results/next 漏 count 是顽固错型）；offset 上限 1000；过滤器写 `settings.universe=` |
