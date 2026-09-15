# WorldQuant Brain 项目长期记忆

> 只记长期有效的口径、结论、约束。当日数值/进度/欠账写 `.workbuddy/memory/YYYY-MM-DD.md`。

## 范围与角色
- **本工作区只做 WorldQuant**；AI Agent 那摊（金融智能体平台 / chat_bi / rag_pdf）属别的项目。助手名「阿衡」，称呼「李工」。
- **考试红线**：考核进行中不提供答案（含限次数的准入/入驻测评；"开卷"与"未禁用 AI"均不改变判断）。只做考后复盘、考前陪练。不评判用户、不贴标签。

## 目标与口径
- **每日 5 个高质量 alpha 是下限不是上限**；**不删除**已提交的；欠账顺延（当日目标 = 5 + 历史欠账）。
- **"高质量"定义**：S+F ≥ 4.0 + testS ≥ 1.25（验证期不崩）+ corr < 0.7 或豁免（豁免线 = 1.10 × max(所有 corr≥0.7 对手的 S)，候选 S 达线即可提交）。
- **台账**：`alpha_quality_analysis/SUBMITTED_LEDGER.csv`，唯一事实源。**累计满 100 → 启动 Super Alpha**（每天 1 个、与 Regular 分开计酬、组合池选低相关互补因子、提交前过 Test Period 预检）。
- **美东口径**：北京 12:00 = 美东 00:00；dateSubmitted 自带 -04:00；北京 03:00 = 美东 15:00 平台更新。

## 平台硬约束（实测）
- **并发模拟上限 = 2**（超过报 429 CONCURRENT_SIMULATION_LIMIT_EXCEEDED）；脚本须 max_workers=2 + 429 退避。
- **字段类型必须过滤**：`fnd6_*` 明细多为 VECTOR（事件型），`divide` 不支持事件输入。查 `GET /data-fields?...&type=MATRIX`；fundamental6 有 574 MATRIX / 312 VECTOR。清单存 `alpha_quality_analysis/fnd6_matrix.json`。
- **`_v1300` 后缀字段 delay=0 不可用**（unknown variable）。
- **算子** `GET /operators` → 66 个（存 `operators.json`）。有 ts_regression / ts_corr / ts_std_dev / ts_zscore / ts_decay_linear / group_neutralize / hump / trade_when / bucket / quantile；**无** ts_skewness / ts_kurtosis（写 `ts_std_dev`，不是 ts_stddev）。
- **选字段看 alphaCount 越低越不易撞车**；coverage 在 USA/TOP3000/delay1 恒为 0.5，无区分度。
- **脚本坑**：台账 CSV 首列带 BOM，必须 `utf-8-sig` 读，否则 DictReader 的 id 键全空、去重失效（0913 翻车过一次）。
- **轮询限速**：<1.3 秒高频打 corr 端点会被服务器 RST（WinError 10054）。间隔不低于 Retry-After，且必须捕获 ConnectionError。

## 相关性（极重要）
- **相关是动态的**：同一表达式预检 corr 从 0.616 → 0.9879，只因中途提交了两个结构相似的因子。self-corr 是对**当前已提交池**实时算的 → 提交后必须对剩余池**重新预检**，旧结论作废；同构候选严禁扎堆。
- **破墙法则**：**锚腿（冷门字段）+ 价量腿同时换**（双轮换）。避开最拥挤的 `ts_delta(close,2)` + `volume/ts_mean(volume,60)`。
- **拥挤腿**：CASH45 / CFEV45 / PV / TXTUB / XRENT / PTPR（骨架饱和 corr 0.75-0.93）。

## 已验证有效的过墙配方（按时间）
| 手法 | 实例 | 关键 |
|---|---|---|
| 五腿稀释 | w60_h corr 0.6548 | 加腿摊薄共享成分 |
| 独有分析师锚 | w64_h GI锚 corr 0.6605 | 锚必须独有 |
| 换价量腿 | w68_b PVD5(ts_delta5+vol90) corr 0.6948 | 同换锚+PV |
| 双独有 analyst4 锚 + 换PV腿 | w77_a corr 0.6598 | 但**一个配方只能吃一口**，同骨架复制必互撞 |
| **腿系数加权改 PNL 构成** | w85_a corr 0.754→0.6803 | 独有 fnd2 锚全权 + 共享 PV 尾部降权 **0.5**（甜点；0.3 质量崩） |
| **7 腿配方（Research16 移植）** | w121_d/3q9NMgk6 SF5.30 testS2.26 | 3 fnd6 锚 + 引擎腿 + PV腿 + 分析师评级腿 |

**共性 = 必须有独有成分腿。**

## 已证伪（勿再试）
- TOP1000/500 换池（S 崩且 testS 全 <1.25）；INDUSTRY/SECTOR 中性化单独用；truncation 放开；PV 腿微调；D0 独立性。
- 纯复制冠军骨架换锚（w69 系 corr 0.78-0.88）；单锚嫁接稀释不够（batch74 corr 0.78-0.89）。
- 全新 fnd6 腿当**主腿**质量全灭（cash45/cfoev45 是质量引擎，不能丢）。
- 新信号族单独用无 Sharpe（PCR/情绪/评分/新闻 w72/w73 全灭）；fundamental2 脚注字段覆盖太低。
- **强 trade_when 门控伤质量**。
- **`rank(ts_regression(...))>0.6` 可信度门控无增量**（rettype 0/2/3 三组 SF 4.08/4.36/4.25 在噪声内）。`rettype` 官方语义仍未标定（社区口径 0=残差/1=截距/2=斜率/3=预测值/6=R²，待实测）。

## 未开发大陆
news12（875 字段）、fundamental2（766）、pv13（165）、option8、model51 —— quality 未跑通，需与骨架混搭；真实数据集 ID 待查。

## 研报/论文移植结论
### 球队硬币帖（0914，详 `LESSONS_20260914_球队硬币与挖矿复盘.md`）
- CHN 无权限实测：region=CHN pv1 count=0、TOP500 亦 0 → 不可直接复现。
- **可移植 4 招**：①隔夜/日内收益拆分（`open/ts_delay(close,1)`）②条件符号切换（`group_mean(x,1,market)` 做截面比较翻转符号 = 结构级差异）③换手距离（abs(换手变化量−市场均值)）④**Slow+Fast Factors 中性化从未测过**（未试杠杆）。
- 元教训：贴主"优秀量价因子 PnL 殊途同归"（行业中性化公共库 corr≈0.8）= 我们 PV 腿怎么换都撞墙的原因。破局 = 叠加其他数据（已做）+ **不同数理方法处理同一数据**（未做）。

### Research Paper 16：分析师短期交易思路（详 `BRAIN_Research16_分析师短期交易思路_20260915.md`）
- Birru / Gokkaya / Liu / Stulz, *Journal of Finance* 77(3):1829-1875 (2022)，DOI 10.1111/jofi.13130。
- 论文自家三版 S+F 仅 1.86 / 2.08 / 2.69，**远低于我们 4.0 门槛——不能照搬，只能移植结构**。论文讲 trade ideas，表达式实现的是评级变化，**不是同一数据对象**。
- **两条铁律**：① `ts_mean` 对**离散字段**降换手无效，须先连续化（rank/zscore/vec_avg）再平滑；② **`? : NaN` 是权重集中（CONCENTRATED_WEIGHT）头号成因**，改 `if_else(cond,·,0)`。降换手：`trade_when` 第三参用 **-1**（保持仓位）而非 0；`hump(x,0.01)` 优于 ts_mean。
- **字段权限**：账号**无独立 analyst 数据集**，**`rating` 字段 404**。等价 4 个评级字段全在 analyst4 且**全为 VECTOR，必须 `vec_avg`**：`anl4_fs_detail_rec_v4_nd_estimate`(aC=24，最冷门) / `anl4_basicdetailrec_ratingvalue`(574) / `anl4_eaz2lrec_ratingvalue`(5886，热) / `anl4_total_rec`(2646)。delay=0/1 均可用。
- **⚠️ 铁律（第二次实证）**：**新信号轴只能叠加、不能顶替 PV 腿**——顶替后 testS 从 2.08 崩到 0.28–1.13 + LOW_SUB_UNIVERSE_SHARPE（与 0914 batch113 同因）。**PV 腿 = 验证期稳定性来源。**
- **⚠️ 修正 0914**：**市值分桶中性化不是普适杠杆**，只在信号已有质量基础时放大效果。
- **改写 0913 的"analyst4 撞墙"**：撞墙的是**离散度/估值轴**；**评级偏离度轴可用**。瓶颈不在质量在**相关性**——没跑 corr 不下结论。
- **风险**：同骨架共用分位桶会互撞（0913 实证 0.82–0.95）→ 提交前须备多个不同桶+不同锚变体。

## 服务停摆期
平台 `correlations/self` 对**全新 alpha** 返回 `200 + Retry-After + 空 body` 即未恢复。**探针必须用从未算过 corr 的候选**——缓存 alpha（如 E5vj5YdL）曾有历史 records，会造成"已恢复"假阳性。模拟（回测）服务不受影响。详见 `.workbuddy/memory/automations/a9b2c5cd-*`。`auto_submit_loop.py` 的 `service_ok()` 用缓存探针 → 恒 True 空转抢队列，勿开。

## 关键事实
- selfCorr ≥ 0.7 触发 Production Correlation 测试；通过 = max corr < 0.7 **或** Sharpe 比相关 alpha 高 10%。
- Sharpe ≈ 15.8 × IR（BRAIN 的 Sharpe 即 IR 年化版）。
- Fitness = Sharpe × √(|R| / max(T, 0.125))。

## 🗂 项目结构（0915 重构，后续严格执行）
> 规范源 = 根目录 `CLAUDE.md`（含放置规则、维护约定、变更记录）。**动手前先读它。**
- `src/` 全部代码（`core`/`submit`/`mine`/`ops`/`tools`/`archive`）——25 个 py，零例外；脚本自带"向上找 brain_credentials.txt 定位项目根"代码块，可从任意位置调用。
- `data/alpha_quality_analysis/` 全部数据（**台账 `SUBMITTED_LEDGER.csv` 唯一事实源**；`mined/` 1098 json；`candidates_all.csv` 1098 条；`candidates_unsubmitted_qualified.csv` **456 条未提交达标**；`leg_value_rank.csv` 207 条单腿排行）。
- `docs/` 全部文档（`methodology/` 六子目录 / `research` / `study` / `exam`（考试资料单独）/ `project` / `reference` / `archive`）。
- `_autologs/` 运行日志。根目录只留 `CLAUDE.md`/`README.md`/`brain_credentials.txt`。
- **历史脚本已于 0915 提取经验后清除**（404 个 py）；表达式与结果完整存于 `src/archive/expr_library.py`（ALL_EXPR 1098 / LEG_VALUE 207 / PY_ONLY 1314 / QUALIFIED 460）。外挂全量备份：`D:\Python\worldquant_backup_20260915\`（0915 重构前快照，勿删）。
- **版本控制（0915 接入）**：git 仓库（分支 `main`），全部代码/数据/文档入库，`.git` 约 35M。远端 `origin` = `https://github.com/jslijb/worldQuantAlpha.git`。
  - ⚠️ **该远端当前是 Public（公开），因此尚未推送**——需李工先去 GitHub 仓库 Settings → General → Danger Zone → Change visibility 改为 Private，之后才能推。
  - `git_snapshot.py` 已内置**公开仓库拦截**：推送前匿名探测远端可见性，检测到 public 即中止（退出码 4）并告警，须显式加 `--allow-public` 才放行。`--no-push` 可只提交不推。
  - **每挖完一批 Alpha 必须提交一次**（约定）。统一走 `src/ops/git_snapshot.py`——自动识别变更、自动生成提交信息（如 `mine(w122): 新增 9 条候选 / 台账 +3`）、无变更时跳过、`--dry-run` 可预演。**不要手写 git add/commit**。
  - **凭据红线**：`brain_credentials.txt` 由 `.gitignore` + `pre-commit` 钩子双重拦截，**永不入库**。禁止 `git add -f` 与 `--no-verify`。
  - **钩子源文件已版本化**于 `src/ops/git-hooks/pre-commit`（`.git/hooks/` 本身不入库）：换机器后执行 `cp src/ops/git-hooks/pre-commit .git/hooks/ && chmod +x .git/hooks/pre-commit`。
  - 不进库的：凭据、工具缓存（`.codegraph`/`.codeartsdoer`/`.arts`/`.freebuff`）、`*.log`、`.workbuddy` 除 `memory/` 外部分。
  - 两个定时任务（`07ac2d4a` 每日挖矿 / `a9b2c5cd` 补提交）prompt 已加入"收尾执行 git_snapshot"步骤。

## 📊 历史挖掘实证（0915 从 1098 条记录提炼，详 `docs/methodology/`）
- **460/1098 达标（41.9%）但只提交 60 个 id → 456 条达标候选从未提交**；历史瓶颈是相关性墙不是质量。
- **参数决定生死**：`ts_av_diff(...,45)` SF **6.19** vs `(...,30)`+`(...,60)` SF **1.33** → **45 是甜点，30/60 死亡区**；量能窗口 **120>60>90**。
- **包装决定换手**：裸 `rank(x)` SF2.38/T0.469 → `group_rank(x,subindustry)` SF5.89/T0.152（全过率 26.2%→54.4%）。
- **结构甜点**：5–6 腿（A/B 档占 61%，E 档 1–4 腿占 74%）；给腿加 0.5 权 → 全过率 67%→**18.2%**。
- **最强腿**：`group_rank(fnd6_xrent/assets,subindustry)` **77.3%**；**最强字段签名** `cashflow_op+enterprise_value+fnd6_xrent` **95.2%**。

## ⚠️ 术语译法规范（强约束）
量化领域术语**按行业习惯译**，禁止字面直译（用户点名批评"Pasteurization→股票池消毒"）：

| 英文 | ✅ 正确 | ❌ 禁止 |
|---|---|---|
| Pasteurization | 池外标的置空（按池过滤） | 消毒 |
| Margin | 单位成交盈亏（PnL/成交额，bps） | 保证金 |
| Production Correlation | 在产 Alpha 相关性 | 生产相关性 |
| Instrument / Universe | 标的 / 股票池 | 工具 / 宇宙 |
| Book size | 账面规模（多空双边名义敞口，默认 2000 万） | — |
| Truncation | 单票权重上限 | 截断 / 去极值 |
| Lookback Days / Fitness | 回溯窗口（天）/ 适应度 | 体能 |
| IS Ladder Sharpe / Region / Test Period | IS 分段夏普稳定性 / 市场区域 / 验证期 | — |

备考总纲已含「术语译法对照表」，新增术语须同步维护。
