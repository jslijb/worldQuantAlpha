# Alpha Loop v2 — 任务清单（task.md）

> 版本 v2.1（对应 spec v2.1，**已批准**）
> 代码写入新包 `alpha_loop/`，不修改既有任何文件。每任务完成即自测。

---

## 阶段 0：基础设施

### T0.1 目录与配置骨架
- `alpha_loop/`、`gates/`、`tests/`、`state/`
- `config.py`：全部常量 + `BANNED_OPERATORS={}`（group_rank 已解禁）+ `USA_UNUSED_DATASET_ONLY=True`
- **验收**：`python -m alpha_loop.config` 打印关键常量，禁用表为空

### T0.2 auth.py
- login/get/post/poll；429 退避、5xx 重试、400 直返
- **验收**：`python -m alpha_loop.auth` → `LOGIN_OK`（不打印凭据）

### T0.3 单测 auth（mock）
- **验收**：`pytest alpha_loop/tests/test_auth.py -q`

---

## 阶段 1：数据层

### T1.1 fielddb.py 拉取与缓存
- region+universe 拉 `/data-fields`，分页拉全，带 region 键落盘
- **验收**：GLB 字段 >5000；`dataset_of` 不跨 region 回退

### T1.2 baseline.py 历史基线
- 拉 `/users/self/alphas` 全量 → region + 表达式 → 已用字段/数据集
- 缓存 24h；失败降级为空集但**告警**（不得静默当"全未用"）
- **验收**：USA 已用数据集数 >0；重复运行命中缓存

### T1.3 角色匹配
- 语义关键词 → 同数据集字段组；排除已用；USA 排除已用数据集
- **验收**：给定 5 条 role，返回同 dataset 组合；USA 候选不含已用数据集

### T1.4 单测 fielddb + baseline
- **验收**：`pytest alpha_loop/tests/test_fielddb.py alpha_loop/tests/test_baseline.py -q`

---

## 阶段 2：idea、合成、门、知识库

### T2.1 idea_lib（≥20 条）
- 每条含 mechanism 一句话 + field_roles + shape_hint + market_scope
- 类型覆盖：分析师修正 / 基本面比率 / 期权结构 / 事件情绪 / 量价结构（≤30%）
- **验收**：`python -m alpha_loop.idea_lib` 打印 ≥20 条，mechanism 无空

### T2.2 composer（9 形态，形态表不含 group_rank）
- A~I 模板；参数网格；同表达式去重
- **验收**：同 idea 产出 ≥9 个不同形态表达式；形态生成器不主动产出 group_rank

### T2.3 gates/operators（R9，已解禁）
- 大小写、空格、嵌套写法全拒
- **验收**：6 种变体全 FAIL

### T2.4 gates/depth + atom
- D1/D2/D3；业务字段提取与分桶归属
- **验收**：9 形态 PASS；`group_zscore(a)+group_zscore(b)` FAIL；跨数据集 FAIL

### T2.5 gates/dataset（R10 + R11 量价黑名单）
- USA 已用数据集拒；其他市场不拒
- **验收**：单测正反例

### T2.6 gates/diversity（V1~V5）
- 含 V5 横截面算子单一占比 ≤60%
- **验收**：每门正反例

### T2.7 knowledge.py 经验库
- 文件式条目 + index.json；6 条审核规则；自动喂料
- **验收**：缺 controls 拒写；L4 证据不得 verified；冲突自动冻结

### T2.8 单测：composer + 5 门 + knowledge
- **验收**：`pytest alpha_loop/tests/test_composer.py alpha_loop/tests/test_gates_*.py alpha_loop/tests/test_knowledge.py -q`

---

## 阶段 3：模拟与判定

### T3.1 sim.py
- POST/轮询/落原始响应
- **验收**：`--live` 跑 1 条拿 alpha_id

### T3.2 judge.py
- 只认 result==FAIL；GLB 分区 / CHN robust；指标缺失不判 PASS
- **验收**：5 份 fixture 解析与人工核对一致

### T3.3 repair.py
- 12 分支 + 升档 + budget
- **验收**：`pytest alpha_loop/tests/test_repair.py -q`

---

## 阶段 4：队列、提交、台账

### T4.1 clock gate
- **验收**：13:59:59 不提交 / 14:00:00 提交

### T4.2 queue.py 跨天队列
- 持久化、原子写、跨天不失效、幂等 drain
- **验收**：模拟"次日窗口"能提交前一日入队件

### T4.3 precheck + submit + confirm
- prod/self ≤0.69；0.68~0.699 打回 decay+6；403 落 checks
- **验收**：dry-run 走通；真实模式窗口内可用

### T4.4 ledger.py
- 新台账只追加
- **验收**：追加 1 行，旧行不变

---

## 阶段 5：主循环

### T5.1 loop.py
- 市场轮转（GLB 优先，USA 默认不进入、仅兜底）、五门、模拟、判定、自愈、窗口优先提交
- 并发 ≤2、断点续跑
- **验收**：跑 3 轮无重复 unit，状态流转完整

### T5.2 report.py
- 单行进度：轮次/市场/idea/模拟/通过/队列/提交/配额/动作

### T5.3 监控
- 连续 5 轮无新 unit → 告警；异常落 crash.log 并非 0 退出
- **验收**：注入异常能定位行号

---

## 阶段 6：测试与交付

### T6.1 全套测试
- **验收**：`pytest alpha_loop/tests -q` 全绿

### T6.2 测试报告
- `alpha_loop/tests/reports/`：pytest 输出 + 覆盖摘要 + 模拟清单

### T6.3 运行手册
- `docs/spec_v2/运行手册.md`

---

## 阶段 7：实跑

### T7.1 冒烟（12:40 前）
- 真实 1 条模拟

### T7.2 冲刺回测（至 14:00）
- 目标 ≥40 条；≥4 条入队
- 横截面算子分布满足 V5；USA 全用未用数据集
- 源码缺陷 → 会话内改 → 回归 → 重跑

### T7.3 14:00 窗口提交
- 预检 → 提交 → 确认 ACTIVE → 台账
- 汇报：id + S/F/TO + 台账总数 + 美东当日计数 + 剩余配额

### T7.4 次日任务预置
- 今日未提交的达标件保留在队列，`day_target` 指向次日窗口
- 汇报队列余量与预计明日提交条数

---

## 完成定义

- [ ] `pytest alpha_loop/tests -q` 全绿
- [ ] 横截面算子分布满足 V5（单一 ≤60%）
- [ ] USA 候选 100% 未用数据集
- [ ] ≥1 条受理 ACTIVE
- [ ] 队列跨天保留可验证
- [ ] 知识库 ≥1 条 verified 且字段完整
- [ ] 运行手册可用
---

## T8. R12 skill 落地与自动维护

### T8.1 skill 骨架
- 建 `.codeartsdoer/skills/alpha-production-loop/`（SKILL.md / CHANGELOG.md / references / scripts）
- SKILL.md 只写跨项目结论；仓库路径全部下沉到 `references/repo-workflow.md`

### T8.2 快照脚本
- `scripts/sync_evidence.py`：读台账 + verdicts + knowledge，生成 `references/evidence/criteria_snapshot.md`
- 幂等：正文 hash 相同则不写盘
- 全部统计量带 `n=`

### T8.3 测试
- `tools/tests/test_sync_evidence.py`：空台账 / 单轮 / 多轮统计 / FAIL 频次 / 幂等 / 样本量标注

### T8.4 运行与自检
- 连跑两次，第二次无新增变更
- CHANGELOG 仅在内容变化时 +1 行