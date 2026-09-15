# WorldQuant Alpha 因子挖掘方法论

> 基于 48+ 轮实测（~100 候选、8 个 ACTIVE Alpha）沉淀的系统化挖掘方法。
> 适用范围：TUTORIAL 权限、USA/EQUITY/TOP3000、FASTEXPR。

## 1. 已验证的有效因子方向（按优先级）

| 方向 | 示例表达式 | S/F | 注意事项 |
|------|-----------|-----|---------|
| **ts_av_diff 偏离度** | `group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry)` | 1.79/1.27 (delay=1)<br>**2.21/1.75 (delay=0)** | 当前最强方向；只对 cf/ev 有效；窗口 60 最优 |
| **简单负债比率** | `liabilities/assets`、`liabilities_curr/assets`、`liabilities_curr/cap` | 1.26~1.55 | 分子限 liabilities/liabilities_curr；分母限 assets/cap |
| **cf/ev 时序排名** | `group_rank(ts_rank(cashflow_op/enterprise_value, 60), industry)` | 1.60/1.24 (dec=6) | decay 调优：dec=4→6 突破 F≥1.0 |
| **signed_power 压缩** | `signed_power(liabilities_curr/assets, 0.5)` | 1.64/1.38 | 只对 liabcurr/assets 有效 |
| **delay=0 变体** | 同一表达式 delay=0 | S 提升约 +0.4 | 与 delay=1 不相关，可同时提交；check 阈值更高 |

## 2. 已验证的降相关策略（避免 SELF_CORRELATION ≥ 0.7）

1. **子类分解**：总负债 → 流动负债（liabilities → liabilities_curr），流动负债与总负债相关 < 0.7
2. **换分母**：账面资产（assets）→ 市值（cap），不同维度降相关
3. **差异化分组操作符**：group_rank vs group_neutralize 相关 < 0.7
4. **时序操作符差异化**：ts_rank（排名位置）vs ts_av_diff（偏离量）不相关
5. **delay 维度**：delay=0 vs delay=1 信号不同，不相关
6. **单调变换注意**：log/signed_power/normalize/group_rank/group_zscore/group_scale 都是单调变换，**不改变排名 → 与原始比率相关**，不能靠这种变换规避自相关

## 3. 已验证的无效方向（避免重复尝试）

### 3.1 因子类型
| 类别 | 例子 | 结果 |
|------|------|------|
| 量价类 | `ts_corr(close, volume, 60)`, `ts_std_dev(returns, 60)`, `close/ts_delay(close, 60)` | S≈0.5~0.6 ❌ |
| 盈利比率 | `return_equity`, `return_assets`, `ebitda/equity`, `cashflow_op/revenue` | S<0.6 ❌ |
| 资产结构 | `ppent/assets`(1.16), `inventory/assets`(0.86), `cash/assets`(-0.22) | ❌ |
| 非负债比率 | `cf/liab`(0.31), `equity/assets`(-1.52), `retained_earnings/assets`(0.03), `working_capital/assets`(-0.48), `operating_income/interest_expense`(0.03) | ❌ |
| 排名差异 | `rank(liabcurr)-rank(assets)`(1.49) | 达标但与 liabcurr/assets 相关 |
| 时序变化 | `ts_delta(liabcurr/cap, 20/60)`(0.20~0.72) | ❌ |
| 时序相关性 | `ts_corr(cf, ev, 60)`(-1.03), `ts_corr(liabcurr, assets, 60)`(0.72) | ❌ |
| 多因子组合 | 差值/乘法/加法/条件（if_else/trade_when） | 全部 ❌，组合反而降 S |
| 新操作符 | `ts_arg_max/min`(0.3~0.5), `ts_quantile`(0.07), `ts_regression` | ❌ |
| ts_av_diff 非 cf/ev | ebitda/cap(1.05), ebit/liab(-0.21), cf/liab(-0.12), cf/assets(0.44), ebit/ev(1.19) | ❌，只对 cf/ev 有效 |

### 3.2 设置维度
| 调整 | 结果 |
|------|------|
| 换 region（CHN/JPN/EUR/GLB） | TUTORIAL 仅支持 USA，400 拒绝 |
| 换 universe（TOP1000/TOP500） | 可用但因子 S 普遍更低；且同 region 跨 universe 仍做自相关检查 |
| 换中性化（SUBINDUSTRY/SECTOR） | SUBINDUSTRY 不改变本质仍相关；SECTOR 降低 S |
| 加 decay 包装 | ts_decay_linear 降低效果；同款因子加 decay 与原始相关 |
| rank() 截面变换 | 降低 Sharpe，不使用 |

## 4. 挖掘流程（每轮标准操作）

```
1. 查存量：GET /users/self/alphas?status=UNSUBMITTED，筛选 S≥1.25 & F≥1.0
   → 避免重复模拟已达标候补（曾直接复用 blja39jM 提交）
2. 批量模拟：10~20 候选/轮，轮询 Retry-After（float 解析）
3. 筛选：S≥1.25 & F≥1.0 & checks 全 PASS（容忍 SELF_CORRELATION=PENDING）
   ※ delay=0 时门槛变为 S≥2.0 & F≥1.3（LOW_SHARPE/LOW_FITNESS 阈值更高）
4. 提交：POST /alphas/{id}/submit → 201≠成功，必须轮询 GET 直到
   status=ACTIVE/SUBMITTED（UNSUBMITTED = 被自相关拒绝）
5. 记录：S/F/T、表达式、settings（delay/decay/neu）、结果到 pitfalls.md
```

## 5. 关键 API/平台知识

| 项 | 要点 |
|----|------|
| 提交语义 | POST 201 仅"已入队校验"，看 GET /alphas/{id} 的 status 字段定成败 |
| SELF_CORRELATION | TUTORIAL 下模拟恒为 PENDING，预检查 `/correlations/self` 返回 max=None 无效；只能直接提交看 403 响应体（含相关性值） |
| Retry-After | 是 float 字符串（"5.0"），必须 `float()` 解析 |
| 模拟结果位置 | `alpha["is"]["sharpe"]`，非顶层 |
| 有效字段 | 48 个基础字段可用（liabilities/liabilities_curr/assets/cap/cashflow_op/enterprise_value/ebitda/ebit/income/debt/debt_lt…）；fnd6_ 前缀字段列表有但表达式不可用 |
| 有效分母 | 仅 assets、cap（ev/equity/revenue/invested_capital 均无效；invested_capital 还触发权重集中） |
| 每日配额 | 美东 03:00 重置；被拒(NONTC/相关性)不消耗配额 |
| 操作符参数 | ts_regression(y,x,d,lag) 的 lag 必须正整数；winsorize/hump 只接受 1 个输入 |

## 6. 效率经验

- 每轮候选控制在 10~20 个，模拟耗时 ~1-2min/个，超长轮次易超时（用 Tee 存日志可断点续读）
- 网络抖动需重连：poll 异常时重新 sign_in() 再续跑
- 发现新有效操作符（ts_av_diff/signed_power）后，立即扩展测试其"有效范围"（哪些比率组合）——通常覆盖范围很窄
- 自相关拒绝的变体系会相互拒绝，识别"本质同族"（如 ts_av_diff 的 SUBINDUSTRY/SECTOR/dec 变体）后整体放弃该族，不逐个死磕

## 7. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-30 | 初版：整合 48 轮挖掘经验、8 个 ACTIVE Alpha 的方法论沉淀 |
| 2026-09-06 | 新增第 8 章：高质量 Alpha 特征（27 个 OS Alpha 数据实证）+ 质量优先策略 |

## 8. 高质量 Alpha 特征与质量优先策略（2026-09-06）

> 基于 27 个 OS Alpha 全指标数据实证 + 平台机制反推。**战略转向：质量优先，宁缺毋滥。**

### 8.1 IS Score 贡献的量化规律（数据实证）

排行榜 IS Score ≈ Σ(每个Alpha的 Sharpe+Fitness) × 常数K（K≈50）
- S 与贡献相关 0.956，F 相关 0.835 —— **S+F 是唯一核心变量**
- 单个 Alpha 贡献分层：
  | S+F | 估算贡献/个 | 典型案例 |
  |-----|-----------|---------|
  | 4.8 | ~240分 | e79kPeEM (S=3.02 F=1.79) |
  | 4.0 | ~200分 | 6XrbGx1L (S=2.26 F=1.75) |
  | 3.3 | ~165分 | 当前27个均值 |
  | 2.3 | ~115分 | QP3XalpK (S=1.27 F=1.07) |
- **结论：一个 S+F=4.0 的 Alpha = 两个 S+F=2.3 的 Alpha**，低质量Alpha纯浪费配额

### 8.2 高质量 Alpha 的特征画像（S+F≥3.6 档）

| 指标 | 甜蜜区 | 说明 |
|------|--------|------|
| Sharpe | ≥1.9（最好≥2.2） | 与贡献相关最高 |
| Fitness | ≥1.7 | F≈S×sqrt(RET/TO)，需低TO高RET |
| Turnover | **9%~28%** | 甜蜜区；TO>50% 拖累 F，TO<5% 常伴随弱信号 |
| Returns | 10%~22% | 年化 |
| Margin | 8~22‰ | 与 TO 负相关(-0.365)，低TO→高MARGIN |
| 结构 | **三因子组合** | TOP5 质量全部是三因子（2基本面+1价格 或 1量价+1基本面+1价格）|
| Drawdown | <7% | 高质量组普遍 4-7% |

实证 TOP5：le8ddYbe(S2.41/F1.87/T23%)、e79kPeEM(3.02/1.79/T57%唯一例外-高回报补偿)、6XrbGx1L(2.26/1.75/T17%)、1YwKML56(2.21/1.75/T19%)、MP1mQRro(1.91/1.74/T9%)

### 8.3 平台机制维度的高质量特征

1. **Checks 全绿**：LOW_SUB_UNIVERSE_SHARPE（子池Sharpe，无法用decay修复）、CONCENTRATED_WEIGHT（truncation可救）是常见拦路虎；高质量Alpha在TOP1000子池同样稳健
2. **prodCorrelation 低**：与全网用户Alpha相关性低 → Uniqueness 高（论坛/社区共识：独特性是稀缺资产）
3. **Pyramid 覆盖**：顾问评级硬指标（Expert≥10/季、Master≥30/季）；新数据集×universe×delay 组合的首个Alpha解锁新Pyramid
4. **Combined Perf**（顾问季评）：Expert>0.5、Master>1.0、GM>2.0
5. **OS 持续性**：IS 高分但 OS 衰减快的信号是"过拟合"，高质量=IS/OS一致

### 8.4 已验证的降相关三件套（突破 0.7 阈值）

1. **全新信号维度**（治本，9维已占满：负债率/cf_ev/cash趋势/ebit_ev趋势/应计/周转率/价格趋势/收益率排名/阴线量占比）
2. **decay=8**（降TO提F，decay=4→8 相关降 0.03+）
3. **SUBINDUSTRY 中性化**（相关 0.70~0.80 且成分不重叠时可用，已三次立功：58Q7kl1z 0.7103→过、A10a7pdY 0.7963→过；成分重叠时无效 0.916）

### 8.5 质量优先策略（新提交标准）

```
提交门槛（从 S≥1.25/F≥1.0 提高）：
  最低线：S≥1.8 且 F≥1.5（S+F≥3.3）
  优先线：S≥2.0 且 F≥1.7（S+F≥3.7）
  拒绝线：预期 S+F<3.0 的候选不提交（贡献太低）
数量：每天 2-3 个高质量，放弃"5个/天"数量目标
方向：新信号维度 > 三因子结构 > 低TO信号
```

### 8.6 低价值挖掘模式（禁止清单）

1. **变体内卷**：同一信号换窗口/分母/操作符（相关0.9+，必拒）
2. **弱信号硬凑**：S<1.2 单因子加价格信号凑数（S+F<3.0）
3. **高TO陷阱**：TO>40% 的信号即使 S 达标，F 难过 1.5
4. **死磕同族**：被拒变体系相互相关，识别后整体放弃
5. **新Alpha即封印**：每个新提交立即成为相关源，同骨架组合当天全拒（A10a7pdY案例）

### 8.7 论坛 setting 对比结论（遗憾规避因子案例）

| 参数 | 论坛 | 我们 | 评估 |
|------|------|------|------|
| Universe | ILLIQUID_MINVOL1M | TOP3000 | 论坛用低流动性池（行为信号在 小盘更强），我们无权限 |
| Neutralization | Subindustry | SUBINDUSTRY | ✅ 一致，已验证 |
| Decay | 0 | 8 | 论坛 decay=0 导致 T=150%；我们 decay=8 是关键 |
| Truncation | 0.04 | 0.01 | 可试 0.04（更宽松权重，待验证） |
| NaN Handling | Off | OFF | 一致 |