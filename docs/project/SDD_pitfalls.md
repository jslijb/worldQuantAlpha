# Pitfalls — 踩坑记录

> 记录开发过程中遇到的关键问题、解决方案和经验，防止会话压缩后丢失。

## 1. API 协议踩坑

### 1.1 Retry-After 是 float 字符串
- **现象**：`int(headers["Retry-After"])` 报错 ValueError
- **原因**：API 返回 `"5.0"` 而非 `"5"`
- **解决**：`float(headers.get("Retry-After", 0))`
- **位置**：utils.py, AlphaSimulator.py, alpha_hunter.py 等所有轮询处

### 1.2 模拟结果在 `is` 字段下，非顶层
- **现象**：`alpha["sharpe"]` 返回 None
- **原因**：Sharpe/Fitness/Turnover 在 `alpha["is"]["sharpe"]` 下（In-Sample）
- **解决**：`is_d = alpha.get("is", {}); sh = is_d.get("sharpe", 0)`

### 1.3 SELF_CORRELATION 在 TUTORIAL 权限下始终 PENDING
- **现象**：checks 里 SELF_CORRELATION 永远不是 PASS
- **原因**：TUTORIAL 账号无完整自相关数据
- **解决**：筛选时容忍 PENDING：`result not in ('PASS', 'PENDING')` 才算失败
- **关键**：不影响提交，提交时才真正校验

### 1.4 提交返回 503 不是错误
- **现象**：POST /alphas/{id}/submit 返回 503
- **原因**：已排队，非错误
- **解决**：继续轮询 GET 同一 URL

### 1.4b POST 返回 201 不等于提交成功（关键踩坑）
- **现象**：POST /alphas/{id}/submit 返回 201，以为成功
- **真相**：201 只是"请求已接受进行校验"，SELF_CORRELATION 校验可能后续失败
- **正确做法**：POST 后必须轮询 GET 同一 URL，并检查 `GET /alphas/{id}` 的 `status` 字段
  - `status=ACTIVE` 或 `SUBMITTED` 才是真正成功
  - `status=UNSUBMITTED` 表示提交被拒（如 SELF_CORRELATION FAIL）
- **实例**：blja39jM (debt/assets) POST 返回 201，但实际 SELF_CORRELATION=0.8365 > 0.7，最终 status=UNSUBMITTED

### 1.4c 提交成功的强制三连确认（自 2026-08-30 起强制）
- **背景**：仅凭 POST 201 / GET status 单字段容易误判，必须展示"状态迁移证据"才可信
- **强制确认逻辑**（三步全验证，缺一不可）：
  1. `POST /alphas/{id}/submit`（200/201=接受，503=排队继续轮询）
  2. 轮询 `GET /alphas/{id}/submit` 直到 Retry-After=0
  3. 独立 `GET /alphas/{id}` 验证三个字段：
     - `status == "ACTIVE"`（或 "SUBMITTED"）
     - `dateSubmitted` 存在（非 None）
     - `stage == "OS"`（从 IS 迁移到 OS）
- **实证**（2026-08-30 决定性对比）：
  - 未提交的 Alpha：`status=UNSUBMITTED, dateSubmitted=None, stage=IS`
  - 已提交的 Alpha：`status=ACTIVE, dateSubmitted=时间戳, stage=OS`
  - 权威记录 `GET /users/self/activities/submissions` 的 records 与 ACTIVE 一一对应
- **交付要求**：提交成功判定代码必须以三连确认为准，并将确认结果（ID/时间戳/stage）写入日志文件，作为可复核证据

### 1.5 /correlations/self 预检查免费
- **用途**：提交前检查 max_corr < 0.7，避免浪费每日提交配额
- **响应**：`{"min": 0.1, "max": 0.5}`，看 max

### 1.6 /check 接口只能 GET
- **现象**：POST /alphas/{id}/check 返回 405
- **解决**：改用 GET

### 1.7 data-fields 响应无 next/previous
- **格式**：`{"count": N, "results": [...]}`，需自行用 offset 分页

### 1.8 operators 返回裸数组
- **格式**：直接 JSON 数组，非 `{count, results}`

## 2. 表达式踩坑

### 2.1 ts_return 不存在
- **现象**：表达式中用 ts_return 报 unknown variable
- **解决**：用 `ts_delta(close, 1)` 或 `ts_delta(close, 1)/close` 替代

### 2.2 ts_av_diff 在 world3.py 中使用但未验证
- **风险**：可能不是有效操作符
- **建议**：先用 GET /operators 确认

### 2.3 decay 参数调优
- **经验**：`decay=4` 是 Sharpe 和 Turnover 的最佳平衡点
- **实测**：cf/ev 时序排名 dec=0→F=0.85, dec=2→0.91, dec=3→0.94, dec=4→0.97+

### 2.4 gross_margin 字段不存在
- **现象**：`ts_delta(rank(gross_margin), 60)` 报 `unknown variable "gross_margin"`
- **原因**：TUTORIAL 权限下 fundamental6 无 gross_margin 字段
- **解决**：使用前先 GET /data-fields 确认字段存在；可用 ebitda/cashflow_op/revenue 等已验证字段

### 2.5 量价类因子在当前设置下效果差
- **实测**（2026-08-28，INDUSTRY 中性化, dec=4）：
  - `-1 * ts_corr(close, volume, 60)`：S=0.54 F=0.30 ❌
  - `ts_std_dev(returns, 60)`：S=-0.51 F=-0.52 ❌
  - `close / ts_delay(close, 60)`：S=-0.62 ❌
  - `ts_delta(rank(cashflow_op), 60)`：S=0.35 F=0.14 ❌
- **结论**：纯量价/时序变化因子在 TOP3000/INDUSTRY 下难以达标，简单财务比率（如 debt/assets）更有效

## 3. 提交策略踩坑

### 3.1 已提交 Alpha 会影响新 Alpha 的自相关性
- **已提交**：58p2XdxX (liabilities/assets), wpjoxbbd (cf/ev 时序排名)
- **策略**：新 Alpha 需用完全不同的结构（不同分子/分母、不同操作符组合）
- **避免**：简单财务比率（revenue/assets, ebitda/equity 等）可能与 liabilities/assets 相关

### 3.2 每日提交有配额限制
- **建议**：先模拟+预检查，只提交最有把握的 1~2 个

### 3.3 优先检查现有 UNSUBMITTED 达标候选
- **经验**（2026-08-28）：历史模拟可能已产生达标但未提交的 Alpha
- **操作**：`GET /users/self/alphas?status=UNSUBMITTED&sort=-is.fitness` 筛选 S≥1.25 & F≥1.0
- **本次**：发现 `blja39jM` = `debt/assets`（S=1.40 F=1.20, max_corr=0.0000）直接提交成功，无需重新模拟
- **教训**：挖掘前先查存量，避免重复模拟浪费时间

## 4. 环境踩坑

### 4.1 Windows 控制台 UTF-8
- **问题**：中文/emoji 输出乱码
- **解决**：
```python
import sys, io, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
```

### 4.2 conda 环境激活
- **命令**：`conda activate bigmodel`
- **禁止**：不能运行 `conda init`

## 5. 项目整理记录

### 2026-08-28 整理
- **删除** 17 个临时脚本（world1/2/3, hunt_final*, submit2~8, today_submit, submit_today, check_np7_now, confirm_today, wait_check）
- **原因**：均为一次性调试脚本，逻辑已被 alpha_hunter.py / find_and_submit_alphas.py 覆盖
- **保留** 5 个核心模块 + API 文档 + 凭据 + CSV 队列
- **新建** docs/ 目录，建立 SDD 文档体系

### 2026-08-28 挖掘提交
- **成功提交 Alpha**：`rKj7w0Z1` = `group_rank(ts_rank(cashflow_op/enterprise_value, 60), industry)` (dec=6)
  - S=1.60 F=1.24 T=15.1%，FINAL status=ACTIVE 确认成功
  - 关键：group_rank（非 group_neutralize）+ dec=6 突破 F=1.0（dec=4 时 F=0.97）
- **失败教训**：
  - blja39jM (debt/assets) S=1.40 F=1.20 但 SELF_CORRELATION=0.8365 与 liabilities/assets 相关，被拒（403）
  - POST 返回 201 不等于成功，必须检查 final status
- **无效候选**（均未达标）：
  - 量价类：-ts_corr(close,volume,60) S=0.54, ts_std_dev(returns,60) S=-0.51, close/ts_delay(close,60) S=-0.62
  - 趋势类：ts_delta(rank(cashflow_op),60) S=0.35
  - 比率类：return_equity S=0.32, return_assets S=0.29, ebitda/equity S=0.24, cashflow_op/revenue S=-0.54
  - 不同分子时序：ebitda/ev_ts60 S=1.00, ebit/ev_ts60 S=1.01（不如 cf/ev）
  - 不同窗口：cf/ev_ts120 S=1.10, cf/ev_ts20 S=1.02（不如 ts60）
- **结论**：cf/ev ts60 是最优组合，group_rank + dec=6 可达标且与 wpjoxbbd (group_neutralize) 相关性可接受

### 2026-08-28 第二轮挖掘（第 4 个 Alpha）
- **成功提交**：`RR79x16n` = `liabilities_curr/assets`，S=1.47 F=1.16 T=1.9%，status=ACTIVE
  - 方法论：`liabilities/assets` 的子类——流动负债/资产，捕捉**短期偿债能力**而非总体杠杆
  - 与 liabilities/assets 相关性 < 0.7（流动负债只是总负债一部分）
- **失败候选**（达标但被拒，相关性 ≥ 0.7）：
  - `debt_lt/assets` S=1.35 F=1.12 → 与 liabilities/assets 相关（长期负债是总负债主体）
  - `group_rank(ts_zscore(cf/ev, 60), industry)` S=1.68 F=1.43 → 与 cf/ev ts_rank 系列相关
  - `group_rank(ts_rank(cf/cap, 60), industry)` S=1.71 F=1.40 → 与 cf/ev 系列相关
  - `group_rank(ts_rank(ebitda/cap, 60), industry)` S=1.39 F=1.07 → 与 cf/ev 系列相关
- **关键经验**：
  - 时序排名型（ts_rank/ts_zscore）无论用 cf/ev、cf/cap、ebitda/cap 都与已提交的 cf/ev 系列高相关
  - 简单比率型可用**子类分解**策略：总负债 → 流动负债/长期负债，流动负债与总负债相关性更低
  - /correlations/self 在 TUTORIAL 下返回 max=None，预检查无效，只能直接提交看 403 响应

### 2026-08-28 第三轮挖掘（第 5 个 Alpha）
- **成功提交**：`9qX8Nr6r` = `liabilities_curr/cap`，S=1.26 F=1.49 T=3.8%，status=ACTIVE
  - 方法论：**换分母策略** — `liabilities_curr/assets`（账面资产）→ `liabilities_curr/cap`（市值）
  - 账面资产 vs 市值是不同维度，相关性 < 0.7
- **失败候选**：
  - `liabilities/cap` S=1.19 F=1.32（Sharpe 不够 1.25）
  - `cash/assets` S=-0.22, `ppent/assets` S=1.16, `inventory/assets` S=0.86（非负债类简单比率均不佳）
  - `group_rank(ts_rank(liabilities/assets, 60))` S=-0.69（杠杆时序排名无预测力）
  - `group_zscore(ts_rank(cf/ev,60))` S=1.42 被拒, `group_rank(ts_rank(cf/ev,60),subindustry)` S=1.58 被拒
  - `ebitda/ev` dec=10 S=1.12, `ebit/cap` ts60 S=1.45 被拒
- **三大有效策略总结**：
  1. **子类分解**：liabilities → liabilities_curr（流动负债与总负债相关性低）
  2. **换分母**：assets（账面）→ cap（市值），不同维度降相关
  3. **时序排名 + decay 调优 + 差异化分组操作符**：cf/ev ts60, group_rank vs group_neutralize, dec=4/6

### 2026-08-29 第四轮挖掘（未找到新因子）
- **配额确认**：美东时间 03:00 重置，8-29 配额已刷新。被拒(403)不消耗配额
- **qMjGZNAZ** group_rank(liabilities_curr/assets) S=1.59 F=1.2 全 PASS，但 SELF_CORRELATION=0.8376 与 RR79x16n 相关，被拒
- **invested_capital 分母**：liabilities_curr/invested_capital S=1.35 F=1.61 但 CONCENTRATED_WEIGHT FAIL(0.367>0.1)，truncation 0.08 无效
- **fnd6_ 前缀字段不可用**：fnd6_xint、fnd6_xsga 报 unknown variable（data-fields 列表有但表达式不可用）
- **ts_decay_linear 包装**：降低效果（S=1.28 F=0.96, S=1.12 F=0.78）
- **无效分母汇总**：enterprise_value(S~0.8), equity(S~0.7), revenue(S~0.5), invested_capital(权重集中)
- **有效分母仅 assets 和 cap**；有效分子仅 liabilities 和 liabilities_curr
- **两大方向均饱和**：负债比率变体都与已提交相关；cf/ev 时序排名变体都与已提交相关
- **下一步建议**：换 region(CHN/JPN)、换 universe(TOP1000)、或用 LLM 生成更复杂表达式

### 2026-08-30 第五~六轮挖掘（成功提交 2 个新 Alpha）

#### 关键突破
- **ts_av_diff 操作符**：`ts_av_diff(x, d)` = x - ts_mean(x, d)，衡量当前值相对时序均值的偏离度
  - `group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry)` S=1.79 F=1.27 T=19.0% → **ACTIVE** (vRjG1Jzw)
  - 与 ts_rank(cf/ev, 60) 不相关：ts_rank 衡量排名位置，ts_av_diff 衡量偏离量
  - **只对 cf/ev 有效**，对其他比率（cf/revenue, ebitda/cap, ebit/liab, cf/liab, cf/assets）均无效
  - 60 天窗口最优（120 天 F=0.90, 20 天 F=0.84）
  - 加 decay=4 与已提交相关

- **signed_power 操作符**：`signed_power(x, 0.5)` = sign(x)*|x|^0.5，压缩极端值
  - `signed_power(liabilities_curr/assets, 0.5)` S=1.64 F=1.38 T=1.9% → **ACTIVE** (QP7z069Q)
  - 不同幂（0.3/0.5/0.7）相互相关
  - 对其他负债比率（liab/assets, liab/cap, liabcurr/cap, debt/assets）都与已提交相关

#### 无效方向汇总（本轮）
- **换 region**：TUTORIAL 权限只支持 USA（CHN/JPN/EUR/GLB 均不可用）
- **换 universe**：TOP1000/TOP500 可用，但不能绕过自相关性（同 region 跨 universe 比较）
- **非负债简单比率**：cf/liab(S=0.31), equity/assets(S=-1.52), revenue/assets, retained_earnings/assets(S=0.03), working_capital/assets(S=-0.48), operating_income/interest_expense(S=0.03) 全部 FAIL
- **有息负债**：debt/assets(S=1.38) 和 debt_lt/assets(S=1.35) 达标但与 liabilities/assets 相关（debt ⊂ liabilities）
- **排名差异**：rank(liabcurr)-rank(assets) S=1.49 达标但与 liabcurr/assets 相关；其他排名差异均不达标
- **时序变化**：ts_delta(liabcurr/cap, 20/60) S=0.20~0.72 均不达标
- **长窗口时序排名**：ts_rank(liabcurr/assets, 250) S=0.49 不达标
- **不同中性化**：SUBINDUSTRY 不改变本质仍相关；SECTOR 降低 Sharpe
- **ts_av_diff 对其他比率**：cf/rev(S=-0.75), ebitda/cap(S=1.05), ebit/liab(S=-0.21), cf/liab(S=-0.12), cf/assets(S=0.44), ebit/ev(S=1.19), income/ev(S=0.62) 均不达标
- **单调变换与原始比率相关**：log(S=1.66), normalize(S=1.47), group_zscore(S=1.46) 都达标但被拒
- **操作符组合**：signed_power+ts_av_diff(S=1.79) 与 ts_av_diff 相关；ts_av_diff+signed_power(S=0.84) 不达标
- **新操作符**：ts_arg_max(S=0.32), ts_arg_min(S=0.48), ts_quantile(S=0.07), if_else(S=0.28), trade_when(S=1.47 被拒) 大多无效
- **ts_regression**：参数格式 `ts_regression(y, x, d, lag)`，lag 必须为正整数

#### 第 41-43 轮：ts_corr/多因子组合/交互项（全部无效）
- **ts_corr**：ts_corr(cf, ev, 60) S=-1.03, ts_corr(liabcurr, assets, 60) S=0.72 均不达标
- **多因子差值**：liabcurr/assets - liabcurr/cap S=-0.98, liab/assets - liabcurr/assets S=1.16 均不达标
- **group_scale**：S=1.60 F=1.24 达标但与 liabcurr/assets 相关（单调变换）
- **hump**：参数错误（只需 1 个输入）
- **交互项**：liabcurr/a * cf/ev S=0.21, rank(liabcurr/a)*rank(cf/ev) S=0.72 均不达标
- **条件因子**：if_else(cf>0, liabcurr/a, 0) S=0.63, if_else(ts_delta(cf,60)>0, ±liabcurr/a) S=-0.84 均不达标
- **加法组合**：liabcurr/a + cf/ev, rank(liabcurr/a)+rank(cf/ev) 均不达标

#### 关键经验
1. **单调变换不改变排名**：log, signed_power, normalize, group_rank, group_zscore, group_scale 都是单调变换，与原始比率相关
2. **ts_av_diff 是有效的新操作符**：提取"偏离度"信号，与 ts_rank（排名位置）不相关；只对 cf/ev 有效
3. **signed_power 是有效的压缩变换**：但只对 liabcurr/assets 有效，且与其他负债比率相关
4. **TUTORIAL 权限限制**：只能用 USA region，不能换 region 绕过自相关性
5. **交互项/条件因子/多因子组合均无效**：组合多个信号反而降低 Sharpe
6. **ts_corr 无效**：时序相关性因子在当前设置下无预测力
7. **多因子差值无效**：两个有效因子的差值不产生新信号

### 2026-08-30 第七轮挖掘（delay=0 重大突破，又提交 2 个）

#### 重大发现：delay=0 产生更强信号
- **`group_rank(ts_av_diff(cf/ev, 60), industry)` with delay=0**：S=2.21 F=1.75 T=18.9% → **ACTIVE** (1YwKML56)
  - 与 delay=1 的同一表达式（vRjG1Jzw, S=1.79）不相关（数据时间不同），自相关性通过！
  - delay=0 = 当天数据可用；delay=1 = 前一日数据。两者信号不同
- **delay=0 的其他变体**：
  - group_neutralize 版：S=0.12 FAIL（group_neutralize 在 delay=0 下无效）
  - SUBINDUSTRY 版：S=2.33 F=1.68（与 INDUSTRY 版相关）
  - SECTOR 版：S=2.07 F=1.64（与 INDUSTRY 版相关）
  - dec=2 版：S=2.05 F=1.77（与 dec=0 版相关）
  - 不同窗口（20/30/90/120）：待测
- **delay=0 的其他因子**：liabcurr/assets(S=1.49, check FAIL), sp(liabcurr/a)(S=1.65, check FAIL), ts_rank(cf/ev)(S=1.84, check FAIL) —— delay=0 下部分因子有 LOW_SHARPE/LOW_FITNESS 等 check 失败

#### TOP1000 universe（无效）
- TOP1000 下所有因子表现更差：liabcurr/assets S=1.15, sp(liabcurr/a) S=1.10, ts_av_diff(cf/ev) S=1.44 F=0.95
- 结论：这些因子在中小盘（TOP3000）上效果更好，大盘股（TOP1000）上不达标

#### 当前有效方法论汇总（8 个 ACTIVE Alpha）
1. 负债比率：liabilities/assets, liabilities_curr/assets, liabilities_curr/cap
2. cf/ev 时序排名：group_neutralize/group_rank + ts_rank(cf/ev, 60) + decay
3. **cf/ev 偏离度：group_rank + ts_av_diff(cf/ev, 60)**（delay=0 或 1）
4. **signed_power 压缩：signed_power(liabcurr/assets, 0.5)**

### 2026-08-30 第八轮挖掘（第 9 个因子——未找到，配额还空）

#### 配额确认（权威 API）
- **提交活动**：`GET /users/self/activities/submissions` → records `[['08-15',1],['08-27',1],['08-28',3],['08-29',3]]`，本月 8 个
- 今日 3 个新 Alpha（vRjG1Jzw/QP7z069Q/1YwKML56）计入**美东 8-29** 配额日
- 当前美东 8-30 03:00 已重置，**8-30 配额窗口尚未使用** → 仍有提交机会
- **瓶颈**：UNSUBMITTED 池 34 个达标候选全部是与已提交的"同族"（ts_av_diff 变体 13 + 单调变换 12 + 其他），提交必被 SELF_CORRELATION 拒绝

#### 第 49-52 轮新方向（30+ 候选全部 FAIL）
- **时序平滑聚合（全部无效）**：
  - `ts_mean(cf/ev, 60/120/250)`：S=0.38~0.41（cf/ev 月度数据均值变化小）
  - `ts_product(cf/ev, 60)`：S=0.13
  - `ts_sum(cf/ev, 60)`：S=0.44
  - `ts_scale(cf/ev, 60)`：S=1.72 F=1.00 达标但与 cf/ev 族相关，被拒（ts_scale 与 ts_rank 同族）
- **股息/盈利类（全部无效）**：
  - `cashflow_dividends/ev`：S=-0.10（且 CONCENTRATED_WEIGHT FAIL）
  - `cashflow_dividends/cap`：S=0.59
  - `eps/close`：S=0.03
- **研发/资本支出/人均（全部无效）**：
  - `rd_expense/revenue`：S=-0.21；`capex/revenue`：S=0.00（CONCENTRATED_WEIGHT FAIL）
  - `revenue/employee`：S=-0.32；`depre_amort/revenue`：S=0.23
- **税率/费用率（全部无效）**：
  - `income_tax/income`：S=0.22；`sga_expense/revenue`：S=0.2 左右

#### 结论
- TUTORIAL 环境下有效因子家族（负债比率 + cf/ev 时序类）已全部提交并饱和
- 尝试过的新方向（股息/eps/rd/capex/员工/折旧/税率/SGA + 时序平滑聚合）全部无预测力
- **第 9 个因子需要更强的模型先验或更换账号权限（非 TUTORIAL）才能突破**

## 10. 跨数据集组合因子突破（8-31 凌晨）

### 10.1 探测的新数据集（全部单独不达标）
- **option8（64字段）**：期权波动率（historical_volatility, implied_volatility_call/mean/skew）
  - 所有因子 S<0.8，turnover 高（90-130%），CONCENTRATED_WEIGHT FAIL
- **model51（16字段）**：风险指标（beta, correlation, systematic/unsystematic_risk）
  - 所有因子 S≈0，无预测力
- **news18（121字段）**：新闻情绪（nws18_ssc/qep/nip/qcm/bee 等）
  - **关键**：event inputs，不支持 group_rank/ts_mean/ts_rank/ts_delta 等普通算子
  - 用 vec_avg 转换后 S≈0，turnover 120-140%
- **socialmedia12（18字段）**：社交媒体情绪（scl12_sentiment/buzz, snt_value）
  - S 为负，turnover 120%+
- **pv1（24字段）**：价格量数据（close/open/high/low/volume/vwap/adv20/returns/sharesout）
  - `group_rank(-ts_rank(close, 20), industry)` S=1.40 F=0.70 — **Sharpe 够但 Fitness 不够**
  - 增加 decay 降低 turnover 但 Sharpe 也同步下降，无法两全

### 10.2 突破：fundamental6 × pv1 组合因子
- **关键发现**：将 fundamental6 的负债率因子与 pv1 的价格反转因子**相加组合**，S 和 F 同时大幅提升
- **成功提交的 3 个组合因子**：
  1. `group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 20), industry)` — S=2.11 F=1.31 id=1YwRK1wW
  2. `group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 10), industry)` — S=2.49 F=1.45 id=9qX3M2mq
  3. `group_rank(liabilities_curr/assets, industry) + group_rank(-ts_rank(close, 5), industry)` — S=2.74 F=1.42 id=kqjpepz8
- **被拒的组合因子**：
  - `liabilities_curr/cap + 反转20`：SELF_CORRELATION=0.7591
  - `liabilities_curr/assets + 反转30`：SELF_CORRELATION=0.9804（与 #1 太相关）
- **lookback 选择**：5/10/20 日反转互相不相关，30 日与 20 日相关 0.98
- **原因分析**：负债率（基本面）提供截面排序信号，价格反转（量价）提供时变信号，两者低相关，组合后信号叠加增强
- **教训**：单数据集饱和后，跨数据集组合是突破方向

### 2026-09-03 第七轮挖掘（成功提交 2 个新 Alpha）

#### 关键突破：decay=8 + 全新基本面趋势信号

**成功提交**：
1. `group_rank(ts_av_diff(cash/assets, 30), industry) + group_rank(-ts_rank(close, 5), industry) + group_rank(-ts_corr(close, volume, 20), industry)` decay=8 — S=1.71 F=1.23 id=akLqqmm6
2. `group_rank(ts_av_diff(ebit/enterprise_value, 30), industry) + group_rank(-ts_rank(close, 5), industry) + group_rank(-ts_corr(close, volume, 20), industry)` decay=8 — S=1.90 F=1.46 id=A10MYm3d

**关键发现**：
- **decay=8 是突破 SELF_CORRELATION 0.7 阈值的关键**：
  - decay=0（默认）相关 0.74，decay=4 相关 0.7089，decay=8 通过！
  - decay=8 同时降低 turnover（从 59% 降到 20%），提升 Fitness
- **全新基本面趋势信号**（30日 ts_av_diff）：
  - `cash/assets` 趋势：现金比率的变化趋势
  - `ebit/enterprise_value` 趋势：EBIT/EV 的变化趋势
- **30日 lookback 最优**：60日与已有 cf/ev 60日趋势相关 0.90+，30日独立

**被拒的变体（全部 SELF_CORRELATION 0.7+）**：
- 负债率变体（倒数、zscore、tsdelta）：相关 0.82-0.86
- debt/assets、debt_lt/assets：与 liabilities_curr/assets 相关 0.82-0.83
- EBITDA/EV 趋势：与 cf/ev 趋势相关 0.87-0.90
- equity/assets、capex/assets、cogs/assets、depre_amort/assets 趋势：与 ebit/ev 或 cash/assets 相关 0.89+
- ebit/ev + cash/assets 组合：相关 0.74-0.79（两个新信号组合仍与已提交相关）
- 不同 decay（10/12/16/20）：与已提交的 decay=8 版本相关 0.93+
- 不同 lookback（10/20/60/120）：与 30日版本相关 0.91+
- analyst4 分析师数据：信号太弱（S<0.6），加反转后 turnover 73%+
- returns 因子：turnover 130%+，Fitness 不够
- 全新量价信号（vwap、振幅、量比、arg_max）：S<1.1 或不达标

**教训**：
- **decay 是调节相关性的关键参数**：decay=8 同时降低相关性、turnover，提升 Fitness
- **全新基本面字段是突破方向**：cash/assets 和 ebit/ev 与负债率/cf/ev 不相关
- **30日 ts_av_diff 是构造趋势因子的有效算子**：比 60日更独立
- **表达式结构变化（乘法、group_neutralize、group_zscore）效果有限**：乘法 S 为负，group_neutralize F 不够，group_zscore 相关 0.91+

#### 9/3 深夜续挖：全部数据集系统性探索（未找到第 3 个）

**fundamental6 继续探索**：
- 利润类字段趋势全部与 ebit/ev 相关 0.89-0.97：oiadp/assets(0.898)、pi/assets(0.891)、ebitda/assets(0.904)、cflow/assets(0.898)、eps(0.890)、equity/assets(0.907)、FCF/EV趋势(0.967)、NI/EV趋势(0.972)
- 资产负债表类信号弱：存货(F=0.77)、应付(F=0.81)、ppent(S=1.13)、intan(S=1.16)
- **应计异象** -(NI-CFO)/assets：S=1.80 F=1.35 但相关 0.8147（历史最低之一）
- **资产周转率** rev/assets：S=1.71 F=1.35 但相关 0.8004
- 融资现金流趋势 -ts_av_diff(cashflow_fin/assets,30)：S=1.55 F=1.03 相关 0.896（与cash/assets同属现金流维度）
- 净现金类全无效：(cash-debt)/ev S=0.09、cash/debt S=0.44
- B/M(equity/cap) S=1.17、E/P(eps/close) S=1.16 均不够
- **fnd6_emps 是 event inputs 不能做除法**；fnd6_cptmfmq 季度字段 oibdpq/atq 趋势 S=1.69 F=1.14 相关 0.889

**model16（24字段，新探测）**：基本面评分全弱
- fscore_bfl_value/quality/profitability/growth/momentum/surface 单独 S=0.35-0.47，加 PV 组合后 S=0.13-0.92，全部不达标
- 结论：评分月度更新，日频预测力弱

**option9（74字段，新探测）**：期权 PCR 覆盖度不足
- pcr_vol/oi 单独 S 为负；加 PV 后 S=1.27-1.44 但 CONCENTRATED_WEIGHT FAIL
- 结论：仅约20-30%股票有期权，权重集中

**fundamental2（766字段，新探测）**：报表脚注信号普遍弱
- 回购强度 repurchased_shares/cap：单独 S=0.68；加 PV S=1.63 F=1.12 相关 0.77
- 养老金负债、租赁义务、重组费用、股权激励、增发：全部 S<1.2

**universe/delay 探索**：
- TOP1000/500/200 信号大幅减弱（S<1.0）— 小 universe 无效
- delay=0 阈值 S≥2.0 F≥1.3，新信号 S=1.78 不达标

**关键结论**：
1. **相关性瓶颈 = 量价部分**：ts_rank(close,5)+ts_corr(close,vol,20) 在 18 个 Alpha 中重复使用，任何组合相关 0.74+
2. **今天成功的本质**：cash/assets 和 ebit/ev 30日趋势是足够独特的基本面信号
3. **相关 0.8 附近候选**（<0.82）：应计(0.81)、周转率(0.80)、ebit+cash组合(0.74)、buyback+PV(0.77) — 都差 0.1+
4. **下一步建议**：寻找与 4 个已用基本面信号（负债率、cf/ev、cash/assets、ebit/ev）都不相关的第 5 维度；或等新权限；或用 ts_regression 等更复杂算子

#### 9/3 深夜重大突破：换量价结构再提交 3 个（当日共 5 个，目标达成）

**成功提交（当日 #3-5）**：
1. `group_rank(-(fnd6_newa2v1300_ni - cashflow_op)/assets, industry) + group_rank(-ts_av_diff(close, 20), industry)` dec=8 — S=1.27 F=1.07 id=QP3XalpK（应计异象+价格趋势）
2. `group_rank(fnd6_mfma2_revt/assets, industry) + group_rank(-ts_av_diff(close, 20), industry)` dec=8 — S=1.54 F=1.41 id=wpYgReRx（资产周转率+价格趋势）
3. `group_rank(-(ni - cfo)/assets) + group_rank(rev/assets) + group_rank(-ts_av_diff(close, 20))` dec=8 — S=1.91 F=1.74 id=MP1mQRro（应计+周转率+价格趋势，当日最高分）

**决定性发现**：
- **价格趋势 -ts_av_diff(close,20) 替代 rev5+corr20 是绕开相关性的钥匙**：
  - 相关性瓶颈的本质是与 #17/#18 相同的量价结构（rev5+corr20）
  - 换成 -ts_av_diff(close,20)（20日价格均值差）后，应计/周转率信号立即通过
  - 二因子结构（基本面+价格趋势）turnover 仅 11-12%，Fitness 反而更高
- **二因子优于三因子**：加 rev5 或 corr20 立即被拒（相关 0.89-0.97）
- **应计异象、资产周转率之前被拒的原因**：不是信号不行，是量价结构重叠
- **其他探测**（信号弱）：ts_regression 残差动量 S=0.38、低波动异象 S≈0、vol_adj_ret S=0.65、ts_max/ts_min 不可用

**新成功公式**：
```
group_rank(全新基本面, industry) + group_rank(-ts_av_diff(close, 20), industry)，decay=8
```
- 二因子即可达标（F 1.07-1.41），turnover 11-12%
- 可叠加多个基本面信号（三因子 S=1.91 F=1.74）
- 切勿再加 rev5/corr20（会与 #17/#18 重叠被拒）

#### 9/4 凌晨收尾探测：新公式信号池饱和

提交 5 个后继续挖（新公式二因子），结果：
- ebit/ev + 价格趋势：相关 0.7733（与 #18 同基本面字段重叠）
- cash/assets + 价格趋势：F=0.98（与 #17 同字段，差 0.02）
- 毛利润率 gp/assets + 价格趋势：相关 0.9192（与应计/周转率相关）
- eps/close、equity/cap、cfo/assets、ebit/assets、存货/收入、流动比率：S 全部 <1.1

**结论**：当日 5 个成功因子已占用最独特的信号组合（cash/assets、ebit/ev、应计、周转率 × 两种量价结构），第 6 个需要新的独立信号维度或等新权限。

**明日（9/4）建议**：
1. 应计/周转率变体：不同 lookback（30/90 日 ts_av_diff）、分母换 cap
2. 组合未测字段：depre_amort/rev、capex/cfo、fnd6_mfma1_capx/assets
3. 价格趋势换 lookback：-ts_av_diff(close, 30/60)（注意 30 日与 20 日相关 0.98 的历史教训，但不同基本面组合下可能不同）
4. fnd6_cptnewqv1300_req（留存收益）/assets 趋势

#### 9/4 探测：美东日切换后的信号池验证（已饱和）

**时区修正**（用户指出）：WQ 平台按美东日期计天。之前记录的"09/03 提交 5 个"实为美东 9/3 提交 4 个（akLqqmm6 10:14、A10MYm3d 11:05、QP3XalpK 23:57、wpYgReRx 23:58）+ 美东 9/4 提交 1 个（MP1mQRro 00:09）。北京时间 = 美东 + 12h；美东日切换在北京时间中午 12 点；北京凌晨 3 点 = 美东 15 点（数据更新）。

**美东 9/4 探测结果（~20 个候选全部被拒或不达标）**：
- 留存收益 req/assets：S=1.23 弱；req/cap 趋势 F=0.89
- capex/cfo：S=0.30 无效；capex/assets：S=0.64
- depre_amort/rev：S=1.40 F=1.16 但相关 0.8674（与周转率同属规模类）
- 存货、应付/存货、商誉：S<0.9；fnd6_gdwls 是 event inputs
- 三因子组合（毛利率+周转率+价格趋势）S=1.19；留存收益+周转率 S=0.80
- 应计/cap 分母：S=1.18；周转率/cap 分母：相关 0.8256（与 #20/#21 重叠）
- 毛利率+应计+价格趋势：相关 0.9223（与 #21 重叠）
- 价格趋势 60 日变体：相关 0.8278（与 20 日价格趋势重叠）
- cfo/rev 趋势：S=0.97

**结论**：
- 美东 9/4 已提交 1 个（MP1mQRro），Days of Submission 已保住
- 5 个新信号（cash/assets、ebit/ev、应计、周转率、价格趋势20）已全部占用，任何变体相关 0.82+
- 第 22 个需要等待：新数据集权限、或完全未探索的表达式结构
- 每日"保底 1 个 + 有余力冲 5 个"策略不变

#### 9/4 重大突破：收益率排名 -ts_rank(returns,20) 是第7维价格信号

**成功提交 4 个新 Alpha（美东9/4 共 5 个，目标达成）**：

| ID | 表达式 | S | F | 时间 |
|------|--------|---|---|------|
| om6ea8j6 | gr(应计) + gr(-ts_rank(returns,20)) dec=8 | 2.00 | 1.25 | 06:14 |
| RRVLeabj | gr(周转率) + gr(-ts_rank(returns,20)) dec=8 | 1.61 | 1.09 | 06:17 |
| 58QVJA9M | gr(cash/assets趋势30日) + gr(-ts_rank(returns,20)) dec=8 | 2.15 | 1.27 | 06:19 |
| 6XrbGx1L | gr(应计)+gr(周转率)+gr(-ts_rank(returns,20)) dec=8 | 2.26 | 1.75 | 06:23 |

**决定性发现**：
- **-ts_rank(returns, 20) 与 -ts_av_diff(close, 20) 不相关**：returns 是日收益率，close 是价格水平，ts_rank 衡量排名位置
- **S 更高**：应计+returns排名 S=2.00 vs 应计+价格趋势 S=1.27；三因子 S=2.26 F=1.75（当日最高分）
- **turnover 更高**：22-29% vs 11-12%（价格趋势），但 Fitness 仍达标
- **ebit/ev趋势+returns排名 被拒**（相关0.7517）：ebit/ev趋势与cash/assets趋势在 #17/#18 中重叠

**新成功公式2**：
```
group_rank(全新基本面, industry) + group_rank(-ts_rank(returns, 20), industry)，decay=8
```

**本轮无效方向汇总**：
- 90/120日价格趋势：S=0.77-1.23（窗口太长信号弱）
- ts_zscore(close,20)：S=1.15（不如 ts_av_diff）
- vwap 替代 close：相关0.9992（vwap≈close）
- volume 趋势：S=0.61-0.77（成交量无预测力）
- 利润率类（毛利率/净利率/ROE/ROA）：S=0.58-1.06（信号弱）
- liab/equity：S=1.62 但相关0.82（与负债率同维度）
- cfo/liab、liabcurr/liab、负债率趋势、毛利率趋势、净利率趋势：S<1.1
- 存货周转率、应付周转率、现金流利润率、EBIT利润率：S<1.1

**关键结论**：
- 7 个信号维度已全部占用：负债率、cf/ev、cash/assets、ebit/ev、应计、周转率、价格趋势20、收益率排名20
- 两种价格信号（-ts_av_diff(close,20) 和 -ts_rank(returns,20)）可分别组合同一基本面
- 第 26 个需要新数据集权限或完全未探索的表达式结构

#### 9/5 重大突破：SUBINDUSTRY 中性化突破相关性瓶颈（58Q7kl1z）

**成功提交**：`gr(cash/assets趋势) + gr(ebit/ev趋势) + gr(-ts_rank(returns,20))` SUBINDUSTRY dec=8 — S=2.14 F=1.49 id=58Q7kl1z（美东9/5 04:59）

**SUBINDUSTRY 突破的边界**：
- cash+ebit双趋势+ret20：INDUSTRY 相关 0.7103（被拒）→ SUBINDUSTRY 通过（相关 <0.7）
- ebit单趋势+ret20：INDUSTRY 相关 0.7517 → SUBINDUSTRY 仍 0.916 被拒（与 58Q7kl1z 的 ebit 成分直接重叠）
- **规律**：相关 0.70-0.75 的组合若与已提交 Alpha 成分不重叠，SUBINDUSTRY 可救；成分重叠则救不了
- decay 越大相关性越高（0.7103→d10 0.7206→d12 0.7268→d16 0.7288），反向操作无效
- MARKET/SECTOR 与 INDUSTRY 相关 0.97+，不能绕过（58Q7kl1z 已占用该表达式空间）
- 表达式内 subindustry 分组：相关 0.98+，同样无效

**delay=0 探索（美东9/5）**：
- delay=0 字段集不同：fnd6_newa2v1300_ni 不可用，income/ebit/cash/assets_curr/interest_expense/return_assets 可用（342字段）
- cash+ebit+ret20 delay=0：S=1.96 F=1.38（差 0.04 达不到 S≥2.0）；d4/d12/d16/t0.02/四因子均无法提升
- delay=0 应计（income 替代 NI）：S=0.56-1.02 信号弱
- delay=0 流动比率 assets_curr/liab_curr：S=-0.39；利息保障 ebit/int_exp：S=-0.08
- 结论：delay=0 是独立维度但信号普遍弱于 delay=1，S≥2.0 阈值难达成

**STATISTICAL 中性化不可用**（TUTORIAL 权限限制，400 错误）

**新无效方向**：
- liab+cf/ev趋势+ret20：S=2.69 F=2.37 超强但相关 0.8336（负债率系重叠）
- 四因子 cash+ebit+turnover+ret20：S 反而降（1.83-2.14），因子过多稀释信号
- ts_zscore(returns,20)/ts_av_diff(returns,20)：与 ts_rank(returns,20) 相关 0.93-0.998
- cash_ebit_ret20 相关 0.7103 的全部参数变体（decay/trunc/中性化/分组）均无法通过

**待探索**：pv1 的 high/low/open 字段（振幅、日内位置）、高阶算子（ts_co_skewness 等）

#### 9/5 pv1 新字段探索（全部无效）
- 威廉%R (close-low)/(high-low)：S=-0.38（无信号）
- 日内收益 -close/open：S=1.85 F=1.25 达标但相关 0.8889（与 ret20 系重叠，同为收益率反转）
- 长窗口量价 -ts_corr(close,volume,60)：S=1.05（信号弱）
- 振幅 -ts_mean((high-low)/close,20)：S=0.10-0.12（无信号）
- 结论：high/low/open 衍生信号要么无预测力，要么与已提交收益率反转本质相同

#### 9/4-9/5 会话总结
**成果**：
- 美东 9/4：5 个（MP1mQRro、om6ea8j6、RRVLeabj、58QVJA9M、6XrbGx1L）
- 美东 9/5：1 个（58Q7kl1z，SUBINDUSTRY 突破）
- 累计 26 个 ACTIVE Alpha，IS Score 约 5,000

**新目标策略**（排名前100）：
- IS Score 是累计值且是最大短板（5,000 vs 前100估算门槛 8,000-10,000）
- 每天 3-5 个高质量提交，每天 +500-1500 分，4-8 天达标
- Days of Submission 每天+1（当前10天，需30天）
- Uniqueness 保持 0.43+

**信号池状态**：26 个 Alpha 后极度饱和。已穷尽：8个基本面维度 × 3种价格信号 × 4种中性化 × 2种delay × 全参数空间。下一个突破口依赖：新权限数据集、或全新算子结构（ts_regression 残差组合等）。

#### 9/6 遗憾规避思想落地：阴线量占比信号突破（A10a7pdY，第27个）

**背景**：用户分享论坛"遗憾规避因子"（研报：基于逐笔成交数据，详见 docs/idea_regret_factor.md）。论坛原版 volsig 结构 S=0.78 T=150% F=0.13 不可用（ILLIQUID_MINVOL1M universe TUTORIAL 无权限）。

**成功提交（第27个）**：
`gr(ts_sum(if_else(close<open,volume,0),5)/ts_sum(volume,5), industry) + gr(rev/assets, industry) + gr(-ts_rank(returns,20), industry)` SUBINDUSTRY dec=8 — S=2.32 F=1.54 id=A10a7pdY（美东9/6 04:19）

**挖掘路径（8批~40个候选）**：
1. 量占比类全弱：阴线量20日(-0.89)、净方向量(0.06)、上涨日量占比(0.23)、跳空(-0.37)、上下影线(≈0)
2. 价格盈亏偏离类全弱：量加权成本偏离(0.38)、套牢盘HCP(0.06)、割肉盘LCP(0.80)
3. **转折点：阴线量5日占比翻转方向**（-1.24 → +1.24），单独 S=1.24 F=0.66
4. +ret20 二因子：S=1.68 F=0.98（差0.02）；decay=10/12 反而降（1.56/1.45）
5. SUBINDUSTRY 二因子：S=1.81 F=1.01 PASS 但相关 0.8047
6. 三因子 + 周转率：S=2.09 F=1.45 相关 0.7963；+ ebit：S=1.87 相关 0.8092
7. PT20 替代 ret20：全部更差（S=1.16-1.82，相关 0.89-0.92）
8. **yin5f+turnover+ret20 SUBINDUSTRY：S=2.32 F=1.54 相关<0.7 通过！**

**关键教训**：
- **信号方向必须实测**：阴线量占比直觉是"抛压大→负向"，实测翻转后（阴线量高=承接活跃→正向）才有效
- **重叠度与 SUBINDUSTRY 救援边界**：yin5f+ret20 INDUSTRY 相关 0.80、+turnover 0.7963，SUBINDUSTRY 恰好推过线；但 A10a7pdY 提交后 yin5f+liab+ret20 SUBINDUSTRY 相关 0.863（新Alpha成为相关源，同骨架组合立即封闭）
- **LOW_SUB_UNIVERSE_SHARPE 无解**：acc+cash+ret20 SUBINDUSTRY S=2.03-2.23 F=1.49-1.56，dec=8/16 均因子池 Sharpe FAIL
- **回购字段纠正**：repurchased_shares 不存在；正确字段 fn_repurchased_shares_value_q/a、common_stock_repurchase_payment，但信号极弱（S=0.24-0.43）
- if_else 嵌套（内含乘法/比较）语法合法，可构建复杂条件量价结构

**阴线量占比信号本质**：下跌日（close<open）成交量占比高 = 下跌中有承接，未来反弹——"遗憾规避"的日频 OHLCV 近似变体（第9维信号）。

**9/6 遗留待挖**：yin5f+cfev趋势、yin 窗口 3/10 日变体（相关风险高）、新字段型信号需等数据集权限。

#### 9/6 续挖：yin窗口变体 + 新算子 + close/vwap 信号探索（全部未达标）

**yin 窗口变体（3/10日，与 A10a7pdY=yin5 同族）**：
- yin3+turnover+ret20 SUBINDUSTRY：S=2.38 F=1.55 PASS 但相关 0.9822（同族）
- yin10+turnover+ret20：S=2.08 F=1.38 FAIL（F不够）
- yin3+cfev_tr+ret20：S=2.26 F=1.50 PASS 但相关 0.7863
- yin3+acc+ret20：S=1.93 F=1.15 FAIL
- yin10+cash_tr+ret20：S=1.76 F=1.06 FAIL
- **结论**：yin 窗口 3/10 与 yin5 本质同族，相关 0.78-0.98，方向饱和

**高阶矩算子（TUTORIAL 不可用）**：
- ts_co_skewness：未知算子，400 错误
- ts_kurtosis：未知算子，400 错误
- ts_std_dev(returns,20)：S=0.34-0.41 极弱（低波动异象在 TOP3000 无效）
- ts_corr(returns, ts_delta(volume,1), 20)：S=1.55-1.57 F=0.86-1.03（F不够）

**新结构/新字段探索**：
- trade_when(volume>ts_mean, -ts_rank(returns,20), 0)+turnover：S=1.24 F=0.76 FAIL
- -close/vwap+ret20：S=2.08 F=1.03 T=65.1% FAIL（TO太高）
- -ts_rank(volume/adv20,20)+ret20：S=1.32 F=0.51 FAIL

**close/vwap 信号深度优化（第10维新信号，但 F 边缘）**：
- -close/vwap+turnover+ret20 SUBINDUSTRY dec=8：S=2.41 F=1.48 T=37.4% **差0.02达标**
- -close/vwap+turnover+ret20 dec=10：S=2.32 F=1.50 PASS 但相关 0.8986（turnover+ret20骨架与A10a7pdY重叠）
- -close/vwap+turnover+ret20 dec=12：S=2.23 F=1.51 PASS 但相关 0.9098
- -close/vwap+acc+ret20：S=2.17 F=1.22 FAIL
- -close/vwap+cash_tr+ret20：S=2.33 F=1.31 FAIL
- ts_rank(close/vwap,5/10)+turnover+ret20：S=2.02-2.30 F=1.07-1.25 FAIL（ts_rank包装反降F）
- 二因子 cvwap+turnover dec=12/16：S=1.60-1.70 F=1.25-1.28 FAIL（S降太多）
- 二因子 cvwap+cash_tr dec=12：S=1.91 F=1.13 + LOW_SUB_UNIVERSE_SHARPE FAIL
- **结论**：close/vwap 是有希望的第10维信号（收盘价与VWAP偏离=日内价格压力），但 turnover 37%+ 拖累 F，三因子 F=1.48-1.51 边缘达标但与 A10a7pdY 的 turnover+ret20 骨架相关 0.89+

**9/6 总结**：美东9/6 提交 1 个（A10a7pdY），保底达成。续挖 ~35 个候选全部未达标或被相关拒绝。信号池 27 个 Alpha 后极度饱和，9维信号 + close/vwap（边缘）已穷尽。下一个突破口依赖：新权限数据集、或完全未探索的算子/字段。

#### 9/6 续挖第二批（~55个候选，ret10/ret40 + delay=0 + close/vwap平滑，全部饱和）

**ret10/ret40 替代 ret20（returns ts_rank 不同窗口同族）**：
- cvwap+turnover+ret10：S=2.37 F=1.43 FAIL（F差0.07）
- cvwap+turnover+ret40：S=2.40 F=1.48 FAIL（F差0.02，同 ret20）
- acc+turnover+ret10：S=2.29 F=1.65 PASS 但相关 0.934（与 #25 6XrbGx1L=acc+turnover+ret20 相关）
- yin5+turnover+ret10：S=2.37 F=1.56 PASS 但相关 0.9885（与 A10a7pdY 相关）
- cash+ebit+ret10：S=2.10 F=1.43 FAIL
- **结论**：returns 的 ts_rank 不同窗口（10/20/40）本质同族，相关 0.93+（与 close 的 ts_rank 5/10/20 互不相关不同）

**delay=0 变体（字段集不同，信号普遍弱）**：
- delay=0 fnd6_mfma2_revt/fnd6_newa2v1300_ni 不可用；用 revenue/assets、-(income-cashflow_op)/assets 替代
- cvwap+revenue/assets+ret20 delay=0：S=1.56 F=0.79 FAIL
- yin5+revenue/assets+ret20 delay=0：S=1.61 F=0.93 FAIL
- cvwap+acc_d0+ret20 delay=0：S=0.93 F=0.39 FAIL
- **结论**：delay=0 下 revenue/assets 信号弱于 fnd6_mfma2_revt/assets，close/vwap 和 yin5 也弱了很多

**trade_when 条件结构（信号弱）**：
- trade_when(volume>adv20, -ts_rank(returns,20), 0)+turnover：S=1.23 F=0.75 FAIL
- trade_when(returns<0, -ts_rank(returns,20), 0)+turnover：S=1.10 F=0.62 FAIL

**close/vwap 平滑包装 + decay 提 F（质量达标但相关 0.89+）**：
- ts_mean(close/vwap,5)+turnover+ret20：S=2.09 F=1.39 FAIL
- ts_mean(close/vwap,10)+turnover+ret20：S=2.08 F=1.46 FAIL（F差0.04）
- ts_decay_linear(close/vwap,5)+turnover+ret20 dec=8：S=2.23 F=1.48 T=30% FAIL（F差0.02）
- **ts_decay_linear(close/vwap,5)+turnover+ret20 dec=10：S=2.18 F=1.53 PASS 但相关 0.8968**
- **ts_decay_linear(close/vwap,5)+turnover+ret20 dec=12：S=2.12 F=1.55 PASS 但相关 0.8943**
- cvwap+ebit_tr+ret20 dec=10：S=2.27 F=1.46 FAIL
- cvwap+cash_tr+ret20 dec=10：S=2.28 F=1.33 FAIL
- trunc=0.04：S=2.32 F=1.50 PASS 但相关 0.8986（truncation 不改变相关性）
- **结论**：ts_decay_linear 平滑降 TO 提 F 有效（F=1.53-1.55 达标），但 turnover+ret20 骨架与 A10a7pdY 相关 0.89+ 无法避免。即使第一因子从 yin5 变成 ts_decay_linear(close/vwap,5)，相关性仍 0.89+，说明相关源是骨架（turnover+ret20）而非第一因子

**9/6 全天总结**：美东9/6 提交 1 个（A10a7pdY S=2.32 F=1.54），累计 27 个 ACTIVE Alpha。共探索 19 批 90+ 候选，全部未达标或被相关拒绝。信号池极度饱和：
- 9 维信号已占满（负债率/cf_ev/cash趋势/ebit_ev趋势/应计/周转率/价格趋势/收益率排名/阴线量占比）
- close/vwap 是第10维边缘信号（S强但F边缘，相关 0.89+ 无法突破）
- returns ts_rank 不同窗口（10/20/40）同族相关 0.93+
- delay=0 信号普遍弱，trade_when 信号弱，高阶矩算子不可用
- **下一个突破口依赖：新权限数据集、或完全未探索的算子/字段/结构**

#### 9/7 字段扫描法重大突破：5 个全新信号字段 + 3 个高质量 Alpha（第28-30个）

**背景**：9/6 探索 90+ 候选全部饱和后，转向系统性扫描 fundamental6 全部 886 字段（docs/scan_fnd6_fields.py，MATRIX 类型 574 个），筛选从未测试的字段构造单因子。

**字段扫描结果（单因子 S）**：
- 有潜力（S 0.8-1.4）：fnd6_xrent/assets 租金强度(1.33, 正向)、fnd6_xopr/assets 营业费用强度(1.17, 正向)、debt_st/assets 短期债务率(0.97, 正向)、assets_curr/assets 30日趋势(0.96)、fnd6_acdo/assets 趋势(0.81)
- 无效（|S|<0.8）：sales_growth(-0.29)、cashflow_invst趋势(0.37)、receivable/sales(-0.31)、inventory_turnover(0.30)、current_ratio趋势(0.10)、cash_st/cap(0.43)、xad/sales(-0.41)、sales_ps趋势(0.38)、bvps趋势(0.31)、oi/assets趋势(0.33)、pretax_ev趋势(0.74)、depre趋势(-0.67)、nopiq趋势(0.62)
- **关键发现：弱信号（S 0.8-1.3）三因子组合可达标**（阴线量占比 S=1.24 同路径先例）

**成功提交 3 个（美东9/7）**：
| ID | 表达式 | S | F | S+F |
|------|--------|---|---|-----|
| 883OXpJl | gr(fnd6_xrent/assets)+gr(ts_av_diff(assets_curr/assets,30))+gr(-ts_rank(returns,20)) SUBINDUSTRY dec=8 | 2.48 | 1.78 | 4.26（卓越线） |
| j23nOrVW | gr(fnd6_xrent/assets)+gr(fnd6_xopr/assets)+gr(-ts_corr(close,vol,20)) SUBINDUSTRY dec=8 | 1.92 | 1.51 | 3.43（最低线） |
| LL9n2Jp1 | gr(debt_st/assets)+gr(operating_expense/assets)+gr(-ts_rank(returns,20)) SUBINDUSTRY dec=8 | 2.22 | 1.57 | 3.79（优先线） |

**组合相关性规则（本日实证）**：
- 新三因子与已有 Alpha 共享 **1 个因子**（如 ret20 或 corr20）→ 通过（883OXpJl、LL9n2Jp1、j23nOrVW）
- 共享 **2 个因子**（如 xrent+ret20 或 surr+xopr）→ 被拒（pwPn3jqq 0.731、QP3n62Mg 0.7954、QP3noeL5 0.8282）
- 提交顺序影响后续候选：883OXpJl 提交后，含 xrent+ret20/xopr 的同源候选全拒（新Alpha即封印）

**方法论沉淀**：
1. **字段扫描法**是信号池饱和后的有效突破：886 字段中只用过 ~15 个，还有大量未探索字段
2. 弱单因子（S 0.8-1.3）× 3 组合 + SUBINDUSTRY + dec=8 是可复制公式
3. 新字段全部正向（租金/费用/债务高=未来好），反直觉但一致——可能反映"经营扩张投入"逻辑
4. 被拒候选记录（次日可用新骨架变体回收）：QP3noeL5(surr+xopr+pt20 S=1.94 F=1.80 相关0.8282)、pwPn3jqq(xrent+xopr+turn+ret20 S=2.07 F=1.73 相关0.731)、QP3n62Mg(xrent+xopr+ret20 S=2.07 F=1.59 相关0.7954)

#### 9/7 续挖：S+F≥4.0 目标的两批失败（新字段空间确认穷尽）

**质量标准收紧（用户 9/7 反馈）**：j23nOrVW(S+F=3.43) 提交后被用户指出质量不达标。
新标准：**S+F≥4.0 才提交**（贡献 ~200分），3.4-3.8 的放弃（除非当天 0 提交的保底场景）。

**第五批（8个，新字段两两组合，全部 <4.0）**：
- xrent+debtst+pt20：S=1.80 F=1.62 S+F=3.42（最高但不够）
- surr+debtst+pt20：S=1.74 F=1.48 S+F=3.22
- opexp+acdo+pt20：S=1.40 F=1.20 S+F=2.60
- surr+opexp+corr20：S=1.66 F=1.24 S+F=2.90
- debtst+surr+corr20：S=1.24（LOW_SHARPE FAIL）
- xrent+acdo+pt20：S=1.62 F=1.52 S+F=3.14
- debtst+acdo+corr20：S=1.22 FAIL
- xrent+debtst+surr（纯基本面）：S=1.63 F=1.21 S+F=2.84

**第六批（8个，xrent/cap 分母变体 + 冷门字段，全部 <3.5）**：
- **xrent/cap 单因子 S=0.91**（远弱于 xrent/assets 的 1.33，分母换 cap 削弱信号）
- xrent_cap+debtst+pt20：S=1.45 S+F=2.85
- nopiq+debtst+pt20：S=1.68 S+F=3.04
- pretax+xrent_cap+ret20：S=1.71 S+F=3.04
- 其余全部 <2.96

**结论**：
1. 新字段强组合只有 3 对：xrent+surr_tr（4.26）、xrent+xopr（3.66）、debtst+opexp（3.79），已全部提交
2. 其他两两组合 S+F 3.0-3.4，达不到 4.0 标准
3. xrent/cap 分母变体严重削弱信号（0.91 vs 1.33）
4. 冷门字段（nopiq/pretax/depre/xad/acdo）单独或组合都弱
5. **fnd6 字段扫描空间已穷尽**，下一批突破需要：等新 Alpha 相关性数据稳定后回收被拒候选、或新数据集权限