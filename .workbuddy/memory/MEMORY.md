# WorldQuant Brain 项目长期记忆

> 平台硬约束/目录/接口坑/常用命令以根目录 `CLAUDE.md` 为准；判死 15 项明细见 `CLAUDE.md` §6 与 `docs/methodology/00_总纲.md`（唯一事实源）。当日数值写 `.workbuddy/memory/YYYY-MM-DD.md`。

## 范围与纪律（李工定，永久有效）
- 本工作区只做 WorldQuant。助手「阿衡」，称呼「李工」。
- **目标定下必须完成；完成不了给根因和补救，不是道歉。不能一直欠账、不能说"明天就干"。缺资源直接开口要。挖到就提交。**
- **李工 0920 加码：不允许"停下汇报再问怎么办"——自主连打直到当日目标清零或给出硬阻塞；工具故障（git 代理/编码/终端）是自己要绕过的问题，不许归因"系统问题"当理由。**
- 每轮汇报必含：本轮提交数、台账总数（唯一 id 口径）、当日（美东）计数、剩余欠账。入池数才算数。
- 考试红线：考核进行中不提供答案（含限次数准入测评）；"禁止 AI/禁止合成数据"条款的活：判断做、代写造数不做。
- 质量闸门只升不降：S+F ≥ 4.0 + tS ≥ 1.25 + 无 FAIL。每日 5 个是下限；欠账顺延（当日目标 = 5 + 历史欠账）。

## 口径
- 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` 唯一事实源，只追加，计数=**唯一 id**（行数≠id 数）。0920 有效提交 90（1YX6MA0M 入池后）。
- 美东口径：北京 12:00 = 美东 00:00。
- 算子坑（0920）：**本账号 `ts_min`/`ts_max` 不可用**（区间极值用 `close/ts_delay(close,N)-1` 替代）；`hump(x,0.01)` 只收 1 参；表达式算子上限 64（约 5 条腿）。

## ★★ 相关判决是两条路（0920 重大修正，李工点破）
- ① 直通：本地 max corr ≤ 0.685。
- ② **豁免线：候选 S ≥ 1.10 × max(所有 corr≥0.7 对手的 S) → 平台放行**（corr 到 0.82+ 也过）。实证：LLNXEe7L（corr 0.7642、S2.30 vs 2.02）、1YX6MA0M（平台 corr 0.8222、S3.26 vs 2.91）双双入池。
- **对手 S 取平台实况**（`GET /alphas/{id}` is.sharpe，缓存 `pool_s.json`）。**台账 S 列是空的** —— 0920 查实的工具级根因：0916 修 bug 把对手 S 源改成台账 row[2]，而 row[2] 从无数据 → 豁免线永远算不出 → 判决退化为纯 corr 硬阈值 → 三周 0 提交。
- **判决工具统一 `src/submit/submit_exempt.py`**（'前缀*' --min-sf 4.0 --min-ts 1.25 --limit N --tag X [--dry]）；`auto_submit_passers.py` 只实现直通，不再用于判决。
- **同族兄弟 S 也进对手集合**：新成员入池即抬高兄弟豁免线（1YX6MA0M S3.26 入池 → 同族 corr 0.93~0.97 的兄弟门槛 3.59 全挡）。
- **池子 Sharpe 地图（0920）**：90 条，max 3.45 / median 2.36；≥3.0 仅 7 条，2.5~3.0 有 19 条，2.0~2.5 有 49 条。**撞中低 S 对手时门槛只有 2.2~2.7** → 造 S≥2.6 的候选放进"只与中低 S 对手相关"的区域最划算。

## 提交判决机制
- 判决 4~9 秒出。`POST /alphas/{id}/submit` → 轮询：`403 + is.checks` = 判决书；ACTIVE = 入池。**唯一判据：出现 FAIL 才是拒信**（403 全 PASS 无 FAIL = 都过）。`SELF_CORRELATION=PENDING` 是未提交默认占位符。提交器 `src/submit/submit_v3.py`；其 POST-403 分支只打 300 字符且不落档 → 用 `_autologs/full_verdict.py` 重取全文再手工补 SUBMIT_VERDICTS.csv。
- `correlations/self` 端点弃用；判决书 `is.selfCorrelated.records` 自带对手明细 = 提交即测量。
- 卡单≠失败：POST 201 后 status=None 仍可能已 ACTIVE，必须 GET /alphas/{id} 核实。
- ⚠️ **auto_submit_passers 重算盲区（0920）**：刚提交的 alpha PnL 未发布、进不了重算池 → 同批同骨架兄弟本地 corr 虚低、本地放行、平台 403（LLNXPaea 0.9143 撞 zq8jl99K）。**对策：一骨架每美东日只提交 1 条；提交成功后同批同骨架全部冻结，次日换新锚组骨架。**

## 相关性墙与工具
- 墙是自己砌的：候选池同质（assets/close 97% 共享）。杠杆优先级：缩放基准(/cap) > 分组 > 锚选择；换锚基本无效。
- **引擎腿 = 质量引擎 = corr 来源，同一条腿**（cash45/cfoev45，ts_av_diff 45 窗口）。新信号轴只能叠加、不能顶替 PV/锚。
- `src/analysis/pnl_corr.py`：本地算 self-corr（pnl recordset 累计须先差分），平台 ≈ 本地 +0.006~0.017 → **直通缓冲线本地 ≤ 0.685**。池子只能取自台账。
- `src/analysis/leg_lab.py`：腿库离线拼装。系统性低估 maxcorr +0.05~0.19（shared 占比越大偏移越大，标定定律）→ 搜索阈值压 --max-corr 0.55~0.57，实跑后必须 pnl_corr 复核。
- 拥挤腿：CASH45 / CFEV45 / PV / TXTUB / XRENT / PTPR。
- 中性化投影（救急）：下移 −0.14~0.27，一个几何只吃 1~2 口；MARKET 伤 tS、SECTOR 保 tS；只救 corr 0.70~0.72 近门槛。工具 `src/mine/mine_neut_convert.py`。

## 过墙配方（有效）
| 手法 | 实例 | 关键 |
|---|---|---|
| 加腿稀释/独有锚/换价量腿 | w60_h~w77_a .65~.69 | 一个配方只能吃一口，锚必须独有 |
| 系数加权改 PNL 构成 | w85_a .754→.6803 | 独有锚全权 + 共享 PV 降权 0.5 |
| 7 腿配方（Research16） | w121_d SF5.30 | 3 fnd6 锚+引擎+PV+评级 |
| /cap 缩放破墙 | kqoq0zed .6999 | 质量天花板 ~3.93 |
| leg_lab 离线拼装 | pwRwWoJ3 SF6.91 | 只跑单腿建库，组合离线算 |
| ★ 第 5 腿加挂（0920 主力） | zq8jl99K SF4.67/tS1.50 corr .6801 | 已验证骨架原样不动（2.0 argmin10 主腿+双锚+0.5 引擎），第 5 腿挂事件条件化腿 0.5~0.75（evh60a/ev60nb）。事件腿不能顶替锚（w213b tS 全塌） |
| ★★ 高 S 主腿（0920 第一生产力） | 1YX6MA0M SF5.20/S3.26 | `2.5*group_rank(-ts_rank(close/open-1, 10), subindustry)`（日内涨跌 10 日时序排名取反）+ 3 条 0.5 锚 + 0.4 引擎。**豁免线规则下追高 S 比追低 corr 更值**。注意它当天就把整个日内反转族收掉（w219 七条 S2.8~3.08 全被 3.59 门槛挡） |

## 已证伪（勿再试，明细见总纲）
- 换区域/风险中性化/PPA/universe/truncation/D0/换字段换锚/新数据轴单独成腿/腿稀释量产/decay 拉大/逐腿 group_zscore/顶层 zscore——全判死；456 积压最低 corr 0.6934。
- 冷字段≠可挖（aC<30 平台无数据，假达标判据：不同锚指标完全相同）；用 COLD_FIELD_WHITELIST.csv（不外推 fundamental2）。
- 事件条件化 argmin 腿：单腿全弱（S −0.23~0.74），"老低点做多"方向死；evh60a（新鲜高点做空 S0.74）只配当第 5 腿。
- w209 经典风格几何（低波/长反转/vol收缩/量能异动/流动性/动量）当主腿 0/8，最高 S 0.64。
- 纯骨架全 0.5 共享腿无价值（corr≈1.0）；TOP1000/500 换池；INDUSTRY/SECTOR 中性化单独用；强 trade_when 门控。

## 研报移植
- 球队硬币帖：CHN 无权限；可移植隔夜/日内拆分、条件符号切换、换手距离。元教训：破局 = 叠加其他数据 + 不同数理方法处理同一数据。
- Research16（分析师）：ts_mean 对离散字段先连续化；`? : NaN` 是 CONCENTRATED_WEIGHT 头号成因改 if_else；评级字段全 VECTOR 须 vec_avg。

## 备考/面试
- 研究顾问面试+背调约 10 月中旬落定，期间正常挖矿攒 Rank。材料：四小时课程（80%+）+ Learn 文档 + 平台常用内容；28 份归档在 docs/exam、docs/study。缺口"能背≠能讲"：待做自己的 Alpha 3 分钟故事、按考纲口述对练、数值速查卡。仅用李工给的资料。
