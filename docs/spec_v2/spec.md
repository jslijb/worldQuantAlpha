# Alpha Loop v2 — 规格说明（spec.md）

> 版本：**v2.1**（2026-11-16 12:20 北京时间，用户批准 v2.0 并追加 4 条硬要求）
> 状态：**已批准，进入实现**。
> 本系统为**全新实现**，代码置于独立包 `alpha_loop/`，不引用、不复制 `src/`、`_grid/`、`_autologs/`、`mine_grid.py`、`run_pipeline.py` 的任何实现。

---

## 0. 目标

建立一条**自闭环**的 Alpha 生产线：

```
idea(机制) → 数据集 → 表达式(关系形态) → 回测 → 判定
                ↑                              │
                └──── 改表达式/改参数 ←── 失败 ┘
                              通过 → 待提交队列（跨天持久）
                                       → 每日北京 14:00 窗口 → 提交
```

核心主张（11-16 讨论结论）：

1. **idea 优先**：先确定"在赌什么"，再找能承载它的单数据集字段，最后选算子。
2. **单数据集（ATOM）是硬约束**，但**必须用关系型构造**，禁止单字段裸变换与"各自归一化后相加"。
3. **多样性是批次层面的**：数据集分散、字段分散、算子分散、形态分散、参数分散。
4. **复杂 = 字段之间成关系 + 变换层数**，不是算子个数。

---

## 1. 范围与非目标

### 1.1 范围内

- 市场优先级：`GLB > EUR > ASI > JPN > CHN(大A)`；**USA 降为最后兜底（2026-11-17 用户指令：不到最后一步不使用）**，默认轮转不进入 USA，需显式开启。
- 每市场 universe：GLB `{TOP3000, MINVOL1M}`；EUR `{TOP2500, MINVOL1M}`；ASI `{MINVOL1M}`；JPN `{TOP800}`；CHN `{TOP2000U, TOP2000}`；USA `{TOP3000, TOP1000}`。
- 仅 REGULAR Alpha（SUPER 不在本期范围）。
- 回测 + 判定 + 自愈 + 跨天待提交队列 + 提交 + 台账 + 经验库，全链路。

### 1.2 非目标

- SUPER 组合与提交。
- 赛事积分抓取。
- 自动修改程序源码（见 §12.2）。
- Web UI。
- 复用旧系统任何生成器/判定器代码。

---

## 2. 红线（违反即中止本批，不得绕过）

| # | 红线 | 校验点 |
|---|---|---|
| R1 | 单条 Regular 表达式只允许**一个业务数据集**的字段 | `AtomGate`，False 一律不 POST |
| R2 | 禁止"独立归一化后直接相加" | `DepthGate.D3` |
| R3 | 字段必须成关系（比值/乘积/差分/条件/相关/回归） | `DepthGate.D1` |
| R4 | 提交前平台预检：`prod.max ≤ 0.69` 且 `self.max ≤ 0.69` | `PreSubmitGate` |
| R5 | 未过平台硬线不得 POST；403 body 的 checks 是唯一真值 | `Submitter` |
| R6 | **只在北京时间 14:00 之后的窗口提交** | `ClockGate` |
| R7 | 台账只追加，不改历史行 | `Ledger.append()` |
| R8 | 字段→数据集映射**按 region 分桶** | `FieldDB` |
| **R9** | **`group_rank` 已解禁（2026-11-16 用户批准）；优先尝试 group_scale / group_zscore / quantile 等替代，group_rank 保留作对照** | `OperatorBan` 只拦 `config.BANNED_OPERATORS` 中的算子（当前为空） |
| **R10** | **USA 市场只允许使用历史未用过的数据集** | `DatasetGate`，USA 已用数据集一律剔除 |
| **R11** | **USA 的量价数据集（pv*）列入黑名单**（2026-11-17 用户指令；其他市场未用过、不设黑名单） | `DatasetGate.is_banned_dataset(dataset_id, region)`，USA 命中即拒 |

平台硬线（本地预筛口径）：

- 常规：`S ≥ 1.58`、`F ≥ 1.0`、`2Y Sharpe ≥ 1.58`、`TO ≤ 70%`、`SUB_UNIVERSE PASS`、`LADDER ≥ 2.02`、`SELF ≤ 0.70`、`PROD ≤ 0.70`。
- GLB 附加：`AMER / EMEA / APAC` 各 `≥ 1.0`。
- CHN 附加：`S ≥ 2.07` 且 `LOW_ROBUST_UNIVERSE_SHARPE`（0.4×S）通过。

---

## 3. 系统架构

```
alpha_loop/
├── config.py        # 常量 + 市场/参数矩阵 + 算子禁用表
├── auth.py          # 认证与请求封装
├── fielddb.py       # 字段/数据集元数据（region 分桶）
├── baseline.py      # 从平台拉历史已提交 alpha → 已用字段/数据集基线
├── idea_lib.py      # idea 定义与候选池
├── composer.py      # 表达式合成（形态 × 字段角色）
├── gates/
│   ├── atom.py      # R1
│   ├── depth.py     # R2/R3
│   ├── operators.py # R9
│   ├── dataset.py   # R10
│   └── diversity.py # 批次多样性
├── knowledge.py     # 经验库（记录/审核/晋升/冲突）
├── sim.py           # POST /simulations + 轮询
├── judge.py         # checks 解析与失败归因
├── repair.py        # 自愈决策表
├── queue.py         # 跨天待提交队列
├── submit.py        # 预检 + 提交 + 受理确认
├── ledger.py        # 台账与状态库
├── loop.py          # 主状态机
└── report.py        # 结构化进度输出
```

数据目录：

```
alpha_loop/state/
├── state.db              # sqlite 全量状态
├── ledger.csv            # 新台账（id 第0列，utf-8-sig，只追加）
├── fielddb/{region}.json # 字段缓存（带 region 键）
├── baseline.json         # 平台历史已用字段/数据集
├── pending.json          # 跨天待提交队列（持久）
└── knowledge/*.md        # 经验条目（一文件一条，带审核状态）
```

---

## 4. 数据模型

### 4.1 idea

```
idea_id / mechanism(一句话,必填) / market_scope / field_roles
dataset_hint / shape_hint / status / budget(默认12) / used
```

### 4.2 unit（表达式单元）

```
unit_id / idea_id / market / shape / params / expr / dataset_id / fields
gate_* / sim_status / alpha_id / metrics / verdict / attempt / parent_unit
```

### 4.3 pending（跨天队列）

```
alpha_id / unit_id / market / S / F / TO / prod_max / self_max
enqueued_at / day_target(目标提交日) / status(ready/submitted/rejected)
```

---

## 5. 主流程状态机

```
SELECT_IDEA → MATCH_DATASET → COMPOSE
   → OperatorBan(R9) → DepthGate → AtomGate → DatasetGate(R10) → DiversityGate
        └ 任一 FAIL → 丢弃，不烧配额
   → SIMULATE(并发≤2) → JUDGE
        ├ PASS_READY → 入 pending 队列（跨天）
        └ FAIL → REPAIR(决策表) → COMPOSE（同 idea）
                    └ budget 耗尽 → idea=abandoned
```

- 单轮最多 `BATCH_SIZE=12` 候选，全局并发 `MAX_CONCURRENT=2`。
- 每轮结束都检查时钟：若已进入 14:00 窗口且队列非空 → 先提交，再继续回测。

---

## 6. 数据集选择层

- 数据源：平台 `GET /data-fields`（region+universe），首次拉取落盘。
- **历史基线**：`baseline.py` 拉 `GET /users/self/alphas` 全量已提交 alpha（region + 表达式），解析出 `used_fields` / `used_datasets`（按 region 分桶），落 `baseline.json`。
- 匹配算法：
  1. `field_roles` 语义关键词匹配字段 `description`（同义词表在 `config.py`）。
  2. 候选字段必须**同属一个 dataset.id** 且在目标 region 有权限。
  3. 排除 `used_fields`；优先 `coverage ≥ 0.8`、`alphaCount` 低。
  4. **USA 市场：数据集必须不在 `used_datasets[USA]`**（R10 硬约束），无候选则该 idea 在 USA 直接跳过。
  5. 本系统使用次数越少优先级越高。
- 匹配不到 → 记录原因，idea 在该市场置 `no_dataset`。

---

## 7. 表达式合成层

### 7.1 横截面层（group_rank 已解禁，优先替代）

| 允许 | 状态 |
|---|---|
| `group_scale(x, G)` | 首选，11-15 四条过线件实测 |
| `group_zscore(x, G)` | 次选 |
| `group_neutralize(x, G)` | 待权限探针 |
| `rank(x)` | 全局横截面，待探针 |
| `quantile(x, driver="gaussian")` | 横截面分位，待探针 |
| `group_rank(x, G)` | **已解禁（2026-11-16）**，保留作对照 |

**禁用**：裸 `zscore(x)`/`normalize(x)`（作主形已证伪）。`group_rank` 已解禁。

### 7.2 形态模板（关系在最内层）

| 代号 | 模板 | 赌什么 |
|---|---|---|
| A | `group_scale(ts_av_diff(F(a,b),N), G)` | 比值的时序变化 |
| B | `group_zscore(ts_av_diff(a,N1) - ts_av_diff(b,N2), G)` | 两腿变化之差 |
| C | `group_scale(ts_av_diff(F(a,b),N) / ts_std_dev(F(a,b),M), G)` | 变化相对自身波动 |
| D | `group_zscore(if_else(a > b, F1(a,b), F2(a,b)), G)` | 条件分支下的相对位置 |
| E | `group_scale(ts_corr(a, b, N), G)` | 两字段一致性 |
| F | `group_zscore(ts_regression(a, b, N, lag=0, rettype=0), G)` | 剔除 b 后的残差 |
| G | `rank(F(a,b))` | 全局横截面排序（无分组） |
| H | `group_neutralize(ts_av_diff(F(a,b),N), G)` | 分组内去均值 |
| I | `quantile(F(a,b), driver="gaussian")` | 横截面分位 |

`F(a,b)` ∈ `{a/b, a*b, a-b}`。

### 7.3 约束

- 每条表达式：**业务字段 ≤ 2**，同数据集。
- 关系算子必须**最内层**；中间不得插入独立时序归一化。
- 参数网格：`N ∈ {20,45,60,120}`，`M ∈ {60,120,250}`，`G ∈ {subindustry, industry, sector, exchange, sector+country}`（按市场裁剪）。
- `group_rank` 允许使用；单批次内横截面算子分布受 V5 约束（单一算子占比 ≤60%）。

### 7.4 横截面算子权限探针

首次使用 `group_neutralize` / `rank` / `quantile` 前，各发 1 条哑模拟验权限；HTTP 400/权限错则从轮换中摘除并记 `knowledge`。探针结果落 `state/op_permissions.json`。

### 7.5 回测参数矩阵

- `neutralization ∈ {SUBINDUSTRY, INDUSTRY, MARKET, STATISTICAL}`（STATISTICAL 仅 GLB/USA/EUR 先试）
- `decay ∈ {0, 6, 12, 20, 32, 64}`；`truncation = 0.08`；`pasteurization = ON`；`delay = 1`
- 参数分配：同 idea 不同形态配不同参数；**禁止同表达式只换分组参数当新件**。

---

## 8. 门

### 8.1 OperatorBan（R9）
表达式含 `config.BANNED_OPERATORS` 中的算子 → FAIL。当前禁用表为空（group_rank 已 2026-11-16 解禁）。

### 8.2 AtomGate（R1）
业务字段（排除算子名/数字/命名参数/分组字段）→ region 分桶查 dataset。≤1 PASS；>1 同数据集 PASS；跨数据集/查不到 FAIL。

### 8.3 DepthGate（R2/R3）
D1 含关系算子或两字段直接相减；D2 变换层数 ≥2；D3 不得两分支各自归一化后相加。

### 8.4 DatasetGate（R10）
USA：`dataset_id ∈ used_datasets[USA]` → FAIL。其他市场：仅做"使用次数降权"，不硬拒。

### 8.5 DiversityGate（批次）
V1 每条字段数 ≤2；V2 每批 ≥2 个历史未用字段；V3 数据集分布熵 ≥阈值；V4 同 idea 批次占比 ≤30%；**V5 横截面算子不得单一占比 >60%**（防止换汤不换药）。

---

## 9. 回测执行层

- `POST /simulations` → `Location` → 轮询（5s，上限 1800s）。
- 429 退避 20~30s；5xx 重试 3 次；400 记 FATAL 不重试。
- 原始响应落 `state/raw/{unit_id}.json`。

---

## 10. 判定与自愈决策表

| 失败项 | 自动动作 | 上限 |
|---|---|---|
| `LOW_SHARPE` | 换形态（A→B→E→F→C→H）+ 换窗口 | 4 |
| `LOW_FITNESS` | decay +6 档 | 3 |
| `HIGH_TURNOVER` | decay +12 档；仍高换形态 C | 3 |
| `LOW_TURNOVER` | decay -6 档；仍低换短窗口 | 2 |
| `CONCENTRATED_WEIGHT` | 换关系算子（`/`→`-`→`if_else`） | 3 |
| `LOW_SUB_UNIVERSE_SHARPE` | 换 universe | 2 |
| `LOW_2Y_SHARPE` | 换窗口/形态 | 3 |
| GLB 分区 S <1.0 | 换 G（industry→sector→exchange） | 3 |
| `LOW_ROBUST_UNIVERSE_SHARPE`(CHN) | 弃 idea | — |
| `SELF_CORRELATION >0.70` | 换 G → 换窗口 → 换 idea | 3 |
| `PROD_CORRELATION >0.70` | decay +6 后复检；仍高弃 | 3 |
| 连续 LOW_SHARPE 且 ΔS<0.05 | 判 idea 无货，abandoned | — |

预算：每 idea `12` 次；每市场每日 `SIM_DAILY=80`。

---

## 11. 提交与跨天队列

```
PASS_READY → queue.enqueue（持久化到 pending.json，day_target=下一个可用提交日）
每日 14:00 窗口开启 → queue.drain：
   PreSubmitGate（prod.max≤0.69 且 self.max≤0.69；0.68~0.699 → 打回 decay+6 重跑）
   → POST submit → 轮询 → 403 记 checks / 200+RA=0 受理
   → GET /alphas/{id} status=ACTIVE + dateSubmitted → 确认
   → Ledger.append + queue 标 submitted
```

- **队列跨天不失效**：当天跑出的达标件只要没提交，明天窗口自动继续。
- 配额：每美东日 4 REGULAR。提交前核对当日计数。
- 窗口外：只回测、只入队，不提交。

---

## 12. 监控、自愈与人工边界

### 12.1 程序内自动（允许）
表达式形态/窗口/分组/decay/中性化/universe 调整；失败重试；断点续跑；每轮结构化进度。

### 12.2 程序外人工（必须会话内做）
程序缺陷、门逻辑错误、接口变更 → 我改源码 → 跑回归 → 立即重跑，并说明改了什么。**程序不得自改源码。**

---

## 13. 经验库（新增，用户第 3 条）

### 13.1 数据形态
一文件一条，`state/knowledge/{ktype}_{slug}.md`：

```yaml
id / ktype(idea_pattern|expr_pattern|failure_mode|param_effect|op_permission)
statement: 一句话结论
evidence_level: L1实测输出 | L2平台返回 | L3论文原文 | L4推断
samples: n
controls: 构造深度/形态/参数/市场
first_seen / last_verified / verify_count
status: candidate | verified | promoted | deprecated | conflicted
supersedes / conflicts_with
```

### 13.2 审核规则（防错误经验入库）
1. **无 L1/L2 证据 → 最高只能 candidate**，不得进生成规则。
2. 进 `verified` 需 `verify_count ≥ 2` 且两次样本独立（不同 idea 或不同市场）。
3. 进 `promoted`（影响生成）需 `samples ≥ 10` 且无冲突条目。
4. 出现反例 → 自动置 `conflicted`，并冻结其下游规则。
5. **任何结论必须写清构造深度 + 形态 + 样本量**；缺一项只能记为"本次构造失败"。
6. 旧归档文件不作为判据来源。

### 13.3 自动喂料
每次模拟结束自动更新统计：形态命中率、失败码分布、idea 类型产出率、参数效果。达阈值才生成 candidate 条目。

---

## 14. 测试要求

| 层级 | 内容 | 通过标准 |
|---|---|---|
| 单元 | 5 个门各 ≥10 用例；决策表 12 分支；ClockGate 13:59/14:00；知识库审核 6 规则 | 全绿 |
| 冒烟 | 认证 → 1 条模拟 | 201/OK |
| 回归 | 10 条固定表达式门判定稳定 | 与基线一致 |
| E2E | 队列跨天（模拟"次日窗口"）→ 提交 dry-run | 队列状态正确流转 |
| 合理性 | 无散落硬编码；异常不静默吞 | 静态检查通过 |

---

## 15. 验收标准

1. 14:00 前 ≥40 条模拟，≥4 条进队列。
2. 横截面算子分布满足 V5（单一算子 ≤60%）；`group_rank` 与替代算子均可使用。
3. USA 所有候选的数据集均不在历史已用集合内。
4. 14:00 后提交 ≥1 条受理 ACTIVE（配额允许）。
5. 知识库有 ≥1 条 `verified` 条目，且每条都带构造深度/形态/样本量。
6. 全链路可追溯。

---

## 16. 待确认（默认执行）

1. 平台历史 alpha 列表接口是否返回表达式 → 不能则逐条拉详情（只读，不影响生产）。
2. 今日美东配额占用 → 运行时核对。
3. CHN 字段缓存为空 → 首次运行拉取。
---

## 17. R12 skill 化与自动维护（2026-11-18 新增）

### 需求
把当日的 Alpha 生产流程沉淀为**可被任何 agent 加载的 skill**，并支持**自动更新**：
后续每发现新判据或被推翻的旧判据，不需要人工重写 skill 正文，由脚本从既有事实源提炼并留痕。

### 事实源（唯一允许的数据来源，禁止脚本凭空生成结论）
1. `data/alpha_quality_analysis/IDEA_LOOP_LEDGER.csv`（每轮判决）
2. `alpha_loop/state/verdicts/*.json`（平台 403 判决书真值）
3. `alpha_loop/state/knowledge/index.json`（人工审核过的经验条目）

### 交付物
- `.codeartsdoer/skills/alpha-production-loop/SKILL.md`（通用方法论，不绑定仓库路径）
- `.../references/platform-constraints.md`（平台硬约束：接口参数、SUPER body、相关性行为）
- `.../references/repo-workflow.md`（本仓库可执行流程与路径）
- `.../references/evidence/criteria_snapshot.md`（**脚本生成**，含生成时间、数据窗口、每条判据的样本量 n）
- `.../CHANGELOG.md`（脚本在有变化时追加；人工追加须写证据出处）
- `.../scripts/sync_evidence.py`（自动提炼脚本）

### 自动更新机制（必须可复验）
1. `sync_evidence.py` 每次运行重新统计事实源，生成快照。
2. **幂等**：快照内容无变化时不写文件、不追加 CHANGELOG。
3. **有变化**时：重写快照 + CHANGELOG 追加一行（时间 / 变更摘要 / 依据文件名）。
4. 脚本**只能**输出可由事实源直接算出的统计量；任何"机制成立/不成立"的判断不得由脚本生成。
5. 机制类判据只允许转载 `knowledge` 中 `status=verified` 的条目，并保留其 `source`。

### 验收
1. `pytest tools/tests -q` 全绿（统计逻辑 ≥6 用例，含幂等用例）。
2. 连续跑两次 `sync_evidence.py`，第二次不产生文件变更。
3. 快照中出现的每个数字都带 `n=` 样本量。
4. SKILL.md 不包含任何绝对路径（可迁移到其他项目/agent）。