# WorldQuant Brain 项目长期记忆

> 明细以 `CLAUDE.md`（红线/纪律/导航）与当日 `.workbuddy/memory/YYYY-MM-DD.md` 为准；当日数值一律写日志，本文件只留跨日仍成立的判据。

## 一、纪律（最高优先）
- 目标=challenge 榜 rank 进前 5、力争第一；每日 5 条（下限）~8 条（加压）+历史欠账，绝不空仓。每轮汇报必含：提交 id+指标 / 台账总数（唯一 id 口径）/ 当日美东计数 / 剩余欠账；入池才算数。
- challenge 无结束日期（perpetual）；isScore 是合并池动态重算的"表现分"非累计积分，低 F/高 selfCorr 提交会稀释分数（0926 净 −177 实证）。对账锚点 `_autologs/_isscore_history.csv`。
- 质量门（李工 1009 批准回写 CLAUDE.md §1）：S+F≥4.2 / tS≥1.3 / TO≤20% / 无 FAIL；corr 直通线 0.65。

## 二、排名
- rank=Total(Days+IS+Uniq)，榜单 3AM EST 刷新，北京 12:00=美东 00:00。前 10 中位 Days 37 / IS 12837 / Uniq 0.72；我们日均 ~345 超对手，差在 Days；Days 会主动流失（前 10 十七天均 −5.1）。

## 三、相关性墙（唯一出量通道）
- ★ 本地 corr ≈ 平台 selfCorr：`平台 = 0.988437×本地 + 0.011202`（n=55，R²=0.9956，RMSE=0.0032）。⚠ fast_corr.py 有 bug 不可信；**corr_predict.py / corr_pair.py 才是正确口径**。平台 0.70 ⇔ 本地 0.6969；提交线=本地 cmax≤0.70（留余量 ≤0.65）。
- ★ `GET /alphas/{id}/check`：未提交 alpha 即返平台 SELF_CORRELATION，**不耗提交配额**；首调常空 body，轮询 1~2 轮出值；只有 result==FAIL 才算 FAIL（每条恒有 1 个 SELF_CORRELATION=PENDING，"checks 全 PASS"恒为 0）。
- 豁免路线实测不可靠（blblxz5M 超 need 仍被拒），不得当常态；平台硬阈值 0.7。
- 每次入池后 corr 地貌全变（JjQPJPLA 0.6875→0.9991），历史判决作废；corr_predict.py 每次现算，无需清缓存。
- 低 corr 与高 tS 结构性冲突：f2 无人区最低 corr 料 tS 仅 0.04~0.18；破法=低 corr 字段当**差异化配腿**嫁接强结构，不单独做主腿。
- 存量池 445 条全死：平台 corr 最低 0.7754，全是同族早被收录。
- 工具：corr_predict.py（**提交前必跑**）/ plat_sweep.py（批量平台真值）/ corr_poll.py / corr_pair.py+corr_model2.py（有新成对样本时重算系数回填 corr_predict 顶部）。

## 四、已证伪（勿再试；明细 atoms.md）
换区域 / 风险中性化 / PPA / D0 / 新材质当主腿(news/socialmedia/option/model16/51) / 腿稀释量产 / decay 拉大 / 逐腿或顶层 zscore / 纯骨架共享腿 / 强 trade_when 门控；regression_neut / vector_neut / floor / tanh / sigmoid / s_log_1p / ts_decay_exp_window / ts_median / scale_down 平台无权限；arc_tan 不可用；期权快照 event 字段 FASTEXPR 不支持。

## 五、池内同质度
pairwise corr 均 0.358 ⇒ n_eff≈2.7；62 字段前 8 占引用 75%；275 骨架族=一条 alpha 的几百变体。

## 六、Universe
TOP2000 死；TOP1000 有效(F 掉 1.2~1.65)；TOP500 非普适但 oci+cfo 骨架站得住（1010 实证）。一池一家族只吃一口；工具 mine_univ_convert.py / diverse_pick.py。

## 七、平台硬边界
FAIL 6 种：LOW_FITNESS / LOW_SHARPE / LOW_SUB_UNIVERSE_SHARPE / CONCENTRATED_WEIGHT / HIGH_TURNOVER / LOW_TURNOVER。平台线 F≥1.0 / TO≤70% / 无 tS 检查；带任何 FAIL 不交。

## 八、Fitness/换手
F = S×√(|R|/max(TO,0.125)) ⇒ TO 10%~12.5% 最优。降 corr 杠杆：MARKET 中性化(S≥2.7 才试) > 换分组 bucket > sweetspot 低靶区。

## 九、算子与字段
不可用：ts_skewness/kurtosis/co_skewness/co_kurtosis/moment/entropy/median/returns/theilsen/triple_corr/min/max。残差显式 y−ts_regression(y,x,d,rettype=3)。向量字段须 vec_avg/vec_sum。`? : NaN` 是 CONCENTRATED_WEIGHT 头号成因→if_else。算子上限 64。拥挤腿 CASH45/CFEV45/PV/TXTUB/XRENT/PTPR。

## 十、账号拉取
count=唯一总数口径；offset 上限 1000；全量 src/pull/pull_unsubmitted.py。Python 统一 bigmodel env（系统 python 无 requests）。

## 十一、工具与坑
- 台账 data/alpha_quality_analysis/SUBMITTED_LEDGER.csv：唯一事实源，只追加，utf-8-sig，id 第 0 列。
- 工具：judge_now / pair_now / screen_pool_corr / find_passers / near_miss / axis_surgery / diverse_pick / smallpool_now / tab / dump_set。
- `sim_run.py`（_autologs/ 下）：通用模拟器，吃 JSON[{cid,code}]，落 data/alpha_quality_analysis/mined/<cid>.json。⚠ 端点 POST /simulations（非 /alphas）；payload `regular` 必须字符串；settings 照抄 `mined/le8T2_t0.05_03.json`；**并发上限 conc=2~3**；单条可 >15 分钟，必须后台跑。
- 后台必须 run_in_background=true（nohup 不保活）；长批次 > log 2>&1；Retry-After 退避 min(ra,15~20)；认证带重试。
- /alphas/{id}/correlations/self 不可用(200 空body)，corr 自己拉 PnL 算；PnL 缓存 pnl/*.json；新模拟延迟数分钟，空判 sleep 重跑。

## 十二、权限与备考
仅 USA；14 数据集 4375 字段（fundamental2=766 未开荒）。顾问通道：10000 分→笔试✓→面试中；Super Alpha 已解锁(OS>100)。备考 28 份 docs/exam、docs/study；缺口"能背≠能讲"。顾问日配额=首 4 常规+1 超级（上限非任务量）；日酬=f(Quality+Quantity, SelfGrowth, Value)，Value 惩罚与已有池相关性⇒质量+低 corr 是杠杆。

## 十三、出量配方（实证入库）
1. 稀释-引擎混合：强引擎(SF4.3+,corr0.74~0.77)×0.40+正交薄腿×0.60，corr 线性 −0.04/0.30 权重。
2. T3000→T1000 换池：SF≥5.5 引擎，SF 留 ~77%、corr 重掷(0.745→0.678)；仅低 TO 基本面有效。
3. group_rank→group_zscore 换形+中性化重掷(0.749→0.660)；母件 SF≥5.5 才垫得住。
4. 低 corr 原料(≤0.66)+0.4~0.6 权重强腿。
5. INDUSTRY→MARKET 中性化 corr −0.044+decay 扰动收口。
6. 基本面动量+应计+MARKET+decay40+T3000：族 corr 最低(0.639~0.673)，天花板 SF 3.96。
7. 原子组合引擎 atom_factory.py：1525 原子→197 强原子，combo 3~4 原子、括号≤30、字段多样性≥2；decay60 对高 TO 族=TO 腰斩+SF 反涨。
8. 组合工厂二层+decay 收口：墙厚料(SF≥4.5,corr≤0.81)两两穷举→外层 group_neutralize(x,bucket(rank(cap),"0,1,0.2"))→decay 40~100 扫→corr<0.685∩SF≥4.2 交点（kqgJYoPg 0.7004→0.6846→平台 0.6776 ACCEPTED）。

## 十四、1007-1010 关键判据
- ★ 存量+流量范式（唯一 SF 过 4.2 结构）：存量腿(f2 科目水平如 other_comprehensive_income_net_tax/assets)×3.0~3.5 + 流量腿(ts_av_diff(cashflow_op/enterprise_value,45))×1.0~1.5；**同质叠加只会稀释**。f_cfo 腿权重=SF↔corr 唯一旋钮（1.5→SF4.46/corr0.6081，已入池 kqgWNYw8）。
- ★★★ SF 与 corr 由同一条腿带来，结构性无法解耦：已验证母件加任何第三腿（换字段/维度/权重/池/decay），SF 上去 corr 必同步上去（5/5 实证，自撞 0.9765~0.9975）⇒ **勿再试给母件加第三腿**。
- ★ 换池 TOP3000→TOP500 是唯一实测能独立降 corr 的杠杆（0.6081→0.4944，tS 1.64→2.03），代价 SF→2.94。
- decay 不重掷 corr（4 次验证，自撞 0.989~0.999）；同骨架变体两两 0.976~0.999 ⇒ 每骨架每日 1 条，出第二条必须**换主腿字段**。
- f2 脚注（cov≥0.7）有效四信号：oci(0.5447 全项目最低)/lease_cur(0.7083)/sbp_nonvst(0.7273)/dbt_issue(0.7524)；税务整族判死；oci 取负、oci 的 ts_delta 判死 ⇒ "水平"才是对的信号形态。
- 组别刀(EX-015)：corr 重掷 ±0.03~0.06；"内外层组互换"(inner_ind)幅度最大(−0.056)；母件 SF<4.5 垫不住。
- D-34 母件设定必须原样继承（wpY3Yxvd 套默认参数 SF 6.19→1.93），批量入库先跑 _BARE 验活，SF 差>15% 即停。
- D-33 战略纠偏：字段笼子（台账仅用 143/4361 字段=3.3%）；存量 idea 库重筛 180 条合格；真瓶颈=组合轴单一+字段族单一，改轴=主要解法。纪律：禁单次 maxcorr 判死 idea、禁叫未提交候选"死料"、每日至少 1 批全新字段。
- 工具：idea.md(原子库+组合登记簿)、combo_gen.py、idea_generator.py(10 类经济机制)。发批前必查 idea.md+atoms.md。
- 外部素材：EXTERNAL_SOURCES.md(EX-NNN 登记)、idea_atoms.md(四类原子+状态机)；论坛镜像 `http://61.182.4.91:8765/wiki/`(408 帖)。未碰可试方向：隔夜/日内拆分⭐(裸信号弱只配配腿)、JACKPOT、GTS、BAB、非线性因子、企业生命周期、盈利不确定性、商誉/过度自信、员工信息分散。
- rel_num_comp(cov0.89)/pv13_h2_sector(cov1.0) 可用但裸因子塌(SF≤2.9)；隔夜/日内拆分 USA T3000 裸信号弱(SF≤2.89)只配配腿。
