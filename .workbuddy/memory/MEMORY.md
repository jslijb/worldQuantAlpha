# WorldQuant Brain 项目长期记忆

> 明细以 `CLAUDE.md`（硬约束/接口坑/判死明细 §6）与当日 `.workbuddy/memory/YYYY-MM-DD.md` 为准；本文件只留跨日仍成立的判据与结论，当日数值一律写当日日志。

## 一、纪律与节奏（李工定，最高优先）
- 工作区只做 WorldQuant；阿衡 / 李工。目标定下必须完成，完成不了给根因和补救，不道歉；不许"停下汇报再问怎么办"。每轮汇报必含：本轮提交 id+指标、台账总数（唯一 id 口径）、当日美东计数、剩余欠账。**入池数才算数。**
- 考试红线：考核进行中不提供答案；"禁止 AI / 禁止合成数据"的活：判断做、代写造数不做。
- ★★ 目标 = `challenge` 榜 rank 进前 10（0921 拍板）；`leaderboard.isScore` 即比赛分口径，禁止再质疑。0922 rank 130→81 已进前 100。前 30 榜单逐日建档 `docs/project/leaderboard_top30_daily.csv`（`_autologs/lb_record.py`，勿重跑同日）。
- ★★ 每美东日提满 5 条，绝不空仓（Days 权重最重且会主动流失，断签不可逆；不交不只是少攒一天）。"上限 2 条 / 只交 F>均值"口径作废（0922 李工："说提 5 个只交 2 个是摆烂"）。
- ★★ 提交质量标准（0926 李工定死进 CLAUDE.md §5，修改必须审批）：**S+F≥4.0、tS≥1.25、TO≤20%、无 FAIL 四条全过才交**；0922 的"tS≥1.0、TO≤50%"口子作废。凑不满 5 条就少交实报欠账，禁止贴线货凑数（0925~0926 放宽交货致合并分掉 177，实证）。改 CLAUDE.md 必须李工审批，他要求加的必须执行。
- 自动化 `07ac2d4a-0c98-4e36-a3e7-49c5a06c777b`：北京 12:05（=美东 00:05）跑；执行前必读 `.workbuddy/automations/<id>/memory.md`，执行后追加摘要。

## 二、排名口径
- rank 由 Total（Days + IS + Uniq）决定；榜单 3AM EST 刷新；北京 12:00 = 美东 00:00。排名 = 相对分（Δ我 − Δ对手），提日分 = 提 Quality。
- ★ isScore 是"表现分"不是累计积分：官方 scoring=PERFORMANCE；实测 0925→0926 净 −177（8923→8746，rank 50→57），且 ΣS/ΣF 对不上总数 ⇒ 非逐条求和，是合并池表现动态重算、会掉。官方 FAQ 原话：Gold(10000) 后转合并表现分，"新的 Alpha 提交可能会降低你的合并表现分数"；一线顾问实证：合并表现按过往 3 个月综合质量评定，**fit 1.03+sc 0.1 提组合、fit 1.98+sc 0.68 拉低组合**——selfCorr 权重高于单条 F。0926 掉分根因=低 F(1.0~1.3)+高 sc(0.67~0.69) 密集提交稀释合并池。资格赛积分体系（双因子归一化/日上限 2000/无负分）是 Gold 前的历史阶段，与 isScore 两套系统勿混。含义：低 corr 互补候选边际贡献 > 高 selfCorr 条；OS 差的条目拖累合并分。锚点序列 `_autologs/_isscore_history.csv`（自动化每日追加），攒 2 周回归定死。
- 前 10 中位：Days 37 / IS 12837 / Uniq 0.72；我们日均 345 > 336 ⇒ 差在 Days 不在速率；Uniq 已持平。对标 HG77739（32 天/377 分·天）走得通；HL19556（48 天/239）⇒ 门槛是持续性不是夏普。Days 会主动流失（前 10 九人 17 天平均 −5.1）。

## 三、相关性墙（唯一出量通道）
- 两条路：①直通 max corr ≤ 0.685；②豁免 S ≥ 1.10 × max(corr≥0.66 对手的 S)。need 时变必须实时算，对手集合收全（漏收即误判）；三个阈值 corr-floor / corr-count / corr-direct=0.685。本地 0.685~0.69 不判死，直接 POST 测。
- 权威测量 = POST /alphas/{id}/submit 判决书：**出现 FAIL 才是拒信**（403 全 PASS 无 FAIL = 过）；POST 后 status=None 须 GET 核实 ACTIVE（卡单≠失败）。对手 S 取 GET is.sharpe → pool_s.json（台账无 S 列）。
- 墙高分布（355 条实测）：99.7% 候选 corr>0.70 ⇒ 出量靠"换轴 + 改造边界候选"，不靠新挖。
- 规律：①"提 S"的改造必须先量 need（降 decay 会把强家族拉进对手集，need 反涨）——判据顺序"先 corr/need 后 S"；②同族兄弟 decay 差只在 corr 0.70~0.75 边界区有效（代价 TO↑F↓，保底弹药）；③换池是 corr 第一杠杆，换池候选历史 corr 读数一律作废（随池增长失效）。
- 近失池极小（1616 被墙里 gap≤0.05 仅 4 条且多为次品）。

## 四、已证伪（勿再试；明细 CLAUDE.md §6）
- 换区域 / 风险中性化 / PPA / D0 / 新材质当主腿（news/socialmedia/option/model16/51）/ 腿稀释量产 / decay 拉大 / 逐腿或顶层 zscore / 纯骨架共享腿 / 强 trade_when 门控 —— 全判死。
- decay 是 S↔TO 跷跷板，只在低靶区用、停在拐点。alpha 强度来自基本面比率腿（cash45/cfoev45 等），不是反转骨架。
- 最强单条 XgbgNwna 是已提交 pwRwWoJ3 的去腿降权版（corr 0.96+）结构性死结；w158/w189/n160 全族 corr 地板 ≈0.70；w182/w193 七腿价值族只能冲 S≥3.66，暂搁。

## 五、池内同质度
pairwise corr 均 0.358 ⇒ n_eff≈2.7；62 字段前 8 占引用 75%；275 骨架族 ⇒ 是同一条 alpha 的几百个变体，不是 N 次机会。

## 六、Universe 轴
TOP2000 死；TOP1000 有效（F 掉 1.2~1.65）；TOP500 非普适（顶级骨架出量，别的家族撞 LOW_SUB_UNIVERSE_SHARPE，逐条验 FAIL）。**一池一家族只吃一口**；换池要分散源骨架簇。工具 `mine_univ_convert.py` / `diverse_pick.py`。

## 七、平台硬边界
FAIL 全集 6 种：LOW_FITNESS / LOW_SHARPE / LOW_SUB_UNIVERSE_SHARPE / CONCENTRATED_WEIGHT / HIGH_TURNOVER / LOW_TURNOVER。平台线：F≥1.0、TO≤70%、无 tS 检查 ⇒ 我们的 tS≥1.25+TO≤20% 极保守（放宽需李工点头）。带任何 FAIL 不交。池内 tS min≈1.02、F 均值≈1.87。

## 八、Fitness / 换手
F = S×√(|R|/max(TO,0.125)) ⇒ TO 10%~12.5% 最优（<12.5% 无额外收益）。高换手批 S 高 0.5+ 但 F 反低 0.3+。降 corr 杠杆：中性化只投 MARKET（S≥2.7 才试，伤 S/tS）> 换分组 bucket（零成本、换对手池）> sweetspot 低靶区。

## 九、算子与字段
不可用：ts_skewness/kurtosis/co_skewness/co_kurtosis/moment/entropy/median/returns/theilsen/triple_corr/**min/max**。残差显式写 y − ts_regression(y,x,d,rettype=3)。向量字段（news_*/scl*/analyst4_*）须 vec_avg/vec_sum。`? : NaN` 是 CONCENTRATED_WEIGHT 头号成因 → if_else。算子上限 64（约 5 腿）；拥挤腿 CASH45/CFEV45/PV/TXTUB/XRENT/PTPR。

## 十、账号拉取
count = 唯一总数口径（只读 results/next 漏 count 是顽固错型）；offset 上限 1000；过滤器写 `settings.universe=`（`universe=` 平台不认）。全量拉取 `src/pull/pull_unsubmitted.py`（dateCreated 天级分片）。

## 十一、工具与坑
- 台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`：唯一事实源，只追加，utf-8-sig，**id 第 0 列**。
- 工具：judge_now / pair_now / screen_pool_corr / find_passers / near_miss / axis_surgery（单轴手术，可叠源 mined id）/ diverse_pick / smallpool_now / tab / dump_set。**提交前三道体检：check_fail_hist / one_corr / pair_now。**
- 后台任务必须 run_in_background（`nohup &` 会被回收）；长批次 Bash `> log 2>&1`，PowerShell Out-File 掐进程且 UTF-16（还原 ungarble.py）。
- Retry-After 退避 min(ra,15~20)；认证必须带重试（偶发 ProxyError/SSL EOF）。
- `/alphas/{id}/correlations/self` 不可用（200 空 body），corr 自己拉 PnL 算。
- Python 统一 `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`。

## 十二、权限与备考
仅 USA 区域；数据集 14 个。顾问通道四步（李工 0926 口述，此前漏记 3 次）：①每天提交 1-2 个 Alpha 攒积分（日上限 2000）到 10000 → ②邀请成为研究顾问 + 笔试 → ③面试 → ④背调（约 1 个月）。**当前状态：10000 积分是过去式，已过笔试，处于面试阶段**；Super Alpha 无权限（与提交条数无关），level GOLD ✓ / SHORTLIST ✓ / consultant 403 ✗。后续挖 Alpha 因子与 10000 分没有任何关系——那是资格赛历史。"科研"= 拿论文处理结构套已有数据（skill `wq-research-porting`）。备考材料 28 份归档 docs/exam、docs/study；缺口"能背≠能讲"。
