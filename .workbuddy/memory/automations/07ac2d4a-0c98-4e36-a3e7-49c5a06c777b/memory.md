# 07ac2d4a 自动任务执行记录

## 2026-09-19 00:34~01:30 北京 —— ★ 日内轴破墙：w200_05 过墙入池，两日 0 提交后首破
- **提交 1 条：3qXd5vg0（w200_05）**——本地 corr 0.6765、平台 selfCorr 0.6842 直通，SF 4.74 / tS 3.00，美东 09-18 计 1/5。台账 86，欠账 9，Super Alpha 差 14。
- **配方（可复用）**：新几何主腿（日内反转 `-ts_rank(close/open-1,20)` 1.5 权）+ 2×fnd6 独有锚 0.75 + 零标准 PV 腿 + 引擎 0.5 可选，共享占比 ≤0.14。生成器 `src/mine/mine_w200_intraday.py`（含拉取失败报警）。
- **★ 偏移标定定律**：pred→real 偏移随共享腿权重占比缩放——shared=0.14 → +0.07~+0.11；shared=0 → −0.03~+0.05。低共享区 pred 可信，**搜索可加 pred≤0.66 硬过滤**。
- **日内轴一口实证**：P_int10/40/60 窗口变体组合 SF 2.7~3.5 全 <4.0（质量死）；P_int20 高 S 变体 pred 撞 3qXd5vg0 0.78+（相关死）；隔夜族 standalone 负 S；条件门控腿（波动率/跳空）S ≤1.03 带 FAIL。轴内再无可吃口。
- md 乱码根因：写入用了 U+2212 负号变 `?`，以后一律 ASCII `-`。详见 `.workbuddy/memory/2026-09-19.md`。

## 2026-09-18 23:38~24:00 北京 —— 李工批评盲区后自查：四个硬伤坐实 + 剩余杠杆定位
- **w159 补判决（batch159 industry 分组，7 条从未判决的达标候选）**：0/7，corr 0.84~0.996（3 条撞自家兄弟 O0N0R5NY，最好 w159_00 撞 9qjqm3Q9 到 0.879）→ 换分组救不了共享权重主导的组合。
- **pred→real 偏移 regime 已漂移**：15 观测 mean +0.29（旧标定 +0.12），corr(delta,pred)=−0.69 → pred 越低偏移越大，压阈值方向是反的；pred 0.49~0.55 区间 real 呈负斜率，预测器在当前池子 regime 下失效。脚本 `_autologs/analyze_pred_real.py`。
- **根因**：共享腿（引擎+PV）权重占比 ≥35% → real corr 0.8+（w197_00 vs LLNL3qqm 共享 38%，PV 腿 wp=2.0）；模拟器重整化把组合向共享主导分量集中。
- **leg_lab 静默丢池成员 bug**：rY07MXgd PnL 从未缓存成功，搜索时被静默排除，而 w196_11 实测最高 corr 撞的正是它（拉取失败需报警，红线"只追加"未改原脚本）。
- **剩余真实杠杆（无需新权限）**：池子 86 条无一以日内/隔夜几何为主腿（gJbkQ31Q 日内腿仅 14% 权重）→ 下轮探针 = 追加式驱动脚本生成「日内腿 1.5~2.0 权主导 + 引擎/PV 0.5~0.75」组合批。详见 `.workbuddy/memory/2026-09-18.md` 23:38 节。
- 当日总判决 40 条（33+7），质量达标 24，过线 0；提交 0，台账 84，欠账 5。

## 2026-09-18 16:00~20:30 北京 —— leg_lab 全锚收官，0 提交
- **本轮提交 0**：w196（最后 7 个 M 锚，19 组合→8 达标）/ x196（中性化转换 2 达标）/ w197+w198（strict 0.50 搜索 7 组合→7 达标）合计 **30 判决 17 质量达标 0 过墙**，最低 real corr 0.7219。
- **leg_lab 离线拼装轴正式关闭**：12 锚双阈值（0.55/0.50）扫毕；pred→real 偏移 +0.05~+0.39 不可控；撞点全为 0917 自家入池赢家（pwRwWoJ3/LLNL3qqm/vRjG1Jzw 等）。详见 `.workbuddy/memory/2026-09-18.md`。
- 台账 84 唯一；美东 09-18 = 0/5；欠账 5；Super Alpha 差 16。git 快照已推（502 重试 1 次成功）。
- 会话中断根因：Bash 工具 PATH 损坏（exit 127 静默失败）+ 宿主挂起无回传；全程 PowerShell + 落文件读取绕过。
- **唯一解锁 = 平台侧新权限（多区域/新数据集），待李工操作；本地自动化继续空转无意义，除非池子或数据面有变化。**


## 2026-09-14 23:10 - 09-15 00:55 北京 —— 平台故障封路，转为积压待发
- **本次无新提交**：自相关服务自 23:47 起持续停摆（复测至 00:50 仍 DOWN），提交通道完全堵死。0914 终态仍为 **4/9**（w101_f / w108_e / w116_d / w116_e），台账 61 行 / 60 有效。
- **故障判定三重复验**：①corr 端点对所有 alpha（含已提交）返回 200+Retry-After+空 body ②盲提交 POST 201 后平台自身检查永不裁决（FINAL=UNSUBMITTED）③平台页面存在 "WorldQuant BRAIN is experiencing some difficulties" 故障提示（搜索佐证）。**属平台侧服务不可用，非队列拥塞、非本账号问题**。
- **本地循环不可长期依赖**：`auto_submit_loop.py` 跑满 7 轮后被 shell 会话生命周期掐断（约 1 小时上限）→ 已改为**已提交 alpha 作探针**（akLmmvPW/kqVp6wnO/npKGgKLw，比未提交的新仿真可靠）+ 落日志 `alpha_quality_analysis/auto_submit_loop.log`，并重启。**durable 通道是每小时定时任务 a9b2c5cd（ACTIVE，有效期至 09-15 12:00）**。
- **积压清点：52 个达标待提交**（w112=5 / w114=13 / w115=5 / w116=10 / w118=10 / w119=9），桶变量互不相同（CAPR/SALE/L60/V60b/INVB/SGAB/CASHB/VOLR/CAPXB/CFOB/EBEV/TVOLB/CURB/CVB/SKEWB…），恢复后按序交即可。口径：S+F≥4.0 且 testS≥1.25 且无 LOW_SHARPE FAIL 且台账未收录。
- **遗留注意**：w118_l/m 等 D0 版仍撞 `fnd6_newqv1300_*` 不可用（D0 铁律第 N 次复验）。

## 2026-09-14 21:46-23:10 北京 冲刺"当日补足7个"（batch114-118）—— 半程
- **⭐ 找到今天第二个可复制的过墙配方：无 vol 尾 + 冷门锚 + 换新桶**。`group_rank(锚, bucket(...)) ×3 + group_rank(cash45/EV45/PV2)`（三腿无 vol）。已落地 2 个：
  - **w116_d / kqVp6wnO**（S2.51 F1.91 SF4.42 testS1.87，corr 0.6973 直通，**CAPR 市值时序分位桶** + [TSTKC,CICURR,INTC]）
  - **w116_e / akLmmvPW**（S2.48 F1.63 SF4.11 testS1.93，corr 0.6952 直通，**SALE 资产周转桶** + [XOPTQ,GLCE,TSTKC]）
- 依据链：w106_d 砍 vol 腿 corr 0.825→0.759；w108_e（3锚+无vol+CB）0.6956 过墙 → 推得"无 vol 尾"是降 corr 主杠杆，且**换从未用过的桶变量**即可连续复制。
- **本日已落地 4 个（0914=4/9）**：w101_f(02:01) / w108_e(07:37) / w116_d(10:27 美东) / w116_e(10:49 美东)。台账 61 行 / 60 有效。
- **证伪（本轮）**：①batch114 七条新轴（换桶/换分组 sector-industry/锚时序化/量价相关/D0）**带 4 腿引擎全灭 0.73-0.84** → 换轴不够，必须砍 vol ②batch115 中性化 MARKET/NONE/SECTOR、高锚比(4-5锚)、长窗口引擎：质量多数不达标，达标者 corr 仍 0.74-0.82 ③5 锚表达式超算子上限（66>64）报错。
- **坑**：corr 预检队列在连续提交后拥塞极重，批量预检会大批 TIMEOUT（需分批、隔几分钟重跑）；提交接口假死锁必须靠 GET /alphas/{id} 核 ACTIVE（submit_v2.py 已内置每 4 轮核一次）。
- **新脚本**：mine_batch114/115/116/117/118.py、submit_v2.py（通用串行提交器，修正豁免线=1.10×max(对手S|corr≥0.7)）。
- 待办：batch118（新桶变量：长窗口流动性/波动率、杠杆、存货、费用率、现金、成交量时序分位、动量）在跑；w116 剩余 7 个因队列拥塞 TIMEOUT 待重检；batch117（引擎腿替换）尚未跑。
- **⚠️ 平台故障（23:47 北京起）**：自相关计算服务全局停摆——`GET /alphas/{id}/correlations/self` 对所有 alpha（含已提交的）持续返回 `200 + Retry-After:1.0 + 空 body`；**盲提交同样卡死**（POST /submit 返回 201，但平台自身检查永不裁决，FINAL=UNSUBMITTED）。非队列排队，是服务不可用。已建 `auto_submit_loop.py`（每 10 分钟探测，恢复后自动按 w112_/w114_/w115_/w116_/w118_/w119_ 前缀逐个预检+提交+写台账）。
- **候选池待提交（服务恢复后按序交）**：batch114（13达标全封 corr 0.73-0.84）·batch115（5达标封 0.74-0.82）·batch116（剩 9 个未检）·batch118（10达标新桶：L60/V60b/INVB/SGAB/CASHB/VOLR/CB/LB/CAPR/DEBTB-D0）·batch119（10达标二批桶：CAPXB/CFOB/EBEV/TVOLB/CURB/CVB/SKEWB/LB×2）。注意 w118_l/m 等 D0 版撞 fnd6_newqv1300_* 不可用。
- **D0 铁律复验**：`fnd6_newqv1300_*` 在 delay=0 报 unknown variable（本轮再证）；D0 只能用 fnd6_tstkc/lifr/intc/tfvce/cicurr 等非 v1300 字段。

## 2026-09-14 16:00-20:35 北京 定时任务续跑（batch104-113）+ UTR研报归档 —— 终账
- **今日（美东 0914）落地 2 个 / 目标 9**：w101_f（0mR2K6lr，凌晨 02:01） + **w108_e（npKGgKLw，S2.42 F1.70 SF4.12 testS1.8，corr 0.6956 直通，07:37）**。**欠账余额 7**，明日目标 = 5 + 7 = 12。台账 59 行 / 58 个有效提交；累计 58/100。
- **⭐ 今日唯一突破：市值分桶分组**。`group_rank(x, bucket(rank(cap), range="0.1,1,0.1"))` 替 subindustry：同骨架 corr 0.825 → 0.6956。**必须与新锚同时用**——batch110（只换分组不换锚）corr 仍 0.85-0.91。同族一次即饱和：w108_e 入池后 batch109 的 7 个 cap 桶族候选（SF4.11-4.50）corr 全 0.84-0.94。
- **corr 下限今日从 0.81 压到 0.70**（batch112：fnd6 冷门科目锚 TSTKC/LIFR/INTC/TFVCE/CICURR + 分桶）。最低 w112_g 对最热 w101_f 仅 0.6447，但对 w77_a/w64_h 仍 0.70-0.78 → 豁免线 3.575 够不着。
- **本日完证伪清单（明日勿再试）**：①SLOW_AND_FAST 中性化 400 ②隔夜距离/条件切换/换手距离 solo（SF≤1.15）③纯多锚无引擎（SF≤1.25）④UTR 条件腿 solo（SF1.71）⑤**砍 PV+vol 腿只留 cash45+cfoev45 → 质量与 testS 双崩（testS 0.22-0.75）**——四腿引擎一个都不能少 ⑥analyst4 估值族（EBIT/EBITDA/CFO/FCF/totassets）互为同轴，换锚不换轴无效（corr 0.81-0.86）⑦anl4 字段与 fnd6_epspi/opeps/aol2/newa1_capx 在 D0 或全 delay 不可用。
- 提交判定教训（重要）：POST /submit 返回 201 后 /submit 轮询接口可长期返回 status=None，但 alpha 可能已 ACTIVE——**必须 GET /alphas/{id} 核 status/stage**。w95_a、0mR2VNQ8 仍卡 UNSUBMITTED+PENDING。
- 产出：`BRAIN_东吴证券_优加换手率UTR因子_20260914.md`（研报归档+平台可用性核对+移植点）；`mine_batch104-113.py`；`submit_batch104.py`（通用串行提交器，注意其豁免线判定取的是 max-corr 对手而非全场最高 S 对手，偏宽松）。
- 明日方向：分桶分组（cap/vol/liq）× 冷门科目锚 的组合矩阵继续扫；找 S≥2.7 且全场 corr<0.7 的组合（当前最近：w112_g S2.51 corr_max 0.7795）。

## 2026-09-14 16:00-20:15 北京 定时任务续跑（batch104-110）+ UTR研报归档
- **今日落地 1 个：w108_e / npKGgKLw（S2.42 F1.70 SF4.12 testS1.8 T0.2025，corr 0.6956 直通）**，dateSubmitted 2026-09-14T07:37:32-04:00。**美东 0914 = 2/9**（w101_f + w108_e），台账 59 行。
- **⭐ 今日最大突破：市值分桶分组 = 新的结构级破墙杠杆**。`group_rank(x, bucket(rank(cap), range="0.1,1,0.1"))` 替代 subindustry：同骨架 corr 0.825→0.6956（w108_a 0.7102 / w108_e 0.6956）。w108_e 是首个靠它过墙的因子。
- **但同族即刻饱和**：w108_e 入池后 batch109（7 个 cap 桶族达标候选 SF4.11-4.50）corr 全部 0.84-0.94 vs npKGgKLw 自己 → 全灭。**一个配方只能吃一口**（第 N 次实证）。
- **batch104-108 证伪清单**：①SLOW_AND_FAST 中性化 400 不可用 ②隔夜距离/条件切换/换手距离 solo 质量崩（SF≤1.15）③纯锚无引擎质量崩（SF≤1.25）→ **引擎腿=质量来源不可省** ④UTR 条件腿（if_else 版）solo 崩（SF1.71）⑤anl4_fs_detail_* 字段**仅 D1 可用**（D0 报 unknown variable）⑥fnd6_newq_xoptdqp/pncdq 仅 D1。
- **可用算子核对**：bucket/group_neutralize/if_else/add/ts_rank 可用；**nan_mask/left_tail/right_tail/humo 不可用**（研报的右尾剔除需另找替代）。
- 提交卡单复发：w95_a、0mR2VNQ8 均 POST 201 后 SELF_CORRELATION 永久 PENDING（提交接口返回 status=None），但 w108_e 同样表现却实际落地了——**结论：卡单≠失败，事后必须 GET /alphas/{id} 核 status==ACTIVE，别只看提交接口**。
- 研报归档：`BRAIN_东吴证券_优加换手率UTR因子_20260914.md`（含平台可用性核对表 + 移植点）。新脚本：mine_batch104-110.py、submit_batch104.py。
- batch110 收尾中：波动率分桶 / 美元成交额分桶分组（换分组维度本身）。

## 2026-09-14 16:00-16:35 北京 定时任务（batch104/105）
- w95_a 复查：仍 UNSUBMITTED + SELF_CORRELATION PENDING（死锁未解）。w101_f(S3.45) 入池后同族豁免线 3.795，w95_a S3.45 数学封死，放弃。
- 今日目标 9（5+欠4），已交 1（w101_f），差 8。
- **batch104 全灭（12 候选）**：SLOW_AND_FAST 中性化 400 不可用（保命杠杆死）；隔夜距离/条件符号切换/换手距离三种新结构 solo SF 0.11-1.15，加 0.5 引擎尾仍 ≤1.15——新结构信号太弱扛不起质量，证伪。
- **batch105 首跑 12 个全报错**：①group_rank 手写漏了第二参数（GS 宏没用上）②字段 ID 照截断打印写了假名（capex 真名 anl4_fs_detail_estimates_advanced_af_nd_capex_median）③fnd6_newq_xoptdqp/pncdq 在 D0 不可用（搜索 delay=0 返回 0 条）。已修正重跑中。
- 提交脚本 submit_batch104.py 已备好（串行+动态corr预检+豁免线+台账追加+断点续跑）。
- **batch105 修正版**：w77式（双新锚+全引擎）出 3 个达标——w105_k/vRkX7z83（XINT+TOTAS，SF4.86 S2.94 tS2.45）、w105_i/xAYp7Ojn（TOTAS-CAPEX，SF4.84 S2.87 tS2.57）、w105_j/KPOMAjvz（CFFH+TOTGW，SF4.13 S2.50 tS2.48）。w85式（无引擎双锚+0.5PV尾）再次证伪（SF≤3.69）。
- **corr 预检全封死**：w105_i 0.825、w105_j 0.8115、w105_k 0.890（对手 w64_h/w77_a）——共享质量引擎 4/6 腿即 0.81+，batch74 教训复现。今日 0 新提交。
- batch106 收尾中：对 w105_i/k 骨架近失扰动（换引擎窗口/PV腿/分组），目标压 corr<0.7。
- 新锚字段备忘（未消耗）：totassets_mean(ac2,cov0.70)、capex_median(ac6)、cff_high/mean(ac4-5)、totgw_mean(ac1)、rd_exp_median(ac3,cov0.37)、fnd6_xintopt(ac74)/tfvce(ac89)（fnd6_newq_xoptdqp/pncdq 仅 D1）。

## 2026-09-14 15:25-16:00 球队硬币研报借鉴 + 提交复盘（李工发起）
- 台账复核 57 个有效提交；面板 Rank 357 / IS Score 7.064 / Uniqueness 0.52。
- **CHN 无权限实测复验**（pv1 count=0）——球队硬币因子不可直接复现。
- 经验文档：`alpha_quality_analysis/LESSONS_20260914_球队硬币与挖矿复盘.md`。**batch104 方向**：USA 骨架加隔夜距离腿/条件符号切换腿（`波动率<市场均值?-收益:收益`，算子全可用）/换手距离，替换最拥挤的 -ts_delta(close,10) 腿；**Slow+Fast Factors 中性化从未测过**，可用则判死池 S3.45+ 候选换它重模拟。
- 提交纪律不变：串行、一次一个等 ACTIVE 再提下一个。

## 2026-09-14 12:13-14:35 北京 中午续跑摘要
- **新提交 1 个：w101_f / 0mR2K6lr（D0，S3.45 F2.13 testS3.62）**——w92_d 骨架 + news_short_interest（空头兴趣）腿，豁免通道压线过（S≥1.10×3.13=3.443）。dateSubmitted=2026-09-14T02:01:50-04:00。**台账 57，美东 0914 = 1/9**。
- **w95_a/w96_a/w96_b/w101_e 四个提交流程死锁**：POST 201 受理后 SELF_CORRELATION 卡 PENDING 永不判（w101_f 却秒过）——疑似同用户并发提交互堵。**下次必须串行提交：一次只提一个，等 ACTIVE/FAIL 再提下一个**。
- **w101_f 入池后同族豁免线抬到 3.795**：w96_a/b(3.45)/w101_e(3.51)/w103_g(3.55) 全部被封死。batch96-103 共 8 轮 54 候选实证：骨架天花板 3.55（情绪变化腿 +0.05）、corr 下限 0.81、新族质量上限 3.43——同族空间数学上穷尽。
- 新情报：D0 的 est_*（盈余惊喜）/news12（75 字段日内）/option8（64 字段波动率）/pv13（8 字段客户链）/socialmedia12（6 字段）全可用但纯族扛不起质量；option9/model16/51/MINVOL1M/TOPDIV3000 账号无权限。
- **下轮指引**：①串行提交（提交一个→轮询到 ACTIVE→再提下一个）②找 S≥3.80 的全新骨架（情绪腿+跳空腿+空头腿极限叠加约 3.6，还差 0.2）③或研究平台权限申请（海外区域/被锁数据集）。

## 2026-09-14 09:21-11:40 北京 上午续跑摘要
- **新提交 1 个：w92_d / e79PvPpE（delay=0，S3.13 F2.72 testS2.75）**——buyback+intang+全权引擎搬 D0，**豁免通道过墙**（S≥1.10×2.72=2.992）。美东 0913 累计 3/7，欠账余额 0910 剩 1（今日 0913 目标 7=5+2，已交 3，未交 4 顺延）。
- 关键实证：①自相关池**不分 delay**（w85_a 原式搬 D0 corr 0.9895）②海外区域无数据权限（EUR/ASI/JPN/CHN 字段全 0，换区域路封死）③**D0 质量普遍高于 D1**（纯引擎 S2.74）④anl4 D0 仅 24 字段、STATISTICAL/CROWDING 中性化账号不可用。
- batch89-95 共 7 轮 64 候选：纯新族（guidance/fscore/IVskew/股息率/长反转）单独全灭（SF≤2.8）；INDUSTRY 中性化保质量但 corr 转向 w68_b（0.83）；**decay 阶梯 d4→d2→d1 S 3.13→3.28→3.45**。
- **w95_a（E5vM2QN1，d1，S3.45）压线豁免（阈值 3.443），POST 201 受理，SELF_CORRELATION PENDING 40+ 分钟未出**，其余 7 项全 PASS。落地后同族豁免线抬到 3.795。
- **美东 0913 终账：3/7（w77_a / w85_a / w92_d），欠 4 个顺延；ET 0914 目标 = 5 + 4 = 9（w95_a 若落地可抵 1 → 8）**。台账 56 个。
- 下一轮指引：先查 w95_a 终态（GET /alphas/E5vM2QN1，PENDING 则继续等；落地写台账）；D0 战场 S-maximization（w92_d 骨架 + fnd2 新锚加腿/decay 变体）或全新族解决质量；fnd2 的 766 字段 D0 全可用。

## 2026-09-13 16:00-22:20 北京 全天执行摘要（含晚间续跑）
- 当日目标 = 5 + 0910 欠账 2 = 7；**实际提交 2/7**：
  1. w77_a / E5vx6NJP（S2.45 F1.85，corr 0.6598，双 analyst4 锚 CFI+SGA + cash45+cfoev45+PVD10+vol120，subind d4）dateSubmitted 04:54 美东
  2. w85_a / 6Xr2eQaJ（S2.27 F1.94，corr 0.6803，fnd2 回购授权 buyback - 无形资产 intangible 全权 + 0.5×PV尾部，subind d4）dateSubmitted 09:48 美东
- 欠账余额：0910 欠 2 → 已补 1，**剩欠 1；明日目标 = 5 + 1 = 6**。
- 累计提交 55 个（美东 0913 计 2 个）。

## 全天战术轨迹（15 轮挖矿 batch74-88，~130 候选，~45 过质量线，2 过墙）
1. 存量池 20 结构代表全灭（0.73-0.99）
2. batch74 单锚嫁接：共享 4/5 腿全灭 → 证明必须双独有锚
3. batch75 fnd6 新腿当主腿：质量全灭
4. batch76 换 PV 腿（PVD10/VOL120）：质量达标 corr 0.73-0.85
5. batch77 近失扰动：**w77_a 过墙（0.6598）**
6. batch78/79 复制配方：被 w77_a 顶死（0.82-0.95）
7. batch80 analyst4 离散度：corr 0.91 撞墙
8. batch81 纯基本面/新 PV：质量崩（SF≤3.45）
9. batch82 算子包裹（quantile/bucket/normalize/market/TOP2000）：质量或 corr 全灭
10. batch83 fnd2 回购锚：w83_b corr 0.754（差 0.05）→
11. batch84-85 系数加权：**w85_a 过墙（0.6803）**，0.5 权重是甜点
12. batch86-88 配方复制/新字段：全被 w85_a 自己顶死或质量不足

## 明日续跑指引
- 目标 6 个；判死缓存 alpha_quality_analysis/.corr_block_cache_0913.txt 可删可留（脚本自动去重）。
- 两个已实证过墙配方骨架：①双 analyst4 独有锚 + 换 PV 腿 ②fnd2 独有锚对 + 0.5×PV 尾部——但各自家族已消耗，需换新锚对/新字段。
- 未开发：pv13/model51 数据集真实 ID 待查（直查 404）；fnd2 还有 ~560 字段未翻（多为 cov<0.45 冷门会计科目）。
- 平台 corr 队列积压 40+ 分钟常态，批量预检留足时间窗。
