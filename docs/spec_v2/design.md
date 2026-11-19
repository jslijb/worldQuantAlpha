# Alpha Loop v2 — 设计说明（design.md）

> 版本：v2.1（对应 spec v2.1，2026-11-16）
> 本文件描述**怎么做**；不含实现代码。spec 变更后本文件同步变更。

---

## 1. 分层与依赖

```
loop.py（编排）
  ├─ baseline / fielddb ─┐
  ├─ idea_lib ───────────┼→ composer → gates(op/depth/atom/dataset/diversity)
  ├─ knowledge ──────────┤              → sim → judge → repair
  ├─ queue ──────────────┤                              ↓
  └─ ledger ←──────────── submit ←──────────────────────┘
```

- 单向依赖；`auth.py` 是唯一出网点；`config.py` 是唯一常量源。

---

## 2. 模块契约

### 2.1 auth.py
```python
class Brain:
    def login(self) -> bool
    def get(self, path, **kw) -> Response
    def post(self, path, json=None, **kw) -> Response
    def poll(self, location, timeout=1800, interval=5) -> dict
```
429→sleep(20~30) 最多 5 次；5xx→指数退避 3 次；400→原样返回不重试。HTTP 日志不含凭据。

### 2.2 baseline.py（R10 数据来源）
```python
def fetch_baseline(brain, regions) -> dict
# {"USA": {"fields": [...], "datasets": [...]}, "GLB": {...}}
```
- 先试 `GET /users/self/alphas?limit=100&offset=` 列表；若不含表达式则逐条 `GET /alphas/{id}`。
- 解析 region + 表达式 → 字段 → dataset（用 FieldDB 分桶映射）。
- 落 `state/baseline.json`；启动时若无缓存则重建，有则按 `fetched_at` 超 24h 刷新。

### 2.3 fielddb.py
```python
class FieldDB:
    def load(self, region, universe)
    def dataset_of(self, field_id) -> str | None     # 分桶，不跨市场回退
    def match_roles(self, region, roles, used_fields, used_datasets, forbid_datasets) -> MatchResult | None
```
打分：`coverage`（高） + `alphaCount`（低） + 本系统使用次数（低）；`forbid_datasets` 命中直接排除（USA 用）。

### 2.4 idea_lib.py
```python
IDEAS: list[Idea]
def candidates(market, used_fields, used_datasets) -> list[Idea]
def budget_left(idea_id) -> int
```

### 2.5 composer.py
```python
def compose(idea, match, shape, params) -> str
def param_grid(region, universe, shape) -> list[dict]
def xop_of(expr) -> str      # 提取横截面算子名，供 V5 统计
```
- 9 形态（A~I）见 spec §7.2；形态表不产出 group_rank，但手工构造可直接使用 group_rank。
- 生成后立即调 `gates.operators.check()` 复核。

### 2.6 gates/
```python
def operators_check(expr, ban_list) -> (bool, dict)   # R9
def atom_pass(expr, region, fdb) -> (bool, dict)      # R1
def depth_pass(expr) -> (bool, dict)                  # R2/R3
def dataset_pass(dataset_id, region, baseline) -> (bool, dict)  # R10
def diversity_pass(batch, history) -> (bool, dict)    # V1~V5
```
全部纯函数，无网络。

### 2.7 knowledge.py（经验库）
```python
def record(ktype, statement, evidence_level, samples, controls, source) -> str
def verify(kid, evidence, samples) -> str            # verify_count++，达 2 升 verified
def promote(kid) -> str                              # 需 samples>=10 且无冲突
def conflict(kid, counter_evidence) -> str
def query(ktype=None, status=None, region=None) -> list[dict]
def stats() -> dict                                  # 形态命中率/失败码分布/idea 产出率
```
- 文件式存储，YAML front-matter + 正文；索引 `state/knowledge/index.json`。
- **写入前强制校验**：`evidence_level ∈ L1/L2` 才允许 `verified`；缺 `controls` 字段直接拒写。
- 自动喂料：`judge` 每出一条结果调用 `stats.update()`，达阈值才 `record(candidate)`。

### 2.8 sim.py
```python
def run(unit, brain) -> SimResult
```
payload `{type: REGULAR, settings, regular}`；轮询 Location；原始响应落 `raw/`。

### 2.9 judge.py
```python
def verdict(alpha_json, region) -> Verdict
```
只认 `result == FAIL`；GLB 分区、CHN robust 单解析；指标缺失记 `METRIC_MISSING` 不判 PASS。

### 2.10 repair.py
```python
def next_action(unit, verdict, idea) -> Action   # RESHAPE/RETUNE/REUNIVERSE/REGROUP/ABANDON
```
严格映射 spec §10；同 fail_code 连续 2 次 ΔS<0.05 升档，3 次 ABANDON。

### 2.11 queue.py（跨天队列）
```python
def enqueue(unit, metrics, day_target) -> str
def peek(day_target=None) -> list[dict]
def drain(submitter) -> list[dict]      # 窗口内逐条提交
def mark(alpha_id, status, reason)
```
- 持久化 `pending.json`（原子写：临时文件 + os.replace）。
- `day_target` = 下一个可提交日；过期未提交不丢弃。

### 2.12 submit.py
```python
def clock_gate(now_bj) -> bool
def precheck(alpha_id, brain) -> (bool, dict)
def submit(alpha_id, brain) -> SubmitResult
def confirm(alpha_id, brain) -> bool
```
预检取 `/correlations/prod`、`/correlations/self` 的 `max`；空 body 轮询 2 轮。

### 2.13 ledger.py / report.py
台账 `utf-8-sig`，id 第 0 列，只追加；`daily_count(east_date)`；进度单行输出。

---

## 3. 状态库 schema

```sql
ideas(idea_id PK, mechanism, market, status, budget, used, created_at)
units(unit_id PK, idea_id, market, shape, xop, params_json, expr, dataset_id,
      fields_json, gate_json, sim_status, alpha_id, metrics_json, verdict,
      attempt, parent_unit, created_at, updated_at)
attempts(id PK, unit_id, fail_codes, action, delta_s, created_at)
pending(alpha_id PK, unit_id, market, S, F, TO, day_target, status, updated_at)
used_fields(field_id, dataset_id, region, first_unit, used_at, PK(field_id,region))
submits(alpha_id PK, unit_id, submitted_at, result, checks_json, confirmed)
```

---

## 4. 一轮时序

1. login → 读 baseline / 队列 / 当日计数
2. **窗口内且队列非空 → 先 drain 提交**
3. 按优先级取市场（GLB→EUR→ASI→JPN→CHN→USA，按欠额轮转）
4. idea → dataset → compose → 五门 → 模拟（并发≤2）
5. judge → PASS 入队 / FAIL 走 repair
6. 落盘 + 进度输出 + 知识库喂料
7. sleep 20s → 回到 2

退出：`SIM_DAILY` 用尽 / 手动停 / 连续 5 轮无新 unit（告警 idea 耗尽）。

---

## 5. 配置项

| 键 | 默认 |
|---|---|
| `MARKET_PRIORITY` | `[GLB,EUR,ASI,JPN,CHN]`（USA 移出默认轮转） |
| `USA_FALLBACK_ONLY` | `True`（USA 仅兜底，需显式开启） |
| `UNIVERSES` | 见 spec §1.1 |
| `NEUTRALIZATIONS` | `[SUBINDUSTRY,INDUSTRY,MARKET,STATISTICAL]` |
| `DECAYS` | `[0,6,12,20,32,64]` |
| `TRUNCATION` | `0.08` |
| `MAX_FIELDS_PER_ALPHA` | `2` |
| `MIN_NEW_FIELDS_PER_BATCH` | `2` |
| `MAX_CONCURRENT` | `1`（2026-11-17 用户指令：并发固定 1） |
| `SIM_TIMEOUT` | `1800` |
| `ROUND_INTERVAL` | `20` |
| `SUBMIT_HOUR_BJ` | `14` |
| `DAILY_REGULAR_QUOTA` | `4` |
| `IDEA_BUDGET` | `12` |
| `PRECHECK_MAX` | `0.69` |
| `PRECHECK_HARD_BAND` | `0.68` |
| `SIM_DAILY` | `80` |
| `BANNED_OPERATORS` | `{}`（group_rank 已于 2026-11-16 解禁） |
| `USA_UNUSED_DATASET_ONLY` | `True` |
| `BANNED_DATASET_PATTERNS` | `['^pv[0-9]*$', '^pricevolume', '^pv_']`（**仅 USA 生效**；其他市场不设黑名单） |
| `XOP_MAX_SHARE` | `0.60` |

---

## 6. 错误处理矩阵

| 场景 | 处理 |
|---|---|
| 认证 401 | 重登 1 次，仍失败 exit 2 |
| 模拟 400 | FATAL + 响应体，不重试 |
| 模拟 429 | 退避 25s，最多 5 次 |
| 轮询超时 | 标 TIMEOUT，交 repair |
| checks 空 body | PENDING 轮询 2 轮，仍空记 CHECK_UNAVAILABLE |
| 提交 403 | 记 checks，转 repair |
| 200 但 RA>0 | 视为部分受理，轮询确认 |
| 状态库写失败 | 全批中止（宁可停不可丢账） |
| 知识库校验失败 | 拒写入 + 告警，不影响生产 |

---

## 7. 测试设计

| 文件 | 要点 |
|---|---|
| `test_auth.py` | 重试/退避/超时（mock） |
| `test_fielddb.py` | region 分桶、跨市场不回退、角色匹配 |
| `test_baseline.py` | 列表/详情两条路径解析、缓存刷新 |
| `test_gates_operators.py` | group_rank 解禁后可过；临时加入禁用表后能拦 |
| `test_gates_atom.py` | 单数据集/跨数据集/未知/分组豁免 |
| `test_gates_depth.py` | 9 形态 PASS；裸单字段 FAIL；独立归一化相加 FAIL |
| `test_gates_dataset.py` | USA 已用数据集拒；其他市场不拒 |
| `test_diversity.py` | V1~V5 每门正反例 |
| `test_composer.py` | 9 形态可生成、形态本身不含 group_rank、去重 |
| `test_repair.py` | 12 分支 + 升档 + budget |
| `test_queue.py` | 跨天保留、幂等 drain、原子写 |
| `test_knowledge.py` | 6 条审核规则、冲突冻结、拒写缺 controls |
| `test_clock.py` | 13:59:59 不提交 / 14:00:00 提交 |
| `test_smoke_live.py` | 真实认证 + 1 条模拟（--live） |
| `test_regression.py` | 10 条固定表达式门判定稳定 |
| `test_e2e_day.py` | 跨天队列 + 提交 dry-run |

---

## 8. 与旧系统隔离

| 项 | 处理 |
|---|---|
| 旧代码 | 不 import / 不复制 |
| 旧台账 | 不作为基线来源（改用平台 API），避免继承旧解析错误 |
| 旧字段缓存 | 弃用（无 region 键） |
| 旧进程 | 不动；新系统独占 2 并发 |

---

## 9. 风险

| 风险 | 对策 |
|---|---|
| group_rank 解禁后，池内 95.8% 已用该算子，相关性可能上升 | 单批次 V5 限流（单一算子 ≤60%）；S/F 不足时先改表达式而非只换算子 |
| USA 无未用数据集可选 | 该市场自动降频，配额让给 GLB |
| 队列跨天堆积 | 每日 drain 后按 S 降序，超 20 条淘汰底部并记知识库 |
| 经验库被错误经验污染 | 只允许 L1/L2 + 双样本进 verified；冲突即冻结 |
---

## 10. R12：skill 与自动维护架构

```
.codeartsdoer/skills/alpha-production-loop/
├── SKILL.md                     ← agent 入口：何时用、流程、判据速查
├── CHANGELOG.md                 ← 变更留痕（脚本/人工）
├── references/
│   ├── platform-constraints.md  ← 平台硬约束（人工维护）
│   ├── repo-workflow.md         ← 本仓库流程（人工维护）
│   └── evidence/criteria_snapshot.md  ← 脚本生成，勿手改
└── scripts/sync_evidence.py     ← 只读事实源 → 生成快照
```

**分层原则**：`SKILL.md` 只放跨项目成立的方法论与判据；仓库路径/命令下沉到 `repo-workflow.md`，
使 skill 可被其他 agent 直接复用而不产生路径依赖。

**写权限划分**：

| 文件 | 谁写 | 约束 |
|---|---|---|
| SKILL.md | 人工/AI | 每次改动须在 CHANGELOG 记一行 |
| criteria_snapshot.md | 仅脚本 | 顶部标注"自动生成，勿手改" |
| CHANGELOG.md | 脚本 + 人工 | 每行必须带依据 |

**幂等实现**：快照正文与上次比对（剔除时间戳行后 hash），相同即跳过写盘与 CHANGELOG。