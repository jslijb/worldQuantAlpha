# 遗憾规避因子研究（2026-09-06 补齐完整）

> 来源：用户提供的论坛分享 + 东吴证券研报《Alpha掘金系列之四：基于逐笔成交数据的遗憾规避因子》（作者：高智威）

## 0. 论坛原版实际表现（2026-09-06 截图分析，重要）

论坛分享的 volsig 版本在平台模拟结果：
```
volsig = (close > ts_delay(close, 1) ? volume : -volume) > 0;
volmov = ts_sum(ts_delta(volsig, 1), 5);
-volmov / ts_sum(volume, 5)
```
- Universe: **USA/D1/ILLIQUID_MINVOL1M**（TUTORIAL 权限不可用，需换 TOP3000）
- **Sharpe=0.78（cutoff 1.58，LOW_SHARPE FAIL）、Turnover=150.22%、Fitness=0.13、Returns=4.15%、Drawdown=12.13%、Margin=0.55‰**
- Checks: 2 PASS / 6 FAIL
- PnL 曲线 2013-2021 长期上涨但波动大
- **评估：曲线好看但指标全面不达标（S=0.78 vs 需1.25+；T=150% 拖垮 Fitness）。核心思想（涨跌标记主动买卖）有价值，但原始实现不可直接提交，必须大改：换 TOP3000、加 decay、融入已验证的 group_rank 组合结构。**

## 1. 理论背景（行为金融学）

非理性投资者决策时倾向于**避免产生后悔情绪并追求自豪感**，避免承认之前的决策失误：
- 投资者不愿卖出下跌浮亏的股票 → 避免失败投资导致的遗憾和痛苦
- 卖掉手中股票后发现其开始不断上涨 → 为避免遗憾和后悔，不会考虑再将其买回

## 2. 原研报逻辑（A股逐笔数据）

1. 利用逐笔成交数据，标记主动买卖单
2. 根据主动买卖，确定总体方向
3. 与收盘价比较，确定总体盈亏占比

使用数据：成交量/价、买卖单号共四列。数据颗粒度小，细节多。

## 3. WorldQuant 平台近似逻辑（美股 OHLCV）

平台无 A 股 ILLIQUID_MINVOL_1M，无逐笔单号数据，用 OHLCV 近似：

1. **用涨跌标记主动买卖**：
   ```
   volsig = (close > ts_delay(close, 1) ? volume : -volume) > 0
   ```
   即当日上涨的成交量记为主动买入量，下跌记为主动卖出量
2. 根据涨跌方向，确定总体方向
3. 与当前收盘价比较，确定相对当前盈亏占比

偏差：数据颗粒度大，损失价格变动细节。

## 4. 价格近似

- 主动买入价格：`buyprice = close > ts_delay(close,1) ? midprice : 0`
- **midprice = (close + open)/2**（高频中买卖价不全分布在 close，取开收盘均价近似逐笔成交均价）
- 主动卖出价格：`sellprice = close < ts_delay(close,1) ? midprice : 0`

## 5. 四个因子公式（已提取）

| 因子 | 公式 | 含义 |
|------|------|------|
| HCVOL | Σ volume_buyᵢ × I(p_buyᵢ > close) / total_volume | **买入浮亏成交量占比**（买入价高于现价的主动买入量占比） |
| LCVOL | Σ volume_sellᵢ × I(p_sellᵢ < close) / total_volume | 卖出反弹成交量占比（卖出价低于现价的主动卖出量占比） |
| HCP | Σ price_buyᵢ × I(p_buyᵢ > close) / close − 1 | 买入浮亏价格偏离 |
| LCP | Σ price_sellᵢ × I(p_sellᵢ < close) / close − 1 | **卖出反弹价格偏离**（用户挑选此因子） |

**用户挑选：HCVOL 与 LCP 两个因子构建**

## 6. 研报 setting（截图中部分可见，待完整补充）

- 美股替换 A 股；universe 疑似 TOP3000/ILLIQUID 类（待用户补充完整截图）
- delay/decay/neutralization 待确认

## 7. FASTEXPR 实现要点（下会话实施参考）

- 条件表达式：WorldQuant 支持 `if_else(cond, x, y)` 或三元 `?:`（需验证）
- 累计求和：需要用 ts_sum 之类的窗口算子模拟"Σᵢᴺ"（N 日窗口内累计）
- 指示函数 I(·)：用 `close > ts_delay(close,1)` 与成交量相乘实现
- 初步表达式构想（HCVOL 近似，20日窗口）：
  ```
  buy_vol = if_else(close > ts_delay(close, 1), volume, 0)
  hcvol = ts_sum(if_else(midprice > close, buy_vol, 0), 20) / ts_sum(volume, 20)
  ```
  （待验证算子可用性和信号强度）

## 8. 与现有 26 个 Alpha 的关系

- **全新行为金融学信号维度**，与现有 8 个基本面维度 × 3 种价格信号完全正交
- 预期自相关性低（<0.5），有利于突破当前信号池饱和
- 可提高 Uniqueness（当前 0.40）
- 风险：条件表达式+窗口累计可能 turnover 偏高，需配合 decay 和短窗口

## 9. 论坛"三大融合避坑指南"评估（对现有因子的适用性）

| 指南 | 现状评估 | 借鉴价值 |
|------|---------|---------|
| 1. 量纲吞噬：加法前先 rank/group_zscore 标准化 | ✅ 已符合：所有组合因子都是 group_rank 相加，无量纲问题 | 无需改动 |
| 2. 自相关：缩短窗口，3-5 天短周期反转 | ⚠️ 我们用 20 日窗口偏长；但 5/10/20 日 lookback 已验证互不相关 | 中等：可试更短窗口的新因子 |
| 3. 换手率：ts_decay_linear 3天平滑 + **adv20 流动性降权** | ❌ **从未尝试 adv20 流动性权重**，全新技巧 | **高**：公式最外层乘流动性权重可降摩擦成本提升 Fitness |