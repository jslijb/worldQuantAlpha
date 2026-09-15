# WorldQuant Brain Alpha 质量提升 Playbook（文档级，含 0.7 真相 + 每日挖矿打法）

> 本方案**全部基于用户提供的 BRAIN_*.md 文档**，每条建议标注来源。不使用任何外部假设。
> 背景：当前 Rank = **719**（非 911，前次误记已更正），目标 **进前 100**；日挖 **≥10 个高质量因子**（保底 ≥3）；**不删除已提交 alpha**。

---

## 一、质量的标准到底在哪（文档定义）

**IS 六指标**（来源：`BRAIN_进阶指南_理解模拟结果与提升Alpha表现.md` §二）：Sharpe、Turnover、Fitness、Returns、Drawdown、Margin。
- Sharpe（Delay1 > 1.25，Delay0 > 2.0）、Fitness（D1 > 1.0 / D0 > 1.3 才算提交）、Turnover（1%–70%）、Drawdown（越小越好）、Margin（越高越好）。
- 公式：**Fitness = Sharpe × √( |Returns| / max(Turnover, 0.125) )**。

**提交六测试**（来源：`BRAIN_Alpha提交测试完整清单.md` §二）：Fitness / Sharpe / Turnover / Weight(<10%) / Sub-universe / **Self-Correlation(<0.7 或 Sharpe 高 10%)**。

**"高质量"的定义（本文档约定）**：S+F ≥ 4.0（A 档，你定的红线）**且** selfCorrelation < 0.7（能过 Production Correlation）。单过提交门槛只是"能进"，过 A 档 + 低相关才是"进前 100"的硬货。

---

## 二、为什么 31 个卡在 719（文档视角诊断）

1. **同质化（根因）**：`selfCorrelation` 均值 0.673，14/31 ≥ 0.7。文档明确：0.7 是 **Production Correlation 测试阈值**（`BRAIN_Alpha改进与顾问进阶指南.md` §十 + `BRAIN_Alpha提交测试完整清单.md` §3.6）。相关性过高 → 平台判定信号重复 → 稀释权重。
2. **Turnover 拖死 Fitness**：6 个 T≥0.4 把 F 压在 1.2–1.8。Fitness 公式里 T 在分母，T 高直接拉低 F。
3. **数据集只用了 2/6 类**：31 个几乎全是 Fundamental（liabcurr/cf-ev/ebit-ev）+ PV（close/returns/volume）。文档 §一/§四/§五 反复强调**换数据集类别才能降相关、增多样性**（`BRAIN_核心数据集类别详解.md` 列了 6 大类）。

---

## 三、文档给的"提升质量"四板斧（带引用）

### 板斧 1：提 Sharpe = 提 Return 或 降 Volatility
- 公式：IR = mean(PnL)/std(PnL)，**Sharpe ≈ 15.8 × IR**（即 Sharpe 就是 IR 的年化版，这就是没有独立 IR 字段的原因）。（来源：`BRAIN_Alpha改进与顾问进阶指南.md` §三）
- 两条路：① **↑Return**＝更好预测/更多数据；② **↓Volatility**＝中性化降低对高波动板块暴露。

### 板斧 2：提 Return 的 5 招（来源：同上 §四）
1. 提高 Turnover（更频繁交易，潜在收益更高）
2. 用更低 Decay（信号更快反映最新数据）
3. 在更小、流动性更好的 Universe 工作
4. 收益/回撤不变前提下适度提高波动率
5. **尝试 News / Analyst 数据集**（常出高收益 Alpha）← 你完全没用

### 板斧 3：降相关性 3 招（来源：同上 §五）—— 这是进前 100 的核心
| 方法 | 示例 |
|---|---|
| 换数据字段 | 用 open/high/low 替代 close |
| 换算子 | 功能相近但形式不同的算子替换 |
| 换分组 | industry / subindustry / sector / country |
> 注意：优先等价替换，不要为降相关扭曲原思路；真正降相关来自"跳出框架思考"。

### 板斧 4：降 Turnover（来源：`BRAIN_进阶指南` §2.2 + `BRAIN_Alpha提交测试完整清单.md` §3.3）
- 算子：`decay`、`hump`、`ts_decay_linear`、`trade_when`、`rank`。
- 事件驱动框架：`trade_when(Event, Alpha, -1)`（来源：改进指南 §六）。**但文档也警告**：trade_when 降 T 但"不容易拿高 Sharpe/Return"——所以降 T 要权衡，别为了 F 牺牲 S。

### 配套：降 PnL 波动（来源：改进指南 §七）
- NaN 跳变 → `backfill`；信号太快 → `decay`/移动平均；单股权重过大 → **Truncation < 0.1**。

### 配套：中性化按数据集（来源：改进指南 §八 表）
| 数据集 | 推荐中性化 |
|---|---|
| 基本面 | industry / subindustry |
| 分析师 | industry / subindustry |
| 价格量 | industry / subindustry |
| 新闻 | subindustry |
| 宏观 | market / sector / industry |

### 防过拟合 8 条（来源：改进指南 §九，挑重点）
- 别把权重集中在高波动股；别选"最好"参数（第二好/平均更稳）；**别为通过测试而拟合测试**；用 Test Period 分 Train/Test；**别陷入 Excellent/Superior 陷阱——IS 好不是重点，能持续才重要**。

### 好 Alpha 四特征（来源：第四课 §四）
**Robustness / Uniqueness / Value-add / Consistency**——稳定亏钱也比暴涨暴跌强，基金经理敢投稳定曲线。

---

## 四、0.7 的真相（关键，决定"不下线"是否成立）

`selfCorrelation ≥ 0.7` 不是"必须删"，而是触发 **Production Correlation 测试**（`BRAIN_Alpha改进与顾问进阶指南.md` §十）：
- **通过条件（满足其一即可）**：① 与任意顾问 Alpha 最大相关性 < 0.7；**或** ② 对每个相关 > 0.7 的 Alpha，你的 Sharpe 至少比它**高 10%**。
- 例：老 alpha X Sharpe=3.18，新 alpha Y 与 X 相关但 Sharpe ≥ 3.50（3.18×1.1），仍可提交。
- **结论**：你"不下线"完全可行。新挖的 alpha 只要做到 **selfCorr < 0.7**，或 **Sharpe 比相关的老 alpha 高 10%**，就能过 Production Correlation。不需要动那 31 个。

---

## 五、每天挖 10 个高质量因子的打法（系统性变异引擎）

文档给的方法论（来源：第四课 §四 Do's + 改进指南 §二）：
> **"复现后往前走一两步：换 dataset / group / operator 组合，就是新的 alpha。"**

即：以 13 个官方示例（`BRAIN_快速表达式_IQC提示与Alpha示例题库.md` §四）为模板母本，对每个母本做"换字段 / 换算子 / 换分组 / 换数据集"的一步变异，批量产出低相关候选。

**扩展到 6 大数据集类**（来源：核心数据集详解 §二），你当前只用 2 类：
| 类 | 可用字段示例 | 你用了吗 |
|---|---|---|
| 价量 PV | close/volume/vwap/returns/ADV20 | ✅ 大量 |
| 基本面 | ebit/ev/liabcurr/rev/assets/cf | ✅ 大量 |
| 分析师 est/etz | etz_eps_delta/etz_revenue_delta/est_netprofit | ❌ 未用 |
| 情绪 snt | snt_bullish/snt_bearish/snt_ratio/snt_buzz | ❌ 未用 |
| 新闻 news | news_volume_1h/news_abs_return_5min/news_pre_return | ❌ 未用 |
| 关系 cust/comp/part | customers/competitors/partners 传导 | ❌ 未用 |

**每日纪律**：
1. 母本池 = 13 示例 + 你 31 个里 A 档（e79kPeEM/le8ddYbe/883OXpJl/6XrbGx1L/E5vkQ76G/kqjpepz8）。
2. 每母本产 ≥1 个变异：优先换**未用数据集**（分析师/情绪/新闻/关系）→ 天然降相关。
3. 每个候选配 settings：Decay（Alpha 参数通常 ≤5 天，decay 10/20 在经济学上无意义，来源第四课 §三）、中性化按上表。
4. **启用 Test Period（Train/Test 划分）**：把 IS 分成 Train 开发 / Test 验证（来源：改进指南 §九 第8条）。已核实之前 31 个 **train/test 全为 null、0/31 启用过 Test Period**——全在整段 IS 上调参，存在过拟合风险；新因子必须在 Test 段 Sharpe 不崩才算稳。
5. 模拟前先估 selfCorr（换数据集/分组后通常 < 0.7）；模拟后筛 S+F≥4.0 且 selfCorr<0.7 的提交。
6. **豁免规则已自动化（2026-09-09）**：mine_submit.py 预检 corr≥0.7 时不再一律跳过——自动从 /correlations/self 的 records 里取 corr≥0.7 的相关 alpha 中最高 Sharpe，候选 S ≥ 1.10×该值即继续提交（records[i][5]=corr, [6]=对方Sharpe，平台直接给）。例：相关 alpha S=3.18 → 候选 S≥3.50 即可提交。
5. 日产出目标 = 模拟 15–20 个候选 → 留存 ≥10 个高质量。

---

## 六、Day-1 候选清单（10 个，跨 4 个未用数据集，待模拟）

| # | 表达式 | 数据集 | Decay | 中性化 | 来源/变异 |
|---|---|---|---|---|---|
| 1 | `group_rank(etz_eps_delta, subindustry)` | 分析师 | 5 | market | 示例4 + 换字段 |
| 2 | `rank(snt_bullish - snt_bearish)` | 情绪 | 5 | subindustry | 新数据集直接试 |
| 3 | `rank(ts_av_diff(news_volume_1h, 5))` | 新闻 | 5 | industry | 新数据集 |
| 4 | `rank(ts_rank(cust_ret, 20))` | 关系 | 5 | industry | 供应链传导 |
| 5 | `group_rank(eps/close, subindustry)` | 基本面 | 0 | market | 示例3 价值因子 |
| 6 | `close > ts_sum(close,20)/20 ? 1.6*rank(-ts_delta(close,2)) : rank(-ts_delta(close,2))` | PV | 0 | subindustry | 示例11 SMA增强 |
| 7 | `rank((ts_sum(open>close,20)/ts_sum(open<close,20)) / (ts_sum(open>close,252)/ts_sum(open<close,252)))` | PV | 130 | subindustry | 示例7 月度反转 |
| 8 | `-rank(ts_delta(close,2))*(1-rank(ts_decay_linear(volume/sum(volume,30),10)))` | PV | 6 | subindustry | 示例1 量价回归 |
| 9 | `rank(ts_delay(close,2)-ts_regression(close,vwap,60,rettype=3))` | PV | 5 | subindustry | 示例6 回归残差 |
| 10 | `rank(cashflow_op/net_income)` | 基本面 | 20 | subindustry | 财务质量因子 |

> 注：字段名以平台实际可用为准（TUTORIAL 权限数据集可能受限，模拟时若报字段不存在即换同源字段）。这 10 个刻意跨 4 个未用数据集 + 多算子/分组，目的就是规避 selfCorr≥0.7。

---

## 七、目标与红线（已记入工作日志）

- 当前 Rank **719** → 目标 **前 100**。
- 日挖 **≥10 个高质量**（S+F≥4.0 且 selfCorr<0.7），保底 ≥3。
- **不删除**已提交 31 个；新 alpha 靠"低相关 或 Sharpe 高 10%"过 Production Correlation。
- 高质量定义：A 档(S+F≥4.0) + selfCorr<0.7。
