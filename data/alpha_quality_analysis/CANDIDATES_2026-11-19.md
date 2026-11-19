# 2026-11-19 候选清单（14:00 后直接提交）

> 生成时间：2026-11-19 00:45（北京）｜A 级 checks 全 PASS 才入选
> 全部 EUR / TOP2500 / INDUSTRY / decay 0 / trunc 0.05，单数据集 fundamental23（真 ATOM）

## 候选（5 条，按提交优先级）

| # | alpha | 主腿经济量 | S | F | TO | Sub | CLUSTER | 2Y | 风险 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **9qlpK85o** | CFO/营收 | 2.45 | 2.13 | 0.0393 | 1.38 | **1.81** | 3.01 | — |
| 2 | **2r5par3w** | CFO/企业价值 | 2.49 | 2.09 | 0.0610 | 1.32 | **1.66** | 2.30 | EV 分母 PROD 历史 0.85+ |
| 3 | **A1xGYzQX** | FCF/资产 | 2.11 | 1.69 | 0.0329 | 1.27 | **1.69** | 2.00 | — |
| 4 | **0mPp3PEK** | FCF/营收 | 2.16 | 1.72 | 0.0397 | 1.37 | **1.67** | 2.63 | — |
| 5 | **leaWRz9n** | CFO/营收+现金/短债 | 2.06 | 1.64 | 0.0442 | 1.07（压线） | **1.58** | 2.31 | Sub 压线 |

## 表达式

```
1) group_scale((cashflow_op / sales) * rank(cash_equivalents_total / assets) * rank(current_ratio), industry)

2) group_scale((cashflow_op / enterprise_value) * rank(cash_equivalents_total / assets) * rank(current_ratio), industry)

3) group_scale(((cashflow_op - capex) / assets) * rank(cash_equivalents_total / assets) * rank(current_ratio), industry)

4) group_scale(((cashflow_op - capex) / sales) * rank(cash_equivalents_total / assets) * rank(current_ratio), industry)

5) group_scale((cashflow_op / sales) * rank(cash_equivalents_total / current_liabilities_total_4) * rank(current_ratio) * rank(cashflow_op / ebitda), industry)
```

## 提交规则

1. **北京时间 14:00 后**开始（配额窗口实测口径）。
2. **逐条提交、一次一条**；403 被拒不消耗配额，可继续下一条，失败原因记 `FAIL:<code>`。
3. 主腿分组：1 与 5 同为 CFO/营收 → SELF 大概率互相撞，只能取其一；
   3 与 4 同为 FCF 族 → 同理。**实际可过估计 2~3 条**。
4. 若只过 2 条，剩余配额用第 6/7 条备选（见下）。
5. 入池立即追加 `SUBMITTED_LEDGER.csv`。

## 备选（A 级未全过，需先改形态）

- `MP6G8Ev6`：CFO/营收 × 现金/短债 × 流动比率，S 2.25，**CLUSTER 1.57 差 0.01**
  → 加 CFO/EBITDA 腿即得 `leaWRz9n`（CLUSTER 1.58）
- `YPavGzv6`：CFO/营收 × 流动比率，S 2.34，Sub 1.20<1.22

## B 级警告（全部候选共有，不阻断）

`MATCHES_THEMES`（GLB/D1 Power Pool Nov`26 / turnover theme 乘数不匹配）、
`OSMOSIS_ALLOCATION`（Daily Osmosis Rank 未生成）。
EUR 件不落平台当期主题内，无法消除；历史证据：带这两条 WARNING 的件被拒原因均为 PROD/Sub。