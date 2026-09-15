# Design — WorldQuant Alpha 挖掘系统设计文档

> HOW：系统如何实现 spec.md 中的需求。本文件随 spec.md 变更同步更新。

## 1. 架构总览

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│  utils.py   │───▶│ 表达式生成器  │───▶│  模拟执行器  │───▶│  筛选+提交   │
│ (登录/字段) │    │(alpha_hunter │    │(AlphaSimulator│   │(find_and_   │
│             │    │ /world4)     │    │ /alpha_hunter)│   │ submit)     │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │ CSV 队列文件  │
                                       │(pending.csv) │
                                       └──────────────┘
```

## 2. 模块设计

### 2.1 utils.py — 公共工具层
- `sign_in() -> Session`：HTTP Basic Auth 登录，返回已认证 Session
- `get_datafields(s, searchScope, dataset_id, search) -> DataFrame`：分页获取数据字段，内置 rate limit 处理
- `submit_and_confirm(sess, alpha_id, timeout=240) -> (bool, dict)`：提交 Alpha 并执行三连确认（POST → 轮询 → 独立 GET 验证 status/dateSubmitted/stage），返回 (成功标志, 验证详情)

### 2.2 alpha_hunter.py — 多策略挖掘器
- 内联 7 大策略（A~G）生成候选列表 `cands: List[(name, expr, settings)]`
- 逐个提交模拟，轮询等待结果
- 筛选 + 自动提交通过的 Alpha
- 输出 CSV 结果 `alpha_hunter_results.csv`

**策略矩阵：**
| 策略 | 思路 | 模板 |
|------|------|------|
| A | 基础价值因子 | `group_rank(ratio, group)` / `group_rank(ts_rank(ratio,60), industry)` |
| B | 价值×动量 | `group_rank(ratio, industry) * momentum` |
| C | 多因子叠加 | `group_rank(v1, industry) + group_rank(v2, industry)` |
| D | WQ101 变体 | 量价相关、sqrt(hl)、sign 等 |
| E | 趋势捕捉 | `group_neutralize(ts_delta(rank(field), d), industry)` |
| F | 组内比较 | `group_rank(ts_rank(field,20)/ts_rank(ev,20), group)` |
| G | 质量因子 | 利润率稳定性、趋势、排名 |
| H | ts_av_diff 偏离度 | `group_rank(ts_av_diff(cf/ev, 60), industry)` ★有效 |
| I | signed_power 压缩 | `signed_power(liabcurr/assets, 0.5)` ★有效 |
| J | delay=0 变体 | 相同表达式 delay=0，信号更强且与 delay=1 不相关 ★有效 |

### 2.3 AlphaSimulator.py — 并发模拟管理器（生产级）
- `AlphaSimulator` 类，封装并发模拟逻辑
- 从 CSV 分批读取（batch_size=20），覆写原文件
- `max_concurrent=3` 并发控制
- 状态机：`load_new_alpha_and_simulate` ↔ `check_simulation_status`
- 结果写入 `simulated_alphas_{date}.csv`，失败写入 `fail_alphas.csv`

### 2.4 world4.py — 跨截面比率型生成器
- 模板：`group_neutralize(ts_op(rank(field)/rank(enterprise_value), days), industry)`
- 生成后追加到 `alpha_list_pending_simulated.csv`
- `is_submit=False` 时只生成不提交，交由 AlphaSimulator 处理

### 2.5 find_and_submit_alphas.py — 端到端流水线
- 登录 → 获取字段 → 生成候选 → 模拟 → 筛选 → 提交
- 内置 `simulate_and_wait()` 函数封装模拟+轮询

## 3. 关键设计决策

### 3.1 为什么用 CSV 而非数据库做队列
- 单机运行，数据量小（~千级）
- CSV 可人工检查、断点续传
- 无额外依赖

### 3.2 为什么 SELF_CORRELATION 容忍 PENDING
- TUTORIAL 权限下该 check 始终返回 PENDING（非 FAILED）
- 不阻止提交流程，详见 WQ_BRAIN_API.md §6

### 3.3 为什么预检查 `/correlations/self`
- 提交有每日配额限制
- 预检查免费，避免浪费配额

### 3.4 Retry-After 用 float 解析
- API 返回 `"5.0"` 而非 `"5"`，必须 `float()` 解析

## 4. Settings 默认值

```python
{
    "instrumentType": "EQUITY",
    "region": "USA",
    "universe": "TOP3000",
    "delay": 1,
    "decay": 0,              # alpha_hunter 用 0；hunt_final2 实测 dec=4 最佳
    "neutralization": "SUBINDUSTRY",  # 或 INDUSTRY
    "truncation": 0.01,
    "pasteurization": "ON",
    "unitHandling": "VERIFY",
    "nanHandling": "OFF",
    "language": "FASTEXPR",
    "visualization": False
}
```

## 5. 错误处理策略

| 错误 | 处理 |
|------|------|
| 429 CONCURRENT | 等待 30s 重试 |
| Rate limit | 指数退避 10×(attempt+1) |
| 会话过期 | 重新 sign_in() |
| 模拟 ERROR | 跳过该 Alpha |
| 提交 403 | SELF_CORRELATION 失败，记录相关性值 |
| 提交 503 | 已排队，继续轮询 GET |

## 6. 变更记录

| 日期 | 变更 |
|------|------|
| 2026-08-28 | 初始整理，合并 17 个临时脚本为 5 个核心模块 |
| 2026-08-30 | 新增策略 H/I/J，验证 delay=0 有效，记录 ts_av_diff/signed_power 方法论 |