# Spec — WorldQuant Alpha 挖掘系统规格说明

> WHAT：系统应该做什么。变更本文件后必须同步更新 design.md 和 tasks.md。

## 1. 功能需求

### FR-1 登录认证
- 系统通过 HTTP Basic Auth 登录 WorldQuant Brain API
- 凭据从 `brain_credentials.txt` 读取（JSON 数组 `[username, password]`）
- 支持断线重连

### FR-2 数据字段获取
- 分页获取指定数据集（如 fundamental6）的所有 MATRIX 类型字段
- 处理 API rate limit（等待 10~30s 重试，最多 5 次）

### FR-3 Alpha 表达式生成
- 支持多策略生成：
  - 策略 A：基础价值因子（group_rank + 行业/子行业中性化 + 时序排名）
  - 策略 B：价值 × 价格动量组合
  - 策略 C：多因子加法叠加
  - 策略 D：经典 WQ101 变体
  - 策略 E：基本面排名时序变化（趋势捕捉）
  - 策略 F：组内比较变体
  - 策略 G：质量因子（利润率稳定性）
  - **策略 H（发现于 08-30）：ts_av_diff 偏离度**：`group_rank(ts_av_diff(ratio, 60), industry)`，提取当前值相对时序均值的偏离度
  - **策略 I（发现于 08-30）：signed_power 压缩**：`signed_power(ratio, 0.5)`，压缩极端值
  - **策略 J（发现于 08-30）：delay=0 变体**：相同表达式用 delay=0 模拟，产生更强信号且与 delay=1 不相关
- 支持跨截面比率型批量生成（world4.py）

### FR-4 并发模拟
- 支持最大并发数控制（默认 3）
- 从 CSV 分批读取待模拟 Alpha
- 循环提交与轮询状态
- 失败重试（容忍上限 35 次），超限重新登录
- 结果写入日期命名 CSV，失败写入 fail_alphas.csv

### FR-5 筛选优质 Alpha
- Sharpe ≥ 1.25
- Fitness ≥ 1.0
- Turnover ∈ [1%, 70%]
- Checks 全部 PASS（容忍 SELF_CORRELATION = PENDING）

### FR-6 自相关性预检查
- 提交前调用 `/correlations/self` 预检查（免费）
- max_corr < 0.7 才提交，避免浪费每日配额

### FR-7 自动提交
- 通过筛选的 Alpha 自动提交
- 处理 503（已排队，继续轮询）、403（相关性失败）、200/201（成功）
- **提交后强制三连确认**（FR-7.1）

### FR-7.1 提交成功三连确认
- POST `/alphas/{id}/submit` 后必须执行：
  1. 轮询 `GET /alphas/{id}/submit` 至 Retry-After=0
  2. 独立 `GET /alphas/{id}` 验证 `status ∈ {ACTIVE, SUBMITTED}` 且 `dateSubmitted` 非空且 `stage = "OS"`
  3. 三个条件全部满足才判定"提交成功"，并将确认结果写入提交日志
- 任何一项不满足即判定失败并记录原因

## 2. 非功能需求

### NFR-1 性能
- API 请求间隔 ≥ 1s（避免 rate limit）
- 并发模拟数 ≤ 3（TUTORIAL 账号限制）

### NFR-2 健壮性
- 登录失败重试上限 30 次
- 模拟请求失败重试上限 35 次
- 会话过期自动重新登录

### NFR-3 可观测性
- 日志写入 simulation.log / find_alpha.log
- 控制台实时输出进度

## 3. 约束

- 凭据文件 `brain_credentials.txt` 不得提交到版本控制
- 表达式语言固定为 FASTEXPR
- 资产类型 EQUITY，区域 USA（TUTORIAL 权限仅支持 USA），universe TOP3000，delay 0 或 1
- universe 可用 TOP1000/TOP500，但同 region 下跨 universe 仍做自相关性检查

## 4. 变更记录

| 日期 | 变更 | 影响 |
|------|------|------|
| 2026-08-28 | 初始整理：删除 17 个临时脚本，建立 SDD 文档 | 重构 |
| 2026-08-30 | 新增策略 H/I/J：ts_av_diff 偏离度、signed_power 压缩、delay=0 变体 | 提交 3 个新 Alpha |
| 2026-08-30 | 新增 FR-7.1 提交成功三连确认 | 提交可靠性 |