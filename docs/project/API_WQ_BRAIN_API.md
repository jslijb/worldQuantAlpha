# WorldQuant Brain API 使用文档

> 本文档整理自 GitHub 开源项目和 Chrome DevTools 协议分析，非官方文档。
> 最后更新：2026-08-28

---

## 1. 基础信息

| 项目 | 值 |
|------|-----|
| Base URL | `https://api.worldquantbrain.com` |
| 认证方式 | HTTP Basic Auth（username, password） |
| 响应格式 | JSON |
| Accept Header | `application/json;version=2.0` |
| 每日重置时间 | 美国东部时间 3:00 AM（非午夜） |

---

## 2. 认证

### POST /authentication — 登录
```python
sess = requests.Session()
sess.auth = (username, password)
resp = sess.post('https://api.worldquantbrain.com/authentication')
# 成功返回: {"user": {"id": "XXX"}, "token": {"expiry": 14400.0}, "permissions": ["TUTORIAL"]}
```

### GET /authentication — 检查会话是否有效
### DELETE /authentication — 登出

---

## 3. 数据字段

### GET /data-fields — 获取可用数据字段
```
GET /data-fields?instrumentType=EQUITY&region=USA&delay=1&universe=TOP3000&dataset.id=fundamental6&limit=50&offset=0
```

**响应格式：**
```json
{
  "count": 500,
  "results": [
    {"id": "ebit", "name": "EBIT", "type": "MATRIX", ...},
    ...
  ]
}
```

**注意：**
- 格式是 `{count, results}`，没有 `next/previous`
- 不同权限能看到的字段不同（TUTORIAL 权限字段较少）
- API 有 rate limit，请求间隔建议 ≥ 1 秒
- 遇到 `{"message": "API rate limit exceeded"}` 需等待重试

---

## 4. 操作符

### GET /operators — 获取所有可用操作符
```python
resp = sess.get('https://api.worldquantbrain.com/operators')
operators = resp.json()  # 返回裸 JSON 数组，不是 {count, results}
```

**常用操作符分类：**

| 类别 | 操作符 |
|------|--------|
| 排名 | `rank`, `dense_rank`, `percentile` |
| 时序 | `ts_rank`, `ts_zscore`, `ts_mean`, `ts_std_dev`, `ts_sum`, `ts_corr`, `ts_delta`, `ts_delay`, `ts_return`, `ts_decay_linear`, `ts_arg_max`, `ts_arg_min`, `ts_step`, `ts_product`, `ts_covariance`, `ts_regression` |
| 分组 | `group_rank`, `group_zscore`, `group_neutralize`, `group_mean`, `group_std_dev` |
| 数学 | `abs`, `log`, `sign`, `power`, `signed_power`, `scale`, `sigmoid` |
| 条件 | `trade_when` |
| 其他 | `pasteurize`, `nanmask`, `last_diff_value`, `densify` |

---

## 5. 模拟（Simulation）

### POST /simulations — 提交模拟
```python
resp = sess.post('https://api.worldquantbrain.com/simulations', json={
    "type": "REGULAR",
    "settings": {
        "instrumentType": "EQUITY",
        "region": "USA",
        "universe": "TOP3000",
        "delay": 1,
        "decay": 0,
        "neutralization": "SUBINDUSTRY",
        "truncation": 0.01,
        "pasteurization": "ON",
        "unitHandling": "VERIFY",
        "nanHandling": "OFF",
        "language": "FASTEXPR",
        "visualization": False
    },
    "regular": "rank(ebit)/rank(enterprise_value)"  # Alpha 表达式
})
# 成功返回 201，Location 头包含轮询 URL
location = resp.headers['Location']  # 如 "/simulations/abc123"
```

### GET /simulations/{id} — 查询模拟进度
```python
resp = sess.get(location_url)
retry_after = float(resp.headers.get("Retry-After", 0))
if retry_after > 0:
    # 还在计算中，等待后重试
    time.sleep(retry_after)
else:
    # 完成，结果在 body 中
    result = resp.json()
    alpha_id = result.get("alpha")  # 拿到 alpha ID
```

**关键细节：**
- `Retry-After` 是 **float 字符串**（如 `"5.0"`），不是 int，必须用 `float()` 解析
- 模拟完成时 `Retry-After` 为 0，body 包含 `{"alpha": "xxx"}`
- 模拟失败时 body 可能包含 `{"status": "ERROR", "message": "..."}`

---

## 6. Alpha 详情

### GET /alphas/{id} — 获取 Alpha 完整信息
```python
resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}')
alpha = resp.json()
```

**响应结构（关键字段）：**
```json
{
  "id": "QP7Y80pr",
  "type": "REGULAR",
  "status": "UNSUBMITTED",
  "regular": "rank(ebit)/rank(enterprise_value)",
  "is": {
    "sharpe": 1.85,
    "fitness": 2.1,
    "turnover": 0.29,
    "returns": 0.09,
    "drawdown": -0.15,
    "checks": [
      {"name": "CONCENTRATED_WEIGHT", "result": "PASS", "value": ...},
      {"name": "LOW_SUB_UNIVERSE_SHARPE", "result": "PASS", "value": ...},
      {"name": "SELF_CORRELATION", "result": "PASS", "value": ...},
      ...
    ]
  }
}
```

**注意：** 模拟结果在 `is`（In-Sample）字段下，不是顶层字段！

### IS（In-Sample）通过标准

| 指标 | 要求 |
|------|------|
| Sharpe | ≥ 1.25 |
| Turnover | 1% ~ 70% |
| Fitness | ≥ 1.0 |
| Checks | 全部 PASS（或 PENDING） |

### Fitness 计算公式

```
Fitness = Sharpe × √(|Returns|) / max(Turnover, 0.125)
```

- `Returns` 是年化收益率（小数形式，如 0.10 = 10%）
- `Turnover` 是小数形式（如 0.35 = 35%）
- Fitness 同时奖励高 Sharpe 和高 Returns，惩罚高 Turnover
- 降低 `decay` 参数可降低 Turnover，但也会降低 Sharpe
- 实测经验：`decay=4` 是 Sharpe 和 Turnover 的最佳平衡点

### Checks 详解

| Check | 含义 | 注意 |
|-------|------|------|
| LOW_SHARPE | Sharpe ≥ 1.25 | |
| LOW_FITNESS | Fitness ≥ 1.0 | 用上面公式计算 |
| HIGH_TURNOVER | Turnover ≤ 70% | |
| LOW_TURNOVER | Turnover ≥ 1% | |
| LOW_SUB_UNIVERSE_SHARPE | 子 universe 的 Sharpe 达标 | |
| CONCENTRATED_WEIGHT | 权重不过度集中 | |
| SELF_CORRELATION | 自相关性检查 | **TUTORIAL 账号下状态始终为 PENDING，不阻止提交** |
| MATCHES_COMPETITION | 与竞赛 Alpha 不重复 | |

**重要发现：** SELF_CORRELATION 在 TUTORIAL 权限下始终返回 `PENDING`（非 `FAILED`），不影响提交流程。

---

## 7. 提交 Alpha

### POST /alphas/{id}/submit — 提交 Alpha
```python
# 注意：返回 503 不是错误，是"已排队"的信号！
resp = sess.post(f'https://api.worldquantbrain.com/alphas/{alpha_id}/submit')
# 200/201 = 已接受，503 = 已排队（需继续轮询），403 = 相关性检查失败
```

**提交后需要轮询 GET 同一 URL 获取最终结果：**
```python
resp = sess.post(f'https://api.worldquantbrain.com/alphas/{alpha_id}/submit')
# 然后轮询
while True:
    resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}/submit')
    retry = float(resp.headers.get("Retry-After", 0))
    if retry == 0:
        result = resp.json()
        # result 中包含 SELF_CORRELATION 检查结果
        break
    time.sleep(retry)
```

**关键细节：**
- `POST /alphas/{id}/submit` 返回 503 = **已排队**，不是错误
- SELF_CORRELATION 判定只在 submit 的轮询结果中，GET /alphas/{id} 不会返回
- 相关性阈值：`correlation >= 0.7` 会被拒绝（403）
- 每日提交有配额限制

### GET /alphas/{id}/correlations/self — 预提交相关性检查（免费）
```python
# 在 submit 之前检查，避免浪费每日配额
resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}/correlations/self')
# 响应: {"schema": ..., "records": ..., "min": 0.1, "max": 0.5}
# max < 0.7 才能提交成功
```

### GET /alphas/{id}/check — 检查 Alpha 状态
```python
# 注意：只能用 GET，POST 会返回 405
resp = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}/check')
```

---

## 8. 用户信息

### GET /users/self — 获取当前用户信息
### GET /users/self/alphas — 列出自己的 Alpha
```
GET /users/self/alphas?status=ACTIVE&filter=is.sharpe%3E%3D1.25&filter=is.fitness%3E%3D1&limit=50
```

**过滤语法（重要！）：**
- 比较运算符嵌在字段名中：`is.sharpe>=1.25`（不是 Django 的 `__gte` 形式）
- 多个 filter 是 AND 关系
- 支持运算符：`>`, `>=`, `<`, `<=`
- 示例：`is.fitness>=3`, `is.turnover<=0.7`

### GET /users/self/activities/{kind} — 获取活动记录
```
GET /users/self/activities/simulations  # 模拟活动
GET /users/self/activities/submissions  # 提交活动
```

---

## 9. Settings 参数说明

```python
settings = {
    "instrumentType": "EQUITY",     # 资产类型
    "region": "USA",                # 地区: USA, CHN, JPN, EUR, etc.
    "universe": "TOP3000",          # 股票池: TOP3000, TOP1000, etc.
    "delay": 1,                     # 延迟: 0=当日, 1=前一日（防前视偏差）
    "decay": 0,                     # 衰减: 0=不衰减, >0=平滑信号
    "neutralization": "SUBINDUSTRY", # 中性化: SUBINDUSTRY, INDUSTRY, SECTOR, MARKET, NONE
    "truncation": 0.01,             # 单票权重上限: 0.01=单只标的最大权重1%（非"去极值"）
    "pasteurization": "ON",         # 按池过滤（官方比喻名"巴氏消毒"）: ON=非Universe标的置为NaN（非处理异常值）
    "unitHandling": "VERIFY",       # 单位处理
    "nanHandling": "OFF",           # 缺失值处理: OFF=忽略
    "language": "FASTEXPR",         # 表达式语言
    "visualization": False          # 是否返回可视化数据
}
```

---

## 10. 常见错误

| 错误 | 原因 | 处理 |
|------|------|------|
| `API rate limit exceeded` | 请求太频繁 | 等待 10-30 秒重试 |
| `Attempted to use unknown variable "xxx"` | 表达式中使用了不存在的字段 | 检查字段名是否在 data-fields 中 |
| `Retry-After` 解析失败 | 值是 `"5.0"` 不是 `"5"` | 用 `float()` 解析 |
| 提交返回 403 | 相关性 ≥ 0.7 | 先用 `/correlations/self` 检查 |
| 提交返回 503 | 已排队，不是错误 | 继续轮询 GET 同一 URL |
| `POST /alphas/{id}/check` 返回 405 | 该接口已改为 GET-only | 用 GET 请求 |

---

## 11. 开源参考项目

| 项目 | 语言 | 作用 |
|------|------|------|
| [RussellDash332/WQ-Brain](https://github.com/RussellDash332/WQ-Brain) | Python | 最简单的 API 自动化示例 |
| [zhutoutoutousan/worldquant-miner](https://github.com/zhutoutoutousan/worldquant-miner) | Python | 完整的自动挖掘系统（含 LLM） |
| [wh0amibjm/brainapi-go-sdk](https://github.com/wh0amibjm/brainapi-go-sdk) | Go | 最完整的 API 文档和协议分析 |

---

## 12. 快速参考：完整流程

```python
from utils import sign_in, get_datafields
from time import sleep

# 1. 登录
sess = sign_in()

# 2. 获取数据字段
fields = get_datafields(sess, searchScope, dataset_id='fundamental6')

# 3. 构造 Alpha 表达式
expression = "group_neutralize(rank(ebit)/rank(enterprise_value), industry)"

# 4. 提交模拟
resp = sess.post('https://api.worldquantbrain.com/simulations', json={
    "type": "REGULAR",
    "settings": { ... },
    "regular": expression
})
location = resp.headers['Location']

# 5. 轮询等待结果
while True:
    progress = sess.get(location)
    retry = float(progress.headers.get("Retry-After", 0))
    if retry == 0:
        break
    sleep(retry)
alpha_id = progress.json()["alpha"]

# 6. 获取详情
detail = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}').json()
sharpe = detail['is']['sharpe']
fitness = detail['is']['fitness']
turnover = detail['is']['turnover']

# 7. 预检查相关性（免费）
corr = sess.get(f'https://api.worldquantbrain.com/alphas/{alpha_id}/correlations/self').json()
if corr['max'] < 0.7:
    # 8. 提交
    sess.post(f'https://api.worldquantbrain.com/alphas/{alpha_id}/submit')
```
