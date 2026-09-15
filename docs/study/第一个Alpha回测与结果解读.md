# BRAIN 第一个 Alpha 回测与结果解读

> 来源：BRAIN 官方“回测你的第一个 Alpha”教程。适合快速掌握 Simulate 页面操作、结果页指标含义，以及什么样的 Alpha 才值得提交。

---

## 一、创建并运行第一次回测

### 操作步骤

1. 进入 **Alphas → Simulate** 页面。
2. 点击右上角 **齿轮图标**（Settings）打开设置面板。
3. 设置：
   - **Region / Universe**：`US: TOP3000`
   - **Neutralization**：`Subindustry`
   - 其他保持默认或按需求调整
4. 点击 **Apply** 应用设置。
5. 确认 **Code** 和 **Result** 都被勾选。
6. 在表达式框中输入：

```
-ts_delta(close, 5)
```

7. 点击 **Simulate** 开始回测。

![第一个 Alpha 回测界面](docs/images/first_alpha_simulation.jpg)

> 上图左侧是表达式输入区，右侧显示累计 PnL 或 Sharpe Ratio 图表。图表可放大到更短的时间段（如 1 个月或 1 年）查看细节。底部信息块包括 IS Summary、Correlation、IS Testing Statuses、Properties。

---

## 二、什么样的 Alpha 是“好”的

### 2.1 核心判断标准

| 指标 | 好 Alpha 的特征 |
|---|---|
| **累计 PnL（Cumulative Profit）** | 持续上升，波动小 |
| **Annual Return** | 较高 |
| **Sharpe Ratio** | Delay 0 Alpha > 2.0；Delay 1 Alpha > 1.25 |
| **% Profitable Days** | 较高 |
| **Profit per Dollar Traded** | 较高 |
| **Drawdown（%）** | < 10% |
| **Turnover（换手率）** | 较低，但不低于 1% |

> 即使收益很高，如果图表波动剧烈、回撤大，也会被判定为不够好。

### 2.2 案例：`-ts_delta(close, 5)` 为什么被评为 Inferior

模拟设置：

| 设置 | 值 |
|---|---|
| Region | USA |
| Universe | TOP3000 |
| Language | Fast Expression |
| Decay | 0 |
| Delay | 1 |
| Truncation | 0.08 |
| Neutralization | Market |
| Pasteurization | On |
| NaN Handling | Off |
| Unit Handling | Verify |
| Max Trade | Off |
| Max Position | Off |

IS Summary 显示：

![IS Summary - INFERIOR](docs/images/is_summary_inferior.png)

关键指标：

| 指标 | 数值 | 评价 |
|---|---|---|
| Sharpe | 1.52 | 低于 Delay 1 的 1.25 看起来刚及格，但年度波动大 |
| Turnover | 40.32% | 明显偏高 |
| Fitness | 0.65 | 偏低 |
| Returns | 7.39% | 一般 |
| Margin | 3.66‰ | 一般 |

问题所在：

- 2017 年 Sharpe 跌至 **1.00**，Fitness 仅 **0.29**，收益走平。
- 2014、2015 年出现较大回撤。
- 整体高波动、低收益稳定性，因此被标记为 **INFERIOR（Needs Improvement）**。

> 这个案例说明：光看 Sharpe 不够，还要看**年度稳定性、回撤、换手率**。

---

## 三、结果页各模块解读

### 3.1 Chart 图表

- 默认显示 **Cumulative PnL（累计盈亏）**。
- 可切换到 **Sharpe Ratio** 图表。
- 支持缩放查看不同时间段。

### 3.2 IS Summary

展示样本内（In-Sample）回测的汇总指标：

| 指标 | 含义 |
|---|---|
| **Sharpe** | 夏普比率，风险调整后收益 |
| **Turnover** | 换手率，平均每日交易金额占比 |
| **Fitness** | 综合质量评分 |
| **Returns** | 年化收益率 |
| **Margin** | 每单位交易成本对应的收益 |
| **Long Count / Short Count** | 每日多头/空头持仓数量 |

### 3.3 Correlation（相关性）

- 点击绿色刷新按钮，可查看当前 Alpha 与你 OS 股票池中其他 Alpha 的**相关性**。
- 高相关性 Alpha 会被平台认为冗余，提交前会检查 Correlation 标准。

### 3.4 Properties（属性）

用于管理和标注 Alpha：

| 字段 | 作用 |
|---|---|
| **Name** | Alpha 名称（如 `AlphaAmy`） |
| **Category** | 类别（如 `Price Reversion`） |
| **Tags** | 自定义标签（如 `HolySharpe`、`Best`） |
| **Color** | 颜色编码 |
| **Description** | 简短描述，方便自己理解 |

![Alpha Properties](docs/images/alpha_properties.png)

> 建议：自定义标签不要过多，否则 My Alphas 页面会难以搜索。

---

## 四、提交 Alpha（OS 测试）

### 提交流程

1. 回测完成后，进入结果面板 **Submission** 标签页。
2. 点击 **Submit Alpha** 按钮。
3. 提交前平台会自动检查：
   - **Correlation 标准**
   - **Sharpe 标准**
4. 通过后进入 OS（Out-of-Sample）测试。

### 提交前自检清单

- [ ] Sharpe 满足标准（Delay 0 > 2.0，Delay 1 > 1.25）
- [ ] Drawdown < 10%
- [ ] Turnover 较低但不低于 1%
- [ ] 累计 PnL 走势平稳，无大回撤
- [ ] 与其他 Alpha 相关性不过高
- [ ] Alpha 已正确命名、分类、加标签

---

## 五、考试速查卡

| 考点 | 标准答案 |
|---|---|
| 进入 Simulate 后点哪个图标设置 | 右上角齿轮 / Settings |
| 示例设置 Universe | US: TOP3000 |
| 示例 Neutralization | Subindustry |
| 第一个示例表达式 | `-ts_delta(close, 5)` |
| 好 Alpha 的 PnL 特征 | 持续上升、波动小 |
| Delay 0 好 Alpha Sharpe | > 2.0 |
| Delay 1 好 Alpha Sharpe | > 1.25 |
| Drawdown 上限 | < 10% |
| Turnover 下限 | 不低于 1% |
| Inferior 的主要原因 | 高波动、大回撤、年度收益不稳定 |
| IS Summary 里 Fitness 含义 | 综合质量评分 |
| Correlation 模块作用 | 查当前 Alpha 与 OS 池 Alpha 的相关性 |
| Properties 里 Tags 建议 | 保持少量，便于搜索 |
| Submit Alpha 前检查 | Correlation + Sharpe 标准 |

---

## 六、常见错误

1. **只看总 Sharpe 不看年度**：2017 年 Sharpe 跌到 1.00，说明信号阶段性失效。
2. **忽视 Turnover**：40%+ 换手率会严重侵蚀收益。
3. **标签泛滥**：自定义标签过多导致后续难以管理。
4. **未检查相关性就提交**：高相关 Alpha 很难通过提交审核。
5. **PnL 高但回撤大**：平台更偏好稳健而非暴利。
