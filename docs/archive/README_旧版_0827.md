# WorldQuant Brain Alpha 挖掘项目

> 自动化挖掘并提交 WorldQuant Brain 平台的优质 Alpha 因子

## 项目目标

通过 WorldQuant Brain API 自动化：
1. 获取基本面/价格数据字段
2. 批量生成候选 Alpha 表达式
3. 并发回测模拟
4. 筛选通过 IS 标准的 Alpha（Sharpe≥1.25, Fitness≥1.0, Turnover 1%~70%, Checks 全 PASS）
5. 预检查自相关性（max_corr < 0.7）
6. 自动提交

## 目录结构

```
worldquant/
├── utils.py                       # 公共工具（登录、获取数据字段）
├── AlphaSimulator.py              # 生产级并发模拟管理器
├── alpha_hunter.py                # 多策略批量挖掘（A~G 七大策略）
├── find_and_submit_alphas.py      # 自动发现并提交（含预检查）
├── world4.py                      # 跨截面比率型批量生成 + CSV 导出
├── alpha_list_pending_simulated.csv  # 待模拟 Alpha 队列
├── brain_credentials.txt          # 登录凭据（不提交到 git）
├── WQ_BRAIN_API.md                # API 使用文档（核心参考）
└── docs/                          # 项目文档
    ├── README.md                  # 本文件
    ├── spec.md                    # 规格说明（SDD - WHAT）
    ├── design.md                  # 设计文档（SDD - HOW）
    ├── tasks.md                   # 任务清单（SDD - 执行）
    ├── pitfalls.md                # 踩坑记录
    └── methodology.md             # Alpha 因子挖掘方法论（核心经验）
```

## 快速开始

```powershell
# 1. 激活环境
conda activate bigmodel

# 2. 批量挖掘（多策略，自动提交通过的）
python alpha_hunter.py

# 3. 或：生成候选到 CSV，由 AlphaSimulator 并发处理
python world4.py
python AlphaSimulator.py
```

## IS 通过标准

| 指标 | 要求 |
|------|------|
| Sharpe | ≥ 1.25 |
| Fitness | ≥ 1.0 |
| Turnover | 1% ~ 70% |
| Checks | 全部 PASS（SELF_CORRELATION 在 TUTORIAL 下为 PENDING，不阻止提交） |
| 自相关性 | max_corr < 0.7 |

## Fitness 公式

```
Fitness = Sharpe × √(|Returns|) / max(Turnover, 0.125)
```

## 已提交 Alpha 记录

| Alpha ID | 表达式 | Sharpe | Fitness | 提交日期 | 备注 |
|----------|--------|--------|---------|----------|------|
| 58p2XdxX | liabilities/assets | 1.55 | 1.34 | 早期 | 总杠杆比率（账面） |
| wpjoxbbd | group_neutralize(ts_rank(cashflow_op/enterprise_value, 60), industry) | 1.37 | 1.00 | 早期 | cf/ev 时序排名, dec=4 |
| rKj7w0Z1 | group_rank(ts_rank(cashflow_op/enterprise_value, 60), industry) | 1.60 | 1.24 | 2026-08-28 | cf/ev 时序排名, dec=6 |
| RR79x16n | liabilities_curr/assets | 1.47 | 1.16 | 2026-08-28 | 流动负债/账面资产 |
| 9qX8Nr6r | liabilities_curr/cap | 1.26 | 1.49 | 2026-08-28 | 流动负债/市值（换分母策略） |
| **vRjG1Jzw** | **group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry)** | **1.79** | **1.27** | **2026-08-30** | **cf/ev 偏离度（ts_av_diff 新操作符）** |
| **QP7z069Q** | **signed_power(liabilities_curr/assets, 0.5)** | **1.64** | **1.38** | **2026-08-30** | **signed_power 压缩变换** |
| **1YwKML56** | **group_rank(ts_av_diff(cashflow_op/enterprise_value, 60), industry) delay=0** | **2.21** | **1.75** | **2026-08-30** | **delay=0 版本，信号最强** |

> 失败记录：blja39jM(debt/assets) 自相关 0.8365；debt_lt/assets、ebitda/cap、ts_zscore、group_zscore、subindustry 分组、ebit/cap 等均因与已提交 Alpha 相关性 ≥ 0.7 被拒。

## 有效方法论（8 个 ACTIVE Alpha 总结）

1. **负债比率**：liabilities/assets, liabilities_curr/assets, liabilities_curr/cap
2. **cf/ev 时序排名**：group_rank/group_neutralize + ts_rank(cf/ev, 60) + decay 调优
3. **cf/ev 偏离度**：group_rank + ts_av_diff(cf/ev, 60)（delay=0 或 1，信号更强）
4. **signed_power 压缩**：signed_power(liabcurr/assets, 0.5) 压缩极端值

## 开发规范

- 使用 `conda activate bigmodel` 环境
- 遵循 SDD + TDD 思想
- 详见 `docs/spec.md`, `docs/design.md`, `docs/tasks.md`
- 踩坑记录见 `docs/pitfalls.md`