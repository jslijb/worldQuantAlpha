# checks FAIL 全解（1098 条实测分布）

> 数据源：历史记录的 `is.checks` 字段
> 用途：模拟出结果后看 FAIL 就知道病因 + 药方

---

## 一、FAIL 分布总表

| FAIL 类型 | 条数 | 占比 | 中位 turnover | 腿数特征 |
|---|---|---|---|---|
| LOW_FITNESS | 281 | 25.6% | 19.7% | 1–4 腿占 78% |
| LOW_SHARPE | 242 | 22.0% | 15.6% | 1–4 腿占 78% |
| LOW_SUB_UNIVERSE_SHARPE | 89 | 8.1% | 13.8% | 分散 |
| CONCENTRATED_WEIGHT | 32 | 2.9% | **32.1%** | 3–5 腿 |
| LOW_TURNOVER | 20 | 1.8% | — | — |
| HIGH_TURNOVER | 10 | 0.9% | **100.3%** | **9 条是 1 腿** |

注：一条因子可同时挂多个 FAIL，故总和 >460（未达标数）。

---

## 二、逐项病因与药方

### LOW_FITNESS（281 条，最大宗）
**症状**：Fitness 低于 1.0 门槛。Fitness = Sharpe × √(|Return|/max(Turnover, 0.125))。
**病因**：Return 不够，或换手太高把分母顶大。
**腿数特征**：1–4 腿占 78% → **结构太薄**。
**药方**：
1. 补腿到 5–6 条（从 `LEG_VALUE` 挑全过率 ≥65% 的腿）
2. 若换手 >25%，先降换手（`hump(x, 0.01)` 或 `trade_when`，第三参数用 **-1** 不是 0）
3. 换主腿为 `group_rank(fnd6_xrent/assets, subindustry)`（全过率 77.3%）

### LOW_SHARPE（242 条）
**病因**：信号弱。中位换手仅 15.6%，**不是换手问题**。
**药方**：
1. 检查是不是裸 `rank()` 没分组 → 加 `group_rank(·, subindustry)`（全过率 26.2%→54.4%）
2. 检查 `ts_av_diff` 窗口是不是 30/60 → 改 45
3. 检查有没有用被证伪的字段当锚（`fnd6_txtubxintis`、单独 `enterprise_value`）

### LOW_SUB_UNIVERSE_SHARPE（89 条）
**病因**：**主力腿缺失**——最常见是砍掉了 PV 腿。
**实证**：0914 batch113 砍 PV/vol 腿、0915 batch120 用分析师腿顶替 PV 腿 → testS 从 2.08 崩到 0.28–1.13，5 条挂这个 FAIL。
**药方**：**补回 PV 腿**（`group_rank(-ts_delta(close, 2), subindustry)`），或 `rank(volume/ts_mean(volume, 120))`。
**结论**：**PV 腿是验证期（Test Period）稳定性的来源，不能顶替只能叠加。**

### CONCENTRATED_WEIGHT（32 条）
**症状**：权重过度集中，或分配权重的标的太少。
**病因**：中位换手 32.1%（全场 1.65 倍）→ **高换手导致权重漂移**；另一大成因是 `? : NaN` 把标的剔出持仓。
**药方**：
1. 换手型：`hump(x, 0.01)` 或加 decay
2. 剔除型：把 `cond ? x : NaN` 改成 `if_else(cond, x, 0)`，**保留全池持仓**
3. `group_rank` 全池铺满天然规避此问题

### HIGH_TURNOVER（10 条）
**特征**：**9 条是单腿（1 腿）裸信号**，中位换手 100.3%。
**药方**：
1. 套 `group_rank(·, subindustry)`（分组本身就降换手）
2. 加 `hump(x, 0.01)`
3. `trade_when(cond, x, -1)` —— **第三参数必须是 -1（保持原仓位）**，用 0（平仓）无效
4. `ts_mean` 对**离散字段**降换手**无效**（论文16 实测 41.43%→41.58%）；离散值必须**先连续化（rank/zscore/vec_avg 聚合）再时间平滑**

### LOW_TURNOVER（20 条）
**病因**：换手过低（低于门槛），decay 太大或信号太惰性。
**药方**：减小 decay；或删掉 `ts_mean` 平滑层。

---

## 三、FAIL 之间的因果链（重要）

```
高换手 (T>25%)
   ├─→ CONCENTRATED_WEIGHT（权重漂移）
   └─→ LOW_FITNESS（Fitness 分母被顶大）
        
1–4 腿薄结构
   ├─→ LOW_FITNESS（Return 不够）
   └─→ LOW_SHARPE（信号弱）

砍掉 PV 腿
   └─→ LOW_SUB_UNIVERSE_SHARPE（验证期崩）
```

**一个反直觉的实证**：LOW_SUB_UNIVERSE_SHARPE 组的中位换手只有 13.8%（全场最低）——**低换手不代表稳，缺 PV 腿才是真因**。

---

## 四、模拟后自检顺序（省时间）

```
1. 有 FAIL 吗？
   ├─ LOW_SUB_UNIVERSE_SHARPE → 补 PV 腿，别动别的
   ├─ CONCENTRATED_WEIGHT → 查换手 + 查有没有 `? : NaN`
   ├─ LOW_FITNESS/LOW_SHARPE → 查腿数 + 查窗口 + 查分组包装
   └─ HIGH_TURNOVER → 查是不是单腿裸信号
2. 无 FAIL 但 SF<4.0
   → 按 docs/methodology/05_历史因子复盘/02_低质量因子升级动作.md 三个动作改
3. SF≥4.0 但 testS<1.25
   → 缺 PV 腿（同第 1 条）
```

---

## 五、相关文档

- `docs/methodology/05_历史因子复盘/02_低质量因子升级动作.md` — 具体改造动作
- `docs/methodology/02_参数与设置/01_参数甜点表.md` — 参数取值
- `docs/methodology/03_过墙与提交/01_相关性墙破法.md` — 过了质量关之后的事
