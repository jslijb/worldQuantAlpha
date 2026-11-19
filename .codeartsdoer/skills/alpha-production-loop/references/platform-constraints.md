# 平台接口硬约束（全部为实测结论）

> 每条都附复验方式。平台接口会变，使用前先用复验方式确认。

## 字段查询

- `/data-fields` **必须带** `instrumentType=EQUITY` 与 `delay=1`，否则返回
  `400 ["Invalid query"]`。
  - 复验：`GET /data-fields?region=EUR&universe=TOP2500&limit=3` → 400；
    加上 `&instrumentType=EQUITY&delay=1` → 200。
- 全量拉取存在 **10000 条上限**，按 id 字母序截断（某次 EUR 全量返回 10000 条全是 `analyst*`，
  `fundamental*` 整段丢失 → 本地数据集判定误报 `UNKNOWN_DATASET`）。
  - 正确做法：按 `dataset.id` 分数据集拉取。
- `search=` 为模糊匹配，返回数量受 `limit` 约束（`limit=100` 可能返回 0，用 ≤50 更稳）。

## 相关性

- 未提交件的 `/correlations/self` 与 `/correlations/prod` **多数情况返回空 body**，
  不能作为提交前的可靠预检。
- 已提交件的 `/alphas/{id}/check` 只返回 `ALREADY_SUBMITTED`，拿不到历史相关值。
- `GET /alphas/{id}/submit` 可查最近一次提交的判决：403 = 判决书（含精确 SELF/PROD）；
  200 空 body = 判决未出，继续轮询。
- **IS 阶段先有 FAIL 时，PROD/SELF 记为 PENDING**，即拿不到相关性数值。
- 高 S 可触发宽限：实测 S 2.13 + PROD 0.7213 判 PASS；S 1.66 + PROD 0.702 判 FAIL。

## 超级 Alpha（SUPER）

- 创建体结构（旧 `combo:{code}` 写法已失效，会 400）：

```json
{"type":"SUPER",
 "settings":{"instrumentType":"EQUITY","region":"USA","universe":"TOP3000","delay":1,
             "decay":32,"neutralization":"SUBINDUSTRY","truncation":0.08,
             "pasteurization":"ON","unitHandling":"VERIFY","nanHandling":"OFF",
             "language":"FASTEXPR","testPeriod":"P0Y0M",
             "selectionHandling":"POSITIVE","selectionLimit":10},
 "combo":"1","selection":"(1-self_correlation)"}
```

- `combo` / `selection` 必须是**字符串**；`selectionHandling` / `selectionLimit` 必须放在 **settings 内**。
- `selectionLimit` **最小 10**（传 8 → `400 Ensure this value is greater than or equal to 10`）。
- 组件数不足 10 时该市场不可用：`status=ERROR "At least 10 component alphas are required for Super Alpha."`
  （实测 EUR 池 4 条、GLB 池 5 条 → 不可用）。
- `combo` 表达式中**不支持** `self_correlation`、`turnover`（均报 `unknown variable`，报错 location 指向 combo）。
- 提交前必须先 `PATCH /alphas/{id}` 补 `combo.description` 与 `selection.description`（各 ≥100 字符），否则 403。
- 超级的 `truncation` 实测无效：0.05 与 0.12 的 S/F/TO/相关性完全相同。
- 超级创建（模拟）不消耗当日超级配额；提交被拒（403）也不消耗。

## 结果判定

- **提交前必须保证 A 级 checks 全 PASS**（2026-11-18 用户："有警告多半都过不了"）。
- **两级分类（实测依据）**：

| 级别 | 项 | 是否阻断 | 依据 |
|---|---|---|---|
| **A 资格级** | `CLUSTER_TEST` <1.58、`LOW_SHARPE/FITNESS/2Y/SUB_UNIVERSE`、`CONCENTRATED_WEIGHT`、`SELF`、`PROD` | **是** | 平台原文 `Alpha does not qualify as Cluster Alpha`；其余为硬门 |
| **B 奖励级** | `MATCHES_THEMES`、`OSMOSIS_ALLOCATION`、`POWER_POOL_DESCRIPTION_LENGTH` | 否 | 历史 403 判决里带这两条 WARNING 的件，被拒原因均为 PROD/Sub，从未是 themes；它们影响主题乘数与渗透排名，不影响能否提交 |

  ⇒ 把 B 级当硬门会导致交不出件（EUR 件不落在平台当期主题内必然 WARNING）。
  ⇒ 目标：**A 级全 PASS，B 级记录并尽量优化**。
- 旧结论「只有 result==FAIL 才算数」已作废——那是"能不能交进去"，不是"该不该交"。
- `CLUSTER_TEST` 通过线 1.58（与 LOW_SHARPE 同值）；实测通过 1.58 / 1.67 / 1.69 / 1.81，
  被拦 1.57 / 1.52 / 1.51 / 1.33 / 1.29 / 1.24。
- `CLUSTER_TEST` 与 S 大致正相关但**不单调**：加腿有时会降 CLUSTER（1.52→1.46、1.51→1.36）。
  提高 CLUSTER 的现实手段是**换对的轻腿**（FCF 形态加流动比率 1.52→1.67）与**提 S**（S≥2.1 时多在 1.6+）。

## 会话与限流

- 连续高频请求后会出现 `401 {"detail":"Incorrect authentication credentials."}`，
  重新登录也无效 → 属于平台短时限流，**须停手等待**，不要连续重试。
- 403 被拒不消耗提交配额；只有受理（200/201）才占配额。