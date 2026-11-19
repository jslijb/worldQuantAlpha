# 2026-11-18 下午：首个入池 + fundamental94 开荒

> 三天零入池在 2026-11-18 14:47（北京）被打破。

## 一、入池件（第 1 条）

| 项 | 值 |
|---|---|
| alpha | **58JOm05N** |
| 状态 | `status=ACTIVE` / `dateSubmitted=2026-11-18T01:47:48-05:00` |
| classifications | `DATA_USAGE:SINGLE_DATA_SET` + `REGULAR:REGULAR`（真 ATOM） |
| 设置 | EUR / TOP2500 / SUBINDUSTRY / decay 0 / trunc 0.05 |
| 指标 | S 1.71 / F 1.11 / TO 0.0406 / returns 0.0529 / drawdown 0.0415 / margin 0.002606 |

表达式（fundamental23 单数据集，五腿同向相乘）：

```
group_scale((cashflow_op / current_liabilities_total_4)
            * ts_rank(dividend_per_share_declared / eps, 140)
            * rank(cash_equivalents_total / assets)
            * rank(cashflow_op / ebitda)
            * rank(current_ratio), subindustry)
```

### 为什么这条能过而 group_zscore 版过不了

同内核同设置只换最终外壳：

| 外壳 | PROD | 结果 |
|---|---|---|
| **group_scale** | ≤0.70 | **受理 ACTIVE（58JOm05N）** |
| group_zscore | 0.7020 | 403 拒（WjlGGmwx，差 0.0020） |
| group_rank | **0.8885** | 403 拒（88NQ03Av） |

**但这条不能外推**：把同一招用到单腿 CFO/资产 上，group_scale 0.90（vs group_zscore 0.8943）毫无改善。
⇒ **group_scale 只在 PROD 已贴门槛（0.70x）时能作最后一刀；差距 >0.02 时无效。**

### 同内核限一条（实测）

四个变体 IS 全过（S 1.66~1.91），只有第一个入池，其余全被相关性打死：

| id | SELF | PROD | 结论 |
|---|---|---|---|
| 58JOm05N | — | ≤0.70 | ACTIVE |
| 88NQ03Av (grank) | 0.8885(PASS) | **0.8885 FAIL** | 拒 |
| zqdmxVR8 (smooth) | **0.9535 FAIL** | — | 拒 |
| QP0V8NaG (softgate) | **0.9802 FAIL** | — | 拒 |

## 二、fundamental94 开荒（新数据集）

`fundamental94`（Aggregated Fundamental Data）EUR TOP2500 有 **528 字段**、完整三表，几乎无人用：
`fnd94_cf_cash_from_oper`（CFO，cov 1.0，uc 120）、`fnd94_bs_assets_tot`（总资产，cov 1.0，uc 54）、
`fnd94_bs_curr_liab_tot`（流动负债，uc 12）、`fnd94_q_q_qin`（净利润，uc 5）、`fnd94_is_oper_inc_bef_dep_q`（uc 3）。

### 实测：换数据集能把 PROD 降 0.09，但同一形态仍撞

| 件 | 形态 | S | SELF | PROD |
|---|---|---|---|---|
| 6XMeXpgp | fundamental23 CFO/资产 (group_scale INDUSTRY) | 1.90 | 0.6877 | **0.90** |
| LLKdapvn | fundamental94 CFO/资产 | 1.81 | 0.5612 | **0.8114** |
| LLKda3W6 | fundamental94 CFO/流动负债 | 1.59 | 0.5941 | **0.8064** |
| akaE327x | fundamental94 CFO/资产 (group_zscore) | 1.83 | 0.5759 | **0.8227** |

⇒ **PROD 的载体是信号形态，不是数据集**（与既有结论一致）。换数据集只降 0.09，仍差 0.10。

### 加腿在 fundamental94 上只稀释、不救 PROD

五腿 S 1.09、四腿 1.45、修现金语义后 1.42、现金流改善形态 1.26 —— 无一过 1.58。
根因：fundamental94 的腿字段口径/覆盖与 fundamental23 不同（分红腿 cov 仅 0.47，作乘数会使 53% 标的归零）。

### 非现金流机制在 fundamental94 上全部 <1

| 机制 | S |
|---|---|
| 应计质量 (净利−CFO)/资产 | 0.14 |
| 非经常损益/资产（正方向） | 0.76 |
| 非经常损益年度累计 | 0.40 |
| 非经常损益 × ROA 双确认 | 0.87 |
| ROA 同比改善 × 流动比率 | 0.70 |

⇒ 与 EUR 11 条非量价机制实测一致：**信号集中在"现金流/规模"族**。

## 三、当日最强件：现金流/营收（S 2.20）

```
group_scale(cashflow_op / sales, industry)
```

S **2.20** / F **1.80** / TO 0.0435 / 2Y **2.95** / CLUSTER **PASS 1.58** / 全部 PASS，
**唯一 FAIL：LOW_SUB_UNIVERSE_SHARPE 1.13 < 1.14（差 0.01）**。

已试的救法全部失败：

| 变体 | S | Sub | 判定 |
|---|---|---|---|
| trunc 0.08 | 2.20 | 1.13 | 数值一字不动 |
| sector 组 | 1.33 | 0.28 | 崩 |
| decay 4 | 2.16 | 1.09 | 更差 |
| group_zscore | 2.11 | 0.97 | 更差 |
| × rank(operating_income/sales) | 1.57 | 0.78 | 稀释 |

待测：STATISTICAL 中性化（遇平台 401 限流，等恢复后补测）。

## 四、今日新增的字段/接口坑

1. **`/data-fields` 必须带 `instrumentType=EQUITY` 与 `delay=1`**，否则一律 `400 ["Invalid query"]`
   （旧写法 `region=&universe=` 已失效）。
2. **字段缓存 10000 条上限截断**：EUR 全量拉取返回的 10000 条按 id 字母序截断，全是 `analyst*`，
   `fundamental*` 全部丢失 ⇒ ATOM 门报 `UNKNOWN_DATASET` 误杀。
   修法：新工具 `alpha_loop/pull_dataset_fields.py`，按 `dataset.id` 补齐（fundamental94 +528 / fundamental23 +2332）。
3. **字段语义必须查 description**：`fnd94_bs_cash_only_q` 是 **Net Cash（净现金）**，不是现金及等价物；
   现金腿正确字段是 `fnd94_bs_cash_equiv_q`。
4. **`dividends_paid_cashflow_quarterly` 没有 `fnd94_` 前缀**，但仍属 fundamental94。
5. **401 连续出现 = 平台短时限流**，重登无效，须停手等待恢复（今日实测两次连发均 401）。
6. `submit.submit()` 对 201 受理不写 verdict 文件；追查判决要用 `GET /alphas/{id}/submit`。

## 五、最终结果：当日常规 4/4 满额

| # | alpha | 表达式（fundamental23 单数据集） | S | F | TO | SELF | PROD |
|---|---|---|---|---|---|---|---|
| 1 | **58JOm05N** | 五腿：CFO/短债 × 分红位置 × 现金/资产 × CFO/EBITDA × 流动比率 | 1.71 | 1.11 | 0.041 | — | ≤0.70 |
| 2 | **d5aR7VZv** | CFO/营收 × 现金/资产 × CFO/EBITDA | 2.38 | 1.99 | 0.044 | 0.3277 | 0.7048 |
| 3 | **xAvdRx9q** | (CFO/营收)/自身波动 × 现金/资产 | 2.13 | 1.61 | 0.051 | 0.5956 | 0.7213（高 S 特赦） |
| 4 | **vRAvjmNw** | EBITDA/营收 × 现金/资产 × CFO/资产 × 现金/短债 | 1.62 | 1.06 | 0.040 | 0.6734 | 0.6734 |

四条全部 `DATA_USAGE:SINGLE_DATA_SET`（真 ATOM），全部 ACTIVE。

### 第 2~4 条的路径（可复用的排序）

1. **S 2.20 的 `CFO/营收` 单腿** Sub 差 0.01，所有救法失败（trunc/sector/decay/zscore/加腿/STAT/universe）。
2. **加两条现金流质量腿**（现金/资产、CFO/EBITDA）反而把 S 抬到 2.38、Sub 抬到 1.39 ⇒ **同族同向的腿是"确认"不是"稀释"**，前提是腿的语义与覆盖正确。
3. 同骨架换 `revenue` 分母 ⇒ SELF 0.9743 撞线（sales 与 revenue 太相似）。
4. **换表达形式**（水平 → 水平/自身波动 = 风险调整现金转化率）⇒ SELF 掉到 0.10 量级，S 2.13，靠高 S 特赦过 PROD 0.7213。
5. 第 4 条又回到水平乘法形态（EBITDA 利润率为主腿，SELF 干净），把第四条腿换成**现金/短债覆盖**后 PROD 从 0.702 降到 0.6734。

### 关键量化规律（本条最有价值）

- **0.702 是该族在 EUR 的 PROD 地板**：五腿件（58JOm05N 前身 0.7020）、四腿件（P05On6wx 0.702）两次撞同一数值。
- **SELF 由主腿决定，换辅助腿无效**：任何含 `(CFO/营收)/ts_std_dev(...,250)` 的件 SELF 恒 0.748~0.754；换分红窗口（100/140）、换波动窗口（60/500）、换辅助腿（current_ratio → 低杠杆）都只动 0.006 以内。
- **换主腿才动 SELF**：`CFO/营收` IR 主腿 → `CFO/资产` IR 主腿 SELF 0.8876；换成水平乘法（EBITDA/营收）SELF 0.67。

## 六、EUR 无法做超级（平台硬约束）

创建 EUR SUPER 返回：

```
status=ERROR  message="At least 10 component alphas are required for Super Alpha."
```

⇒ **EUR 已提交池不足 10 条，该区域超级配额不可用**（不是参数问题）。超级只能在有足量池子的市场（USA/GLB）做，
这与"不进 USA 兜底"的约束叠加后，等于**当前没有可用的超级通道**。

附：SUPER 创建接口的正确 body 结构（旧的 `combo:{code}` 写法已失效）：

```json
{"type":"SUPER",
 "settings":{"instrumentType":"EQUITY","region":...,"universe":...,"delay":1,"decay":25,
             "neutralization":"SUBINDUSTRY","truncation":0.08,"pasteurization":"ON",
             "unitHandling":"VERIFY","nanHandling":"OFF","language":"FASTEXPR",
             "testPeriod":"P0Y0M",
             "selectionHandling":"POSITIVE","selectionLimit":10},
 "combo":"1","selection":"(1-self_correlation)*in(datasets,\"fundamental23\")"}
```

`combo`/`selection` 必须是**字符串**，`selectionHandling`/`selectionLimit` 必须在 **settings 内**（平台 400 明确列出）。

## 七、当前状态

- 今日常规 **4/4 满额**（连续三天零入池后首次满额）
- 超级配额不可用（EUR 池不足 10 条）
- 结构性约束仍成立：EUR 只有现金流族有信号，形态差异（水平 / 风险调整 / 主腿替换）是唯一有效旋钮
## 八、超级 Alpha 攻坚（2026-11-18 晚，常规 4/4 满额后）

今日常规 4/4，超级 0/1 可用。池子规模实测（已提交、stage=OS）：

| 市场/universe | 常规件数 | 能否做超级（需 ≥10 组件） |
|---|---|---|
| USA TOP3000 | 277 | ✅ |
| USA TOP1000 | 35 | ✅ |
| USA TOP2000 | 31 | ✅ |
| GLB MINVOL1M | 5 | ❌ |
| EUR TOP2500 | 4 | ❌ |

USA 池成分（按表达式字段解析主数据集）：**pv1 301 / fundamental6 46 / analyst4 3 / option8 2**（共 352 条常规件）。

### 已试配置与 SELF 判决

| # | 配置 | S | F | TO | SELF | 结果 |
|---|---|---|---|---|---|---|
| 1 | USA TOP3000 / decay32 / limit10 / sel=`(1-self_correlation)` | 2.78 | 2.32 | 0.0412 | **0.7116 FAIL** | 拒（LLKdKNk6） |
| 2 | 同 1 + sel 限 `in(datasets,"fundamental6")` | 2.48 | 1.98 | 0.046 | **0.7109 FAIL** | 拒（E5QeNAWK） |
| 3 | USA TOP2000 / decay32 / limit10 / 默认 sel | 2.27 | 2.21 | 0.0437 | 待判（vRAv67rG） | — |

### 已确认的平台硬约束

- **selectionLimit 最小 10**：传 8 返回 `400 Ensure this value is greater than or equal to 10`。
- 判决书里 `PROD_CORRELATION` 在 SELF FAIL 时为 **PENDING**（平台不再算第二项），所以一旦 SELF 撞线就拿不到 PROD。
- 超级创建的模拟**不消耗**当日超级配额（配额在 submit 受理时才占；403 被拒不占）。

### 当前判断

换组件主题（fundamental6）只把 SELF 从 0.7116 降到 0.7109（-0.0007），说明 **SELF 不是组件选择决定的**；
与 11-16 的 decay 楼梯实测（每 +6 档压 ≈0.005、同时抬 PROD 0.008）叠加看，
**0.71 是该池下超级的结构性下限，与 0.70 门差 0.01 量级**。
下一步唯一未试的维度是**中性化**（此前所有配置都是 SUBINDUSTRY）。

### 追加实测（20:0x）

| # | 配置 | S | F | TO | SELF | 结论 |
|---|---|---|---|---|---|---|
| 3 | USA TOP2000 / d32 / limit10 / 默认 | 2.27 | 2.21 | 0.0437 | **0.9136 FAIL** | TOP2000 池 31 条太同质，更差 |
| 4 | USA TOP3000 / d32 / limit10 / **neut MARKET** | 2.83 | 2.39 | 0.0395 | **0.7187 FAIL** | 中性化不是杠杆（反升 0.007） |
| 5 | USA TOP3000 / **d56** / limit10 / **trunc 0.05** | 2.56 | 2.04 | 0.0307 | 待判 | — |

**结论：SELF 对超级几乎是结构性常量。** 组件主题（-0.0007）、组件池（+0.20）、中性化（+0.007）全部无效，
唯一有单调效果的是 decay（11-16 实测每 +6 档 ≈ -0.005，d56 已知最低 0.7074）。

原因可解释：超级 = 已提交件的等权组合，它与池内任一 alpha 的相关 ≈ 组件对该 alpha 的平均相关，
所以 SELF 的下限就是"池内平均相关的最低水平"。池子越演进（今天 352 条），这个下限越高 ⇒
**同一配方 11-14 能过（wpoXaojQ），今天同配置 0.7116 被拒**。
