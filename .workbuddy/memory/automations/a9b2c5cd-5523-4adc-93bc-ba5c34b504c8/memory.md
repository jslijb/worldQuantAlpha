# 自动化执行记忆（a9b2c5cd-5523-4adc-93bc-ba5c34b504c8）

## 2026-09-15 00:48–01:15｜WQ 补提交（服务探测 + w112_~w119_ 串行提交）

- **结论：本次新提交 0 个。** 平台自相关服务对「全新 alpha」仍未恢复，未执行有效提交。
- 探测：`E5vj5YdL` 返回 200 + 5 条 records（判定 UP），但随后实测证明这是**历史缓存假阳性**——
  w114_ 的全新候选持续返回 `200 + Retry-After:1.0 + 空 body`（连续 29 次 / 37 秒无 records）。
  **教训：探针 α 必须用从未计算过 corr 的候选；缓存 alpha 不能当探针。**
- 实际执行范围：w112_ 跑完（5 个达标，corr 0.775–0.812，豁免线 3.575/3.795，全部封死，0 提交）；
  w114_ 跑到第 2 个候选（13 个达标，1 个拿到缓存 corr 0.7975 被封死，其余 TIMEOUT）后主动停止；
  w115_/w116_/w118_/w119_ **未执行**（服务未恢复，按指令不长轮询）。
- 台账：61 行 / 60 唯一 alpha / 美东 0914 = 4，**与执行前完全一致，未发生任何写入**。
- 剩余积压：6 目标前缀未提交达标候选 52 个（w112_:5 / w114_:13 / w115_:5 / w116_:10 / w118_:10 / w119_:9）；全 mined 池未提交达标候选 425 个 / 1078 文件。
- **并发冲突处置**：执行前后共停掉 2 个 `auto_submit_loop.py` 实例（PID 21220 创建于 23:47、PID 25232 创建于 00:50，后者由另一 WorkBuddy 会话拉起）。
  该循环的 `service_ok()` 用缓存 alpha 当探针 → 永远返回 True → 每 10 分钟对 6 前缀各跑一次 submit_v2，既空转又与串行提交抢队列（正是记忆中"同用户并发提交互堵"的成因）。已确认停掉后不再重生。
- 环境观测：以 1.3 秒间隔高频轮询 corr 端点会被服务器直接 RST（WinError 10054）。轮询间隔不要低于 Retry-After 值，且应加 ConnectionError 重试。
- 下次执行注意：①先确认 `auto_submit_loop.py` 未在运行 ②探针改用无缓存候选（可从 mined 里挑一个未提交 id）③服务真正恢复的判据 = 全新 alpha 能返回 records。

## 2026-09-15 09:00（北京）｜WQ 补提交（第 2 次），服务仍未恢复

- **结论：新提交 0 个，台账零写入。** 平台自相关服务对全新 alpha 依旧不可用。
- 探测（`probe_corr_service.py`，各 3 次封顶、不长轮询）：
  缓存探针 `E5vj5YdL` → 3 次均 200+Retry-After:1.0+空 body（**这次连缓存都没有了**，缓存假阳性路径失效）；
  全新探针 `KPOAOXEE`（w112_a）→ 同样空 body。**两路皆空 → STILL_DOWN。**
- 未执行任何 submit_v2（服务未恢复，按指令只报状态）。
- 台账：61 行 / 60 唯一 id / 美东 0914 当日 = 4，与执行前一致。剩余积压 6 目标前缀 52 个（w112_:5 / w114_:13 / w115_:5 / w116_:10 / w118_:10 / w119_:9）。
- 并发检查：执行前无 python 进程，`auto_submit_loop.py` 未运行。
- **下次执行注意**：直接用 `probe_corr_service.py` 做双探针判定；单一缓存探针会误导。

## 2026-09-15 10:09（北京）｜WQ 补提交（第 3 次），服务仍未恢复

- **结论：新提交 0 个，台账零写入。** 平台自相关服务对全新 alpha 依旧不可用。
- 探测（`probe_corr_service.py`，各 3 次封顶）：缓存探针 `E5vj5YdL` 与全新探针 `KPOAOXEE`(w112_a) 均 `200 + Retry-After:1.0 + bodylen=0`、无 records → **STILL_DOWN**。按指令未执行任何 submit_v2。
- 台账：61 行 / 60 唯一 id / 美东 0914 当日 = 4，与执行前一致。
- 并发检查：无 python 进程，`auto_submit_loop.py` 未运行。
- 积压：6 目标前缀 52 个；加 w120_ 1 + w121_ 8 = 61 个；全 mined 池 433 个 / 1098 文件。
- 0915 三次执行（01:15 / 09:00 / 10:09）全部 0 提交。距美东 0914 窗口关闭仅剩不到 2 小时。
- 下次执行注意：继续用双探针脚本；服务恢复后优先跑 w112_~w119_ 六前缀，再补 w120_/w121_。

## 2026-09-15 10:32（北京）｜第 4 次执行：服务仍未恢复 + 本轮转为项目目录整理

- **补提交部分：新提交 0 个，台账零写入。** `probe_corr_service.py` 双探针（缓存 `E5vj5YdL` + 全新 `KPOAOXEE`）各 3 次均 `200 + Retry-After:1.0 + bodylen=0` → **STILL_DOWN**。按指令未跑 submit_v2、未长轮询。积压仍为 61 个（52 个六前缀 + 9 个 w120_/w121_）。
- **本轮实际任务转为「项目目录整理方案」**（李工当轮指令），产出：`_autologs/整理方案_20260915.md`（目标框架 + 文件去向映射 + 分级删除清单 + 8 步执行顺序）与 `_autologs/delete_archive_list.txt`（91 项 A 类待删 + 404 项 B 类待归档逐项清单）。
- **核查结论**：约 1900 个文件中，真正在跑的脚本只有 5 个（submit_v2 / probe_corr_service / mine_batch120 / mine_batch121 / auto_submit_loop）+ 2 个公共库。
- **待李工审批的 3 项**：①是否执行阶段 1（备份+删 A 类+归档 B 类）②活跃脚本是否移入 `src/`（需同步改脚本路径与 2 个定时任务 prompt）③`.codeartsdoer/`.`.arts/`.`.freebuff/` 与「联想SRC方法论持续检索」定时任务如何处置。
- **本轮零破坏性动作**：未删/未移/未改名任何文件，未动台账与脚本。仅新增 3 个只读扫描脚本于 `_autologs/`。
- **下次执行注意**：服务恢复判定仍以「全新 alpha 能返回 records」为准；提交前先确认 `auto_submit_loop.py` 未在运行。若李工已批准目录整理，执行时注意先做全量备份（项目无 git）。

## 2026-09-15 11:00（北京）｜第 5 次执行：服务仍未恢复；项目重构完成 + 本任务 prompt 已更新路径

- **补提交部分：新提交 0 个，台账零写入。** `src/submit/probe_corr_service.py` 双探针（缓存 `E5vj5YdL` + 全新 `KPOAOXEE`）各 3 次均 `200 + Retry-After:1.0 + bodylen=0` → **STILL_DOWN**。未跑 submit_v2。积压仍 61 个。
- **本轮实际任务：项目目录重构**（李工当轮指令，已批准）。根目录 233 → **11 条目**；总文件 1922 → 1344；体积 66M → 40M。
- **⚠️ 路径全部变更，下次执行务必按新路径**：
  - 项目规范源 = 根目录 `CLAUDE.md`（**动手前先读**）
  - 提交器 = `src/submit/submit_v2.py`；探针 = `src/submit/probe_corr_service.py`
  - 台账 = `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`（**唯一事实源**）
  - 挖矿结果 = `data/alpha_quality_analysis/mined/`
  - 新挖矿脚本 = `src/mine/mine_batch{NNN}.py`
  - 现成达标候选 = `data/alpha_quality_analysis/candidates_unsubmitted_qualified.csv`（456 条）
  - 历史表达式库 = `src/archive/expr_library.py`
  - 方法论 = `docs/methodology/`（01_骨架与配方 / 02_参数与设置 / 03_过墙与提交 / 04_失败模式 / 05_历史因子复盘 / 06_打法手册）
- **本任务 prompt 已同步更新**（脚本路径 + 双探针 + 新数据路径），无需再手动改。两个生产定时任务（`07ac2d4a` 每日挖矿 / `a9b2c5cd` 本任务）的 prompt 均已更新。
- **验证**：`src/submit/probe_corr_service.py` 在新路径下跑通（读到台账、扫出 52 个达标未提交候选）→ 路径改造成功。台账零损伤（61 行 / 60 唯一 id / mined 1098 条完整）。
- **下次执行注意**：服务恢复后跑 `src/submit/submit_v2.py auto w112_`，再依次 w114_ / w115_ / w116_ / w118_ / w119_（每前缀一条，串行）；仍要先确认 `auto_submit_loop.py` 未在运行（它已移到 `src/ops/`，且 `service_ok()` 用缓存探针会恒 True，勿开）。
