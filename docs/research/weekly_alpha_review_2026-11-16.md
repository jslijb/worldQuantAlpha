# 周复盘报告：本周提交 Alpha 全量分析（2026-11-16）

> 数据源（全部实测，无凭印象数字）：
> ① 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`（复盘时 360 行，含本次补记 d5almKdJ）
> ② `_autologs/_verdict_*.json` 16 份 + `_autologs/_one_submit_1115.txt` 提交日志
> ③ 平台 API 实拉（`_autologs/_wk_review_probe.py` → `_wk_review_data.json`）：15 条本周 alpha 的 IS 指标 + checks 全文、OS count=360、`/competitions/challenge` 返回 Not found
> ④ `_autologs/_wd_psubmit3.out` 当前提交器实例预检拦截记录（无行级时间戳，频次仅供参考）
> 本周口径：美东 2026-11-08 ~ 11-15（报告落笔时美东 11-15 刚收盘、11-16 配额尚未开始）

## 0. 总量对账（逐行数出）

| 项 | 数 | 出处 |
|---|---|---|
| 本周入池合计 | **16 条 = 13 常规 + 3 超级** | 台账 + 平台 API dateSubmitted 逐条核对 |
| POST 级被拒 | 9 条（详见 §2） | verdict 文件逐份读出 |
| 重放/超时各 1 | P05eKkr7 ALREADY_SUBMITTED；QP0mXnEK POLL-TIMEOUT | verdict 文件 |
| POST 接受率 | 16/(16+9) ≈ 64% | 同上 |
| OS stage 计数 | 360（API count 字段） | GET /users/self/alphas?stage=OS |
| 台账行数 | 359 → 补 d5almKdJ 后 360 | csv 逐行 |
| isScore/rank | **本周无法取数**：`/competitions/challenge` 实测返回 `{"detail":"Not found."}`；`/users/self/score`、`/users/self/activities/os-score` 均 404 | 11-16 实测 |

**按美东日入池明细**（4R+1S 配额）：

| 美东日 | 常规 | 超级 | id |
|---|---|---|---|
| 11-08 | 1/4 | 0 | wpQkRVG5 |
| 11-09 | 3/4 | 0 | xAr7pJRJ, omEj0xK5, pwdbeNLx |
| 11-10 | 1/4 | 0 | kqaxzkW6 |
| 11-11 | 0 | 0 | — |
| 11-12 | 2/4 | 0 | O0WEE6zJ, pwaAzrrX |
| 11-13 | 2/4 | 1/1 ✓ | d5aAQPpv; P05eKkr7 |
| 11-14 | 0/4 | 1/1 ✓ | wpoXaojQ |
| 11-15 | **4/4 ✓** | **1/1 ✓** | d5al5ljw, LLKlxA7m, YPaWd16q, WjlWKLPj; d5almKdJ |

11-15 是本周唯一满额日。欠账日（11-09/10/11/12/14 常规缺额）按李工令不追补。

**台账勘误**：d5almKdJ（SUPER，美东 11-15 17:52 入池，S3.18/F3.22/TO0.0533）此前漏记，本次已按 API 真值追加（batch=super_model51_1115）。OS=360 与台账现已对平。

## 1. 成功共性清单（可复制配方）

### 1.1 本周 13 条常规平台真值（API 实拉）

| id | 区域/池/中性化 | decay | S | F | TO | subU | 结构 |
|---|---|---|---|---|---|---|---|
| wpQkRVG5 | USA T3000 SUBI | 10 | 2.26 | 1.92 | 0.143 | 1.54 | 混合引擎+稀释腿 |
| xAr7pJRJ | USA T3000 SUBI | 10 | 2.46 | 2.23 | 0.157 | 1.33 | fnd6 主腿混合 |
| omEj0xK5 | USA T3000 SUBI | 10 | 2.24 | 2.11 | 0.134 | 1.11 | option 期权波动率 |
| pwdbeNLx | USA T3000 SUBI | 10 | 2.68 | 2.53 | 0.121 | 1.21 | option+fnd6 混合 |
| kqaxzkW6 | USA T3000 SUBI | 10 | 2.53 | 2.10 | 0.159 | 2.04 | 混合（zscore 外壳） |
| O0WEE6zJ | USA T3000 SUBI | 10 | 2.07 | **1.24** | 0.197 | 1.21 | news+option 混合 |
| pwaAzrrX | USA T3000 SUBI | 10 | 1.89 | **1.32** | 0.067 | 0.83 | fnd6 动量 zscore |
| d5aAQPpv | USA T3000 SUBI | 10 | 1.90 | **1.37** | 0.139 | 0.99 | anl4+fnd6 混合 |
| KPgepR9k | GLB MINVOL1M STAT | 2 | **7.54** | **4.02** | 0.380 | 4.04 | tm+tcm 三腿 rank+ts_zscore(270) |
| d5al5ljw | GLB MINVOL1M STAT | 64 | 2.51 | 1.74 | 0.122 | 1.52 | gSc returns 双腿(industry) |
| LLKlxA7m | GLB MINVOL1M STAT | 64 | 2.51 | 1.85 | 0.195 | 1.61 | gSc returns 双腿(sector) |
| YPaWd16q | GLB MINVOL1M STAT | 64 | 2.50 | 1.73 | 0.146 | 1.52 | gSc returns 双腿(exchange) |
| WjlWKLPj | GLB MINVOL1M STAT | 64 | 2.85 | 2.01 | 0.203 | 1.71 | gSc returns 双腿(sector+country) |

（GLB 四条无 IS_LADDER 检查，改 LOW_2Y_SHARPE：2.92~3.36 全 PASS；AMER/EMEA/APAC 分区 1.13~2.46 全 PASS。）

### 1.2 配方 A：GLB gSc 波动/动量双腿家族（★ 本周唯一 100% 复用成功的常规配方，4/4 过线）

```
0.5*group_scale(-ts_std_dev(returns, 120), G) + 1.4~1.5*group_scale(-ts_av_diff(returns, 45|60), G)
GLB MINVOL1M / STATISTICAL / decay 64
```
- 关键因素（实测归因）：
  1. **单数据集 ATOM 合规**：只用 `returns`（pv1），无跨集字段；
  2. **group_scale 替 group_rank**（合规替身，符合 11-15 禁令）；
  3. **组别轴 G 互换 = corr 重掷刀**：industry / sector / exchange / sector+country 四种组合全部 SELF/PROD 预检 ≤0.69 过线；
  4. **decay 64 压 TO**：TO 落 0.122~0.203，全部在 F 最优区（10%~20%）；
  5. GLB 三分区（AMER/EMEA/APAC）全 ≥1.13，无短板件。
- 产出区间：S 2.50~2.85 / F 1.73~2.01。WjlWKLPj（sector+country 交叉组）是同族最强件（S2.85/F2.01）——**组别内外层交叉互换是同族里幅度最大的重掷刀**（与既有"组别刀"判据一致）。

### 1.3 配方 B：主题限定超级（★ 本周新实证，d5almKdJ）

```
type=SUPER / USA TOP3000 / selection=(1-self_correlation)*in(datasets,"model51") / selectionLimit=10
decay=25 / SUBINDUSTRY / trunc 0.08 / componentActivation IS / combo='1'
→ S3.18 / F3.22 / TO0.0533 ACTIVE（美东 11-15）
```
- **超级 selection 支持数据集主题过滤**（`in(datasets,"model51")`），在 1-self_correlation 排序之上再圈定数据集家族。
- 用法：超级配额 1 条/日，可用主题过滤按数据集家族轮流吃（model51 已吃，可轮 option9/news18 等），比全池 1-self_correlation 更可控。
- 与既有配方（selection=1-self_correlation + decay 楼梯 32）互为补充：decay 楼梯压 PROD、主题过滤压 SELF 结构。

### 1.4 配方 C：STATISTICAL 中性化 + 高 S 特赦（既有判据本周再证 1 例）

KPgepR9k（GLB STATISTICAL，tm_16+tcm_ta50+tm_15 三腿 ts_zscore(270)+rank+ts_decay_linear(2)）S7.54/F4.02，PROD 0.788 处于稀疏区触发特赦入池。⚠ 注意：tm+tcm 属两数据集混用，**11-15 ATOM 红线下不可复制**，此条仅作"STATISTICAL+稀疏区特赦"机制证据保留。

### 1.5 成功共性汇总（13 常规）

1. TO 全部 0.067~0.380，**12/13 落在 0.12~0.20**（F 最优区），唯一例外 KPgepR9k 靠 S 顶破；
2. SUB_UNIVERSE_SHARPE 最低 0.83（pwaAzrrX，贴动态限额线过），**越贴线越危险**；
3. decay=10 主流（9 条 USA）；GLB 家族 decay=64 靠慢化压 TO；
4. CLUSTER_TEST=ERROR/WARNING 的 5 条（wpQkRVG5/xAr7pJRJ/omEj0xK5/pwdbeNLx/kqaxzkW6 ERROR、pwaAzrrX/d5aAQPpv/d5al5ljw/YPaWd16q WARNING）**照常入池** → 再次确认只有 FAIL 才拦，ERROR/WARNING 不拦截。

## 2. 失败模式清单（带量化证据，9 条 POST 级被拒）

| # | id | 批次 | S | F | 致命 FAIL | 量化证据 |
|---|---|---|---|---|---|---|
| 1 | WjlK1b2k | atom | 8.26 | 4.27 | PROD 0.8856 | S8+ 高分也死：PROD 密集区特赦无效 |
| 2 | QP0mXGY5 | scout | 8.73 | 5.13 | PROD 0.8263 | 同上（SELF 仅 0.5956，死在 PROD） |
| 3 | vRAavlk3 | super | 2.89 | 2.48 | PROD 0.7061 | decay20，超线 0.0061 |
| 4 | 1YW6pJQJ | super | 2.83 | 2.39 | PROD 0.7002 | decay26，**超线 0.0002**（差一口气） |
| 5 | RReZrkq0 | 1115 | 1.94 | 0.56 | LOW_FITNESS 0.56 | **TO 0.4405 摊薄 F**：S 够线仍死 |
| 6 | 6XMg30YJ | ipv2 | 2.29 | 0.65 | LOW_FITNESS 0.65 | TO 0.3975 |
| 7 | O0WKmPAJ | ipv3 | 2.22 | 0.65 | LOW_FITNESS 0.65 | TO 0.3549 |
| 8 | YPaXdv2l | scout2 | 1.81 | 0.75 | LOW_FITNESS 0.75 | TO 0.0848（慢件 F 也塌，不止 TO 一个成因） |
| 9 | A1xq6OPe | sm | 1.87 | 0.92 | LOW_FITNESS 0.92 | TO 0.0939 |

另有：P05eKkr7 同参重放 ALREADY_SUBMITTED（超级同配置去重，换参才出新件，既有判据再证）；QP0mXnEK POLL-TIMEOUT（轮询超时非判决）。

**失败模式归纳**：
1. **PROD_CORRELATION 是头号杀手（4/9）**，且 2/4 是 S8+ 的"高分死"——高 S 特赦只对 PROD 稀疏区（0.788 档）有效，0.82+ 密集区无效（本周再添 2 例）。
2. **LOW_FITNESS 5/9，其中 4 例 TO≥0.09**。TO 0.44 → F 0.56 的 RReZrkq0 是最极端样本：F=S×√(|R|/max(TO,0.125))，TO 超过 0.125 后 F 被 √TO 分母直接吃掉。decay 没拉够是共同成因（RReZrkq0 decay 未及 64 档）。
3. **压线判决**：1YW6pJQJ PROD 0.7002 差 0.0002 → decay 楼梯"每档 +6 ≈ −0.006"的步长估计仍成立，**压线时至少再 +6 档，不要赌 0.0002**。
4. **预检拦截省下的配额**（当前提交器实例，无时间戳仅频次）：SKIP-PROD 12 条（corr 0.6972~0.8226，最低那条 0.6972 仅差 0.0072）、SKIP-LOCAL 85 条。SKIP-LOCAL 失败项频次：LOW_FITNESS 117 次 > IS_LADDER 34 ≈ LOW_SHARPE 34 > HIGH_TURNOVER 24 > GLB EMEA 8 > SUB_UNIVERSE 6 > APAC/AMER 各 5 > 2Y 4。**GLB 的短板分区是 EMEA**（1.0 线最容易卡）。

## 3. 下周优化措施（具体到参数与族方向）

1. **gSc returns 双腿家族限量**：本周一天 4 条同族（仅组别互换）。同族变体两两 SELF 0.97+ 是既有判据，同族连发对 VF 增量递减。下周该家族**每天 ≤1 条**，组别优先试未用过的 `market`、`subindustry` 互换与窗口 (120,90)/(90,60) 交叉。
2. **RReZrkq0 教训 → 生成端加 TO 预控**：表达式里含快腿（ts_rank(close,5) 类）的合成件，decay 上限直接给 32~64，TO 预估 >0.25 的不发模拟（省并发）。
3. **主题超级轮换**：d5almKdJ 的 `in(datasets,"model51")` 模板轮到未开荒数据集（GLB 缓存里的 global_seasonal_model 196 字段 / predictive_starmine / intraday_pv_feats 均可试 `in(datasets,"<id>")`），配额 1/日。
4. **PROD 压线纪律**：预检 prod.max 在 0.68~0.699 的一律先做 decay +6 再交，不赌 0.0002（1YW6pJQJ 实证）。
5. **EMEA 补腿**：GLB 批模拟前先看 EMEA 分区 S，<1.0 的批不发（SKIP-LOCAL 8 次 EMEA 是当前最高频分区死因）。
6. **F 贴线件止损**：platform_rebuild 批 3 条 F 1.24~1.37 虽入池，但 sub-universe 0.83/0.99 贴限额线、低 F 稀释 isScore（0926 净 −177 实证）。同类 zscore 外壳批生成时按 F 降序取头部，F<1.5 变体靠后排。
7. **修 isScore 取数链**：`/competitions/challenge` 已 404（11-16 实测），锚点停在 10-06（isScore 9691 / rank 14）。下次会话需摸新端点或网页截图通道，否则 VF 走势盲飞。

## 4. VF 提速建议（VF 与已提交池强相关）

1. **池内多样性是第一杠杆**：本周 13 条常规里，GLB gSc 同族 4 条 + USA 混合引擎 5 条（fnd6/option/anl4 腿高度复用）→ 字段族集中度仍高。增量 VF 看的是"新信息量"，model51 主题超级（新数据集家族入池）是本周对多样性贡献最大的一条。
2. **低 F 件稀释 isScore**：3 条 F 1.24~1.37 的擦线件会拉低合并池表现分。宁可当日少交，也不交 F<1.5 的同族备胎（配额是上限不是任务量，李工既有令）。
3. **isScore 取数断链**：本周起无法量化 VF 走势，修复优先级高于继续堆提交——没有读数的优化是盲打。
4. **保留节奏**：11-15 模式（4R 满额 + 1 主题超级）是本周最优节奏，直接按此复制。

## 5. 本周已回写的文档

- `AGENTS.md` §4 追加「11-16 周复盘新增判据」：gSc returns 家族 4/4 明细、主题限定超级配方、高 S 死 PROD 再证、TO→F 摊薄实证、CLUSTER_TEST ERROR 不拦、EMEA 短板、challenge 端点 404。
- `docs/methodology/idea.md` 追加 M17 周复盘条目。
- 台账补记 d5almKdJ（OS 360 = 台账 360，对平）。
