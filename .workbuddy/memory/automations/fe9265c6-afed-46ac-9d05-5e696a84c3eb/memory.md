# 自动化执行记忆：每周 Alpha 自检

- 2026-11-16 10:15 首次执行（覆盖美东 11-08~11-15）：
  - 数据源：台账（Python csv，awk 切列会串列勿用）+ `_verdict_*.json` 16 份 + 平台 API（探针 `_autologs/_wk_review_probe.py`，含认证、challenge 端点、OS count、15 条 alpha 的 IS/checks）。
  - 结果：入池 16（13R+3S）/ POST 拒 9（PROD 4、LOW_FITNESS 5）；11-15 唯一满额日；台账补记漏掉的 SUPER d5almKdJ；`/competitions/challenge` 404 → isScore 断链待修。
  - 落盘：`docs/research/weekly_alpha_review_2026-11-16.md`、AGENTS.md §4 新增判据、idea.md M17、台账 +1 行。
  - 坑：OS count 与台账差 1 时先查最新 SUPER 是否漏记；verdict JSON 结构不统一（有的 checks 在 body 里，有的独立键）解析要兼容。
