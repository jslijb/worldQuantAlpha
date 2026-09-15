# WorldQuant BRAIN：Fast Expression 官方操作符完整清单

> 来源：BRAIN 官方 Operators 参考页（`docs/operators.pdf`，7 页截图，PDF 无文本层，已用 OCR 识别并逐条核对）
> 整理时间：2026-09-06
> 定位：**官方操作符全集速查卡**（考试/写 Alpha 时查签名和参数用）
> 与《BRAIN_快速表达式_IQC提示与Alpha示例题库.md》的分工：那份文档 = Fast Expression 基础语法（注释/分号）+ IQC 技巧 + 13 个完整示例 + 高频算子精选；本份文档 = **官方七大类全部算子的完整签名 + 官方描述 + 大白话 + 考试速记**。两者互补，复习顺序建议：先读那份，再拿本份当字典查。

---

## 一、先说结论：Fast Expression 不是编程语言

用户原话确认：**Fast Expression 没有"语法"**，它不像传统编程语言那样有变量声明、循环、函数定义、控制流。它只有三样东西：

| 元素 | 是什么 | 示例 |
|---|---|---|
| **数据字段（field）** | 有名字的数据集合 | `open`、`close`、`volume`、`vwap` |
| **算子（operator）** | 对数据做数学/统计变换的函数 | `rank`、`ts_delta`、`group_rank` |
| **数值（number）** | 常量 | `2`、`30`、`0.1`、`20` |

**表达式的本质 = 用括号把算子和数据字段组合起来**，仅此而已。所谓"语法"只剩两条：

- **多行注释**用 `/* */` 包裹（不是 `#` 也不是 `//`）。
- **每行结尾加分号 `;`，最后一行不加**。

其余的"语法感"（比如 `volume > adv20 ? A : B` 这种三元写法、`a = ...;` 这种赋值）都来自算子本身（`if_else`、`trade_when`），而不是语言层面的语法。

所以考试复习的重点不是"语法"，而是**背熟算子清单**：每个算子叫什么、参数是什么、返回什么。这就是官方 operators.pdf 的全部价值。

---

## 二、官方算子七大类别总览

官方把所有算子分成 **7 大类**，共 **60 个**（本 PDF 收录）：

| 类别 | 数量 | 作用 | 考试频率 |
|---|---|---|---|
| Arithmetic（算术） | 14 | 数值四则运算、幂、对数、符号 | 中（常被当作常识考） |
| Logical（逻辑） | 10 | 与/或/非、比较、条件判断 | 中（`? :` 与 `if_else` 高频） |
| Time Series（时间序列） | 23 | 对单只股票过去 d 天做统计 | **最高**（ts_* 全家族） |
| Cross Sectional（横截面） | 5 | 当天所有股票横向比较 | **最高**（rank/zscore） |
| Vector（向量） | 2 | 向量字段降维成矩阵 | 低（考概念） |
| Transformational（变换） | 2 | 自定义分组、条件交易 | 中（trade_when 高频） |
| Group（分组） | 5 | 组内做排名/中性化等 | 高（group_* 家族） |

---

## 三、Arithmetic 算术算子（14 个）

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `abs(x)` | 返回 x 的绝对值，去掉负号 | 取绝对值 | 简单，不常考 |
| `add(x, y, filter=false)` 或 `x + y` | 逐元素相加；`filter=true` 时把 NaN 当 0 再求和 | 加法；可选忽略缺失值 | **`filter=true` 是抗 NaN 技巧**，写 Alpha 常用 |
| `densify(x)` | 把很多分桶的分组字段压缩成"实际存在"的少量分桶，提高计算效率 | 分组字段瘦身 | 知道概念即可 |
| `divide(x, y)` 或 `x / y` | x 除以 y；**除以 0 会报错**，可用 `divide(x, add(y, 0.0001))` 加微小量避免 | 除法；分母加 epsilon 防除零 | **除零报错是高频坑**，考试易考 |
| `inverse(x)` | x 的倒数 1/x；**x=0 报错**，用 `inverse(add(x, 0.0001))` 避免 | 取倒数 | 同上，防除零 |
| `log(x)` | 自然对数；常用于正值数据的变换 | 对数变换 | 配合正向字段用（如市值、成交量） |
| `max(x, y, ...)` | 所有输入的最大值，**至少 2 个输入** | 取最大 | 注意最少 2 参 |
| `min(x, y, ...)` | 所有输入的最小值，至少 2 个输入 | 取最小 | 注意最少 2 参 |
| `power(x, y)` | x 的 y 次方；**y 非整数时可能丢失 x 的符号** | 幂运算 | 要保符号就用 `signed_power` |
| `reverse(x)` 或 `-x` | 取相反数 | 负号 | 与 `-x` 等价 |
| `sign(x)` | 符号函数：正→1，负→-1，零→0；输入 NaN 则输出 NaN | 判断正负 | 官方给了例子：(2,-3,5,6,3,NaN,-10)→(1,-1,1,1,1,NaN,-1) |
| `signed_power(x, y)` | x 的 y 次方但**保留 x 的符号** | 保号幂 | `power` 的防坑版 |
| `sqrt(x)` | 非负平方根，等价 `power(x, 0.5)`；**x<0 无定义** | 开方 | x<0 时用 `signed_power(x, 0.5)` 保符号 |
| `subtract(x, y, filter=false)` 或 `x - y` | 从左到右相减，支持 ≥2 个输入；`filter=true` 把 NaN 当 0 | 减法 | 与 add 对称 |

---

## 四、Logical 逻辑算子（10 个）

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `and(input1, input2)` | 两个输入都为真（=1）才返回 1，否则 0 | 与 | 逻辑与 |
| `if_else(input1, input2, input3)` | 条件为真返回第一个值，否则返回第二个值 | 三目运算符 | **等价 `? :`**，写条件 Alpha 核心 |
| `input1 < input2` | input1 小于 input2 返回 1，否则 0 | 小于比较 | 返回 0/1 掩码 |
| `input1 <= input2` | input1 小于等于 input2 返回 1，否则 0 | 小于等于 | 同上 |
| `input1 == input2` | 两输入相等返回 1，否则 0 | 相等比较 | 可做掩码 |
| `input1 >= input2` | input1 大于等于 input2 返回 1，否则 0 | 大于等于 | 同上 |
| `input1 != input2` | 两输入不同返回 1，否则 0 | 不等比较 | 同上 |
| `is_nan(input)` | 输入是 NaN 返回 1，否则 0 | 缺失值标记 | 处理数据缺失常用 |
| `not(x)` | 逻辑非：x=1 返 0，x=0 返 1 | 取反 | 与 and/or 组合 |
| `or(input1, input2)` | 任一输入为真返回 1，否则 0 | 或 | 逻辑或 |

> 速记：比较算子和 `is_nan` 的输出都是 **0/1 掩码**，可直接乘到别的 Alpha 上做条件开关（见《IQC提示》示例 8/9 的 `? :` 用法）。

---

## 五、Time Series 时间序列算子（23 个）—— 考试重头

> 共同特征：对**单只股票**过去 **d 天**的数据做运算，参数里的 `d` 就是回看天数。

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `days_from_last_change(x)` | 距 x 上一次发生变化过去了多少天 | 变量多少天没变了 | 低频字段用 |
| `hump(x, hump=0.01)` | 限制输入变化的大小和幅度，从而**降低换手率** | 给变化加"限速" | 降换手技巧之一 |
| `kth_element(x, d, k, ignore="NaN")` | 回看 d 天，取其中第 k 个值，可忽略 NaN | 取过去第 k 个值 | **常用于回填缺失数据、提升 long-short count** |
| `last_diff_value(x, d)` | 过去 d 天中，与当前值**不同**的最近一个值 | 上次变到几 | 事件类思路 |
| `ts_arg_max(x, d)` | 过去 d 天内最大值距今几天；今天最大返回 0，昨天最大返回 1 | 最高点几天前 | 判断"峰值是否近期" |
| `ts_arg_min(x, d)` | 过去 d 天内最小值距今几天 | 最低点几天前 | 同上 |
| `ts_backfill(x, lookback=d, k=1)` | 用 lookback 窗口内最近的有效值**回填 NaN**，提升覆盖率、降低缺失风险 | 缺失值前向填充 | **覆盖率工具，考试常提** |
| `ts_corr(x, y, d)` | x、y 过去 d 天的 Pearson 相关系数 | 两序列相关度 | 因子相关性/配对交易 |
| `ts_count_nans(x, d)` | 过去 d 天 NaN 的数量 | 数缺失 | 数据质量检查 |
| `ts_covariance(y, x, d)` | 过去 d 天 y 与 x 的协方差 | 同向变动程度 | 比 corr 少归一化 |
| `ts_decay_linear(x, d, dense=false)` | 过去 d 天做线性衰减加权平均，平滑数据、降低旧值/缺失值影响 | **近重远轻的加权均值** | **降换手核心算子**；第四课讲过公式：权重和 = N(N+1)/2 |
| `ts_delay(x, d)` | 返回 d 天前的 x | 取历史值 | **防未来函数**；`ts_delay(close, 1)` = 昨收 |
| `ts_delta(x, d)` | x 与 d 天前之差 | 变化量/动量 | **反转因子核心**：`-ts_delta(close, 2)` |
| `ts_mean(x, d)` | 过去 d 天简单均值 | SMA | 移动平均 |
| `ts_product(x, d)` | 过去 d 天连乘；用于几何均值、复利/增长率 | 连乘 | 几何收益用 |
| `ts_quantile(x, d, driver="gaussian")` | 滚动窗口内把数据重塑/归一化分布 | 分位变换 | driver 可选 gaussian/cauchy/uniform |
| `ts_regression(y, x, d, lag=0, rettype=0)` | 对 y、x 做回归，返回回归相关参数 | 时序回归 | **rettype 决定返回什么**（示例 6 用 rettype=3 返回回归估计值） |
| `ts_scale(x, d, constant=0)` | 把时序缩放到 0~1 区间，可按最小值偏移 | 归一化 | 与横截面 normalize 区分 |
| `ts_std_dev(x, d)` | 过去 d 天标准差 | 波动率 | 分母/波动因子 |
| `ts_step(1)` | 返回天数计数器，每天加一 | 第几天了 | 官方示例签名如此显示 |
| `ts_sum(x, d)` | 过去 d 天求和 | 累加 | 基础算子，SMA 的分母 |
| `ts_zscore(x, d)` | 当前值距近期均值几个标准差 | 标准化 | **事件触发常用**（示例 12：|z|>3.5 触发） |
| `ts_winsorize(x, d, std=4.0)` | 过去 d 天所有非 NaN 值的**去极值均值**：按 std 倍标准差裁剪极端值后取均值 | winsorized 均值 | 抗离群值的均值，std 默认 4.0 |

---

## 六、Cross Sectional 横截面算子（5 个）—— 考试重头

> 共同特征：**当天**在所有股票（或组内股票）之间横向比较，与时间无关。

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `normalize(x, useStd=false, limit=0.0)` | 当天截面减去市场均值居中；可选再除以截面标准差，并把结果限制在 [-limit, +limit]；NaN 不参与均值/标准差 | 去均值（去市场敞口） | `useStd=true` 时 ≈ zscore 的简化版；`limit` 做限幅 |
| `quantile(x, driver=gaussian, sigma=1.0)` | 对 Alpha 值排名并移位，再套用指定分布（gaussian/cauchy/uniform）压离群；sigma 控制尺度 | 排名后映射到分布 | 比 rank 更强力的离群处理 |
| `rank(x, rate=2)` | 在所有股票中排名，输出 0.0~1.0 均匀分布 | 百分位排名 | **写 Alpha 收尾最常用**：消除量纲 |
| `winsorize(x, std=4)` | 把数据限制在均值 ± std 个标准差内；**std 取 2~5**：std=2/3/4/5 分别剔除约 4.5%/0.27%/0.01%/0.0001% 极端值 | 缩尾去极值 | 高频考点：**std 越大剔除越少** |
| `zscore(x)` | 距均值几个标准差 | 截面标准化 | 与 ts_zscore 区分：这是当天全体股票 |

---

## 七、Vector 向量算子（2 个）

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `vec_avg(x)` | 对向量字段的每个元素取均值，把向量数据降成单个矩阵值 | 向量压成标量（平均） | **向量数据必须先降维**（第四课重点） |
| `vec_sum(x)` | 对向量字段所有元素求和 | 向量压成标量（求和） | 同上 |

---

## 八、Transformational 变换算子（2 个）

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `bucket(rank(x), range="0, 1, 0.1", skipBoth=False, NaNGroup=False)` | 按排名的数值区间把数据切成自定义分桶，供 group_* 算子使用 | 自定义分桶 | **两种写法**：`range="0,1,0.1"`（0~1 步长 0.1 的等宽桶）或 `buckets="2,5,6,7,10"`（自定义断点）；配合 `group_neutralize`/`group_rank`/`group_zscore` |
| `trade_when(x, y, z)` | 仅当条件满足时改变 Alpha 值，否则保留旧值；退出条件下可用 NaN 平仓；**降低换手、控制交易时机** | 条件交易/条件保持 | **三参数**：`trade_when(条件, 新值, 否则值)`；第三课/示例 10、12 已反复演练 |

---

## 九、Group 分组算子（5 个）

> 共同特征：都带 `group` 参数（sector / industry / subindustry / country / 自定义分组），在组内做操作。

| 算子（签名） | 官方描述（译） | 大白话 | 考试速记 |
|---|---|---|---|
| `group_mean(x, weight, group)` | 计算数据字段在每组内的（加权）均值 | 组内均值 | 带 weight 权重参数 |
| `group_neutralize(x, group)` | 组内每个值减去组均值（中性化） | 组内去均值 | **等价 Simulation 面板的 Neutralization**；代码里用了它，面板就要选 None |
| `group_rank(x, group)` | 组内排名，输出 0.0~1.0 | 组内百分位 | 示例 3/4：子行业内排名 |
| `group_scale(x, group)` | 组内缩放到 0~1，跨组可比 | 组内归一化 | 与 ts_scale 区分 |
| `group_zscore(x, group)` | 组内 Z-score | 组内标准化 | 与 zscore 区分 |

---

## 十、考试速查卡（一页版）

### 最容易考的三组对比
| 易混 | 区别 | 一句话 |
|---|---|---|
| `rank` vs `group_rank` vs `ts_rank` | 全体排名 / 组内排名 / 时序排名 | 横截面 / 分组 / 时间 |
| `sum` vs `ts_sum` | 截面求和（当天所有股票） / 时序求和（单股过去 d 天） | `sum` 没有 `ts_` 前缀 |
| `zscore` vs `ts_zscore` vs `group_zscore` | 截面 / 时序 / 组内 | 看有没有 `ts_`/`group_` |
| `normalize` vs `ts_scale` | 横截面去均值 / 时序缩放 0~1 | 一横一纵 |

### 高频防坑点
1. **除零报错**：`divide` / `inverse` 遇到 0 直接报错 → 加 epsilon：`divide(x, add(y, 0.0001))`。
2. **`power` 丢符号**：y 非整数时 x 符号可能丢失 → 用 `signed_power`。
3. **`add` / `subtract` 的 `filter=true`**：把 NaN 当 0，抗缺失值。
4. **`winsorize` 的 std**：默认 4，取值 2~5；**std 越大，剔除的极端值越少**。
5. **向量字段必须降维**：`vec_avg` / `vec_sum` 后才能进入矩阵运算。
6. **trade_when 三参数**：`(条件, 满足时的值, 否则的值)`，否则值传 `-1`/`NaN` 可平仓/空仓。
7. **代码里用了 `group_neutralize`，Simulation 面板 Neutralization 选 None**。
8. **掩码用法**：比较算子返回 0/1，可直接乘法开关信号（示例 8/9/11）。

### 各思路首选算子（写 Alpha 起点）
| 想做 | 首选算子 |
|---|---|
| 反转（均值回归） | `-ts_delta(close, d)` + `rank` |
| 动量/趋势 | `ts_delta` / `ts_mean`（SMA） |
| 价值 | `group_rank(eps/close, subindustry)` |
| 降换手 | `ts_decay_linear`、`hump`、`trade_when` |
| 覆盖率不足 | `kth_element`、`ts_backfill` |
| 事件触发 | `ts_zscore` + `trade_when` |
| 消除市场/行业敞口 | `normalize` / `group_neutralize`（或面板 Neutralization） |
| 去离群 | `winsorize` / `quantile` / `rank` |
| 相关性/回归 | `ts_corr` / `ts_regression` |

---

## 十一、来源与核对说明

- 本文档所有算子签名、官方描述均来自 `docs/operators.pdf`（BRAIN 官方 Operators 页面 7 页截图）的 OCR 识别，其中第 2/3/5/7 页共 4 处 OCR 乱码已通过区域放大重识别核对（`input1 <= input2` 描述、`ts_step` 签名、`ts_winsorize`、`group_mean`）。
- 页面标注的等级徽章均为 **base（基础级）**；官方说明提示更高等级（Expert/Master/Grandmaster Genius）会解锁更复杂的算子，本 PDF 未包含。
- 中文"大白话"与"考试速记"为备考整理，不属于官方原文。
- 关联文档：《BRAIN_快速表达式_IQC提示与Alpha示例题库.md》（基础语法 + 13 示例 + 高频精选）、《BRAIN_零基础学量化第二课_数据与算子.md》、《BRAIN_零基础学量化第四课_Decay_Vector_Do_Dont.md》。
