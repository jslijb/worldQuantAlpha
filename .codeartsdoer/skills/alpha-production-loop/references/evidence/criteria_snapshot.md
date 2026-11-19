# 判据快照（自动生成，勿手改）

生成时间：2026-11-18 23:08
生成脚本：`scripts/sync_evidence.py`

> 本文件只包含可由台账 / 平台判决书直接算出的统计量。机制类结论见 SKILL.md 与 knowledge。

## 样本

- 台账轮次：n=267（来源 `data/alpha_quality_analysis/IDEA_LOOP_LEDGER.csv`）
- 判决书文件：n=12（来源 `alpha_loop/state/verdicts/*.json`）
- 经验条目：n=28，其中 verified n=0

## 判决分布

- FAIL: n=108（占 n=267 的 40.4%）
- SIM_OK: n=77（占 n=267 的 28.8%）
- OTHER_MALFORMED: n=26（占 n=267 的 9.7%）
- GATE_FAIL: n=11（占 n=267 的 4.1%）
- PASS_READY: n=10（占 n=267 的 3.7%）
- FAIL(403): n=7（占 n=267 的 2.6%）
- SUBMIT: n=7（占 n=267 的 2.6%）
- SIM_ERROR: n=4（占 n=267 的 1.5%）
- GATE_BLOCK: n=4（占 n=267 的 1.5%）
- SUBMITTED: n=4（占 n=267 的 1.5%）
- REJECTED: n=3（占 n=267 的 1.1%）
- IDEA_EXHAUSTED: n=2（占 n=267 的 0.7%）
- STILL_RUNNING: n=2（占 n=267 的 0.7%）
- SUBMIT_READY: n=2（占 n=267 的 0.7%）

## FAIL 项频次（前 10）

- LOW_SHARPE: n=69
- LOW_FITNESS: n=47
- LOW_FITNESS_LOCAL: n=44
- LOW_SHARPE_LOCAL: n=44
- LOW_2Y_SHARPE: n=42
- LOW_SUB_UNIVERSE_SHARPE: n=41
- LOW_SHARPE;LOW_FITNESS;LOW_2Y_SHARPE: n=12
- OK: n=8
- LOW_SHARPE;LOW_FITNESS;LOW_SUB_UNIVERSE_SHARPE;LOW_2Y_SHARPE: n=7
- CLUSTER_TEST: n=7

## 按区域

| 区域 | 轮次 | 提交 | 提交率 |
|---|---|---|---|
| EUR | n=223 | n=11 | 4.9% |
| TOP2500 | n=25 | n=0 | 0.0% |
| USA | n=16 | n=0 | 0.0% |
| ? | n=2 | n=0 | 0.0% |
| JPN | n=1 | n=0 | 0.0% |

## 按数据集（前 10）

| 数据集 | 轮次 | 提交 | 提交率 |
|---|---|---|---|
| fundamental23 | n=118 | n=8 | 6.8% |
| EUR | n=25 | n=0 | 0.0% |
| risk72 | n=22 | n=0 | 0.0% |
| model36 | n=20 | n=0 | 0.0% |
| fundamental6 | n=14 | n=0 | 0.0% |
| fundamental94 | n=14 | n=3 | 21.4% |
| insider_feats | n=12 | n=0 | 0.0% |
| ? | n=9 | n=0 | 0.0% |
| model109 | n=8 | n=0 | 0.0% |
| analyst4 | n=7 | n=0 | 0.0% |

## 台账内 Sharpe 过线率

- S≥1.58：n=68 / n=243（n/a 表示台账未记录 S）

## 平台相关性实测值（来自判决书）

- PROD_CORRELATION 有值件数：n=7
  - 最小 0.6860 / 中位 0.7127 / 最大 0.8943
- SELF_CORRELATION 有值件数：n=0
