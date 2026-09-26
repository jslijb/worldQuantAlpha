
## 二十五、存量回扫 + 候选队列 + b22 兄弟手术（13:20~13:55，续会话）

### 25.1 MEMORY.md 瘦身
- 27KB → 9KB：只留跨日成立的判据与结论，当日数值/榜单读数/批次明细归 daily log 与 `docs/project/`。**修正一处过期铁证**：`npdO71xw` 对池 corr 0.4806 的旧读数已作废——自家 0921 交了同族 `npdOdMdz` 后涨到 **0.8989**（换池结果随池子增长失效的实证，已写入 MEMORY §三规律三）。

### 25.2 59 条过墙候选全量回扫（对当前 114 池）
- **58 条（剔除当日已交 N1axM3mp）全部仍直通，0 条失效**。过程修了两个坑：
  - `judge_now.py` 的 id 过滤 `x[0].isalpha()` 会滤掉**数字开头的 id**（1YX/2rw8/58Qj/9qjL…共 15 条），已改 `x.isalnum()`；
  - PowerShell `*>` 重定向产出 UTF-16 被当二进制；改 `Start-Process -RedirectStandardOutput`。Bash 工具本轮多次 PATH 损坏（dirname/grep 全 127），python 一律绝对路径直调、结果落盘再 Read。
- **新工具**：`_autologs/parse_judge.py`（解析判决块→PASS/DEAD 表）、`build_queue.py`（汇总多块→QUEUE.md）、`run_judge_file.py`（从文件读 id 跑判决）、`dump_set.py`（打印 settings+指标）、`tab.py`（mined/ 结果汇总表）。

### 25.3 ★★★★ 可用候选队列 `_autologs/QUEUE.md`（Automation 直接消费）
- **A 队 16 条**过全部质量闸（tS≥1.25 + TO≤20% + 无 FAIL），按 F 降序：`blbWNYpK` 1.72 / `1YX12gvK` 1.68 / `Grb30d2Q` 1.60 / `ZY07Zw88` 1.52 / `vRr3mV5z` 1.43 / `9qVE11b2` 1.37 / `mLmzaLaE` 1.35 / `78ZjkVnZ` 1.20 …
- **前 8 条两两 corr ≤0.44（最大 0.394）⇒ 可连续 8 天各提 1 条不重样**。
- B 队 45 条直通但破质量闸（多为 tS<1.25 或 TO>20%）。
- 三条使用铁律写进 QUEUE.md：①提交当天必须重判（need 时变）；②同日 2 条先 pair_now；③按 F 降序、加交条件 = F > 当天已交均值。
- **质量天花板确认**：A 队最高 F 1.72 < 池均值 1.87；全库过墙候选 F 上限 1.84（tS 为负）。S+F≥4.0 的闸门在"能过墙"的集合里**无解**——当天 F 均值保住 1.7+ 就是现状最好水平。

### 25.4 b22 兄弟 decay 差手术（x246 族 6 源 × de6/de3 = 12 模拟）
- 全部无 FAIL，但 **11/12 仍被墙封死**：corr 只从 0.90 降到 0.85~0.93（`levVV7wl` F1.78 也在内）。唯一直通 `O0NpZnA1`（VkaY0ZA0 de3，corr 0.6792，F1.28/TO34%）进 B 队。
- `xA3xkgjN`（WjbWLqXo de3）gap 仅 **+0.001**（S2.10 vs need 2.101，对手 npdOdMdz S1.91）——离豁免过线只差一丝。
- **★★★★ 新规律（修正规律二适用域）**：**兄弟 decay 差只在 corr 0.70~0.75 边界区有效**（kqoQ2l2d 0.73→0.61）；对 corr ≥0.85 深重叠兄弟无效（降不破 0.685）。⇒ 别再对深重叠家族成批跑 decay 阶梯，每家 2 个探针值（de6/de3）足够判生死。
