# WorldQuant Brain 项目长期记忆
> 读者="下一个会话的我"。规则全文在项目根 `AGENTS.md`，**冲突以 AGENTS.md 原文为准**。
> 本文件只留判据（标【A:机制】/【B:复验N次】/【单次】；未标=李工定的规则）；实测明细在 daily log `2026-11-*.md`；`_archive_*`、`*.bak_*`、被撤回段不作判据。
> 准入（11-17）：一次观察≠规律；须【A:机制可复验】或【B:≥2次独立验证(跨市场/生成器/日期/代码族)】；同批N样本≠N次独立验证。被证伪的删除并写作废原因。

## 〇 最高条款（凌驾一切）
- **事实条款**（李工11-15 17:01）：任何数字/条数/指标/平台返回必须有出处（本次命令输出/文件原文/API）；无出处写"未核实"，不许给看似合理的数。汇总行从明细逐行数。引用规则先grep原文。说"跑过了"要指出日志与关键行。认错要写进文档并改代码。
- **写前grep**：写进记忆的数字须能在 `SUBMIT_VERDICTS.csv`／`SUBMITTED_LEDGER.csv`／`_autologs/_prodcache_1113.json`／`_autologs/*.txt` grep到原始行；grep不到=自编，删。
- **文件打标**（李工11-18 15:51）：WorkBuddy产生的所有文件带 `_workbuddy` 后缀；不碰共享账本/mined/`alpha_loop/`（另一工具）。清理任何文件前先问李工。

## 〇三 李工纪律七条（11-17批复+11-18修订，全文AGENTS.md §0.5）
1. 11-12前行为都是反例；混血件只当形态参考不可重投。
2. **USA量价(pv1)黑名单，USA优先级最低；EUR/ASI/CHN/GLB/JPN一致（非USA量价单数据集ATOM已放开，11-18李工拍板）**。
3. 真ATOM：单dataset字段+6豁免分组(country/exchange/market/sector/industry/subindustry)；cap/close/returns/volume属pv1；提交前验平台 `classifications` 含 `DATA_USAGE:SINGLE_DATA_SET`。
4. 防反复违规：规则=唯一通道硬门+自检命令+留痕；每次违规当场写violation(时间/规则/后果/修正)。
5. **回测/提交串行**：sim_run `--conc>1` exit5+全局锁；并行挖矿bat已改.disabled_20261117。
6. 研究循环：回测→能交就交；不能交按平台返回错误修表达式/数据集；同一idea深挖——**20轮只是参考非硬门，综合判断，玩不转就换**。
7. idea记账 `IDEA_LOOP_LEDGER.csv` 一轮一行(平台指标/错误/修正动作)；新idea先过经济+交易逻辑二次检查。
- **流程**（李工定）：idea→选数据集→构造→回测→提交，不过回退改表达式/数据集。S/F不过=表达式写错(非idea不行)，改形状不丢想法。

## 一 配额与质量门
- **每日窗口**北京时间14:00。**配额**4常规REGULAR+1超级SUPER(美东日)。"每日6条"作废。汇报固定`常规x/4 + 超级y/1`，入池才算，不欠账不跨日。
- **唯一硬拦门=ATOM**。质量门=平台门：F≥1.0/TO≤70%/无FAIL/SELF≤0.70/PROD≤0.70/S≥1.58/2Y≥1.58。提交前过 `src.core.atom.judge()`(3元组)。
- 【B全量】**选件第一道筛=S≥1.58**：平台把value<limit一律FAIL；`GET /alphas/{id}` 的is.checks不达标只显WARNING，但`POST /submit` 403判FAIL⇒**不能拿GET的result当"可投"**(11-17全部11件质量门拒都栽S=1.0~1.4)。
- 【B全量】被拒不消耗配额⇒可直接POST让平台判。低S=形态/idea层错，非数据层；S与能否进池是两个独立闸门。

## 二 平台机制（与alpha无关，已直证）
- 【A+B≥4】`POST /alphas/{id}/submit` 的**403 body就是判决书**(checks在is.checks)；200/201受理后才轮询`GET .../submit`。被拒不轮询，POST间隔30~70s。
- 【A+B】value<limit一律判拒；`CLUSTER_TEST`例外(低门限仍入池)。判决书只报一个FAIL，未报项PENDING(SELF/PROD PENDING=PASS)。CSV坑：`verdict`空+`failChecks`裸值(如`PROD_CORRELATION=0.7849`)也是被拒，须同时解析 `v.get('checks') or v['is']['checks']` 与裸值，否则漏80%拒因。
- 【A直证】`OLD_SIMULATION`(FAIL,value=null)=模拟过期必拒⇒**只有刚模拟完的件值得投**，小批高频别投存量。
- 【B5组】门限浮动(随信号强度给动态limit)⇒差距读当次GET的limit，不用固定门。`REGULAR_SUBMISSION` limit=4。
- 【A+B2】SELF撞平台他人已提交形态，PROD撞全平台该形态的池⇒我方池0件≠安全。**未提交件corr端点返空body**⇒新件只能靠POST拿判决(例外见§五免费预检)。
- 【事实】平台并发上限3，李工要求≤2；我方OS池364条(USA355/GLB5/EUR4)。isScore/rank无API通道。

### 二·五 判决全量反推（11-17，426+判决/157 ACCEPTED/235+ REJECTED；工具 `_grid/analyze_verdict_families.py`）
1. 【A+B全量】平台REGULAR不查ATOM(check名全集18个，无DATA/USAGE/ATOM类)；157 ACCEPTED全部混数据集⇒混血是历史唯一验证过门形态；但ATOM是我方自设红线(为VF/atom比例)仍必须守。
2. 【A+B全量】SELF豁免2026-11消失(时间边界)：9/10月ACCEPTED有self≥0.70，11月142件全拒零豁免⇒只信当天实测。
3. 【A+B复验9】**质量门=可调参数(decay/中性化/universe/窗口/分组)；corr=结构问题(只能换族)**。
4. 【A+B判决表】同族封死：GLB pv1波动率族4件占满⇒全部变体SELF0.76~0.99全拒；option8 call-put偏斜族QP0E3qwK/ZYar0wd3 SELF0.9873/0.9645、PROD0.8875/0.8873⇒**"池内0次使用"≠"平台上冷"**。
5. 【A机制】处女地策略：判决表反推已投族指纹，库存未投过族2747件平台已判质量达标⇒零模拟成本；但多数OLD_SIMULATION⇒要先重模拟。
6. 【A+B全量】单数据集路线空间极小：全库16765件里"单数据集+无FAIL+F≥1.0"仅35件、全pv1；加处女地+质量达标剩14件。
   - 【157件统计】双过件(真prod≤0.70)结构三铁律：①最外层zscore()；②嵌套双层权重`zscore(A*(B*(核心)+C*(对冲))+D*(第三块))`；③窗口252主导。双过件`O0WEE6zJ`(S2.07/self.6548/prod.683)、`pwaAzrrX`(S1.89/.638/.6991)=我方11-12提交件。

### 二·六 冷≠可用，真墙是PROD（判决426+mined1599+prodcache1113 三源）
- 【A+B】冷池S中位极低(model109 0.36/fundamental23 −0.08)vs主流池(fundamental2 1.79/pv1 1.66)⇒**uc只预测拥挤度不预测信号强度**。prodcache:34条有self≤0.70的23件(68%)；24条有prod≤0.70仅2件(8.3%)⇒**别为压SELF换数据集/市场，要命的是PROD**。
- 【A直证】"高S救PROD"不成立：`6XMVrmbL` S2.46但prod0.7737仍拒⇒高S只在PROD稀疏区有宽限，非通用杠杆(AGENTS.md §2高S特赦与此冲突，取实测)。
- 【A+B】fundamental2内uc<80&cov>0.55字段120个，池内0次使用(可做关系腿)。
- 【A直证】atom.py region串味已修(`judge(expr,region=)`)；EUR/GLB分区域表未拉⇒EUR仍串味(待补)。

## 三 方法论
1. 先理解idea再写表达式；每条候选一句话说清"赌什么"，说不清=噪声不进批。
2. 换设置层(decay/中性化/universe/truncation)=合法微调；换数据集≠微调。
3. 【A】单轴隔离：一次只动一个轴(反例M72/M77同改3轴⇒结论作废)。
4. 【A】只做"表述正确"因子不做字段堆砌；多腿须同机制(option8三腿S0.80 vs双腿S2.20⇒混机制稀释)。
5. 【A】corr的对手是"形态"不是"字段"⇒复现他人已验证件必撞生产池。
6. 【B2跨市场】decay是伤S的悬崖非降换手旋钮⇒降换手靠加长窗口。
7. 【A】换市场是首选：EUR/GLB/ASI/JPN/CHN我方池空⇒SELF天然白送(但须选对市场：短反转只CHN成立)。
8. 【A】本地存量件不可投两硬因：①OLD_SIMULATION②混数据集破ATOM红线(②不是平台会拒)。
9. 【A】投单前GET预筛is.checks(但result的WARNING≠可投，见§一)。
10. 【A+B2】设置层能决定0.76的Sharpe(同式decay10/SUBINDUSTRY→S1.44；decay60/MARKET→S2.20)⇒模拟前先固定设置层。

## 四 市场门限真值
- **GLB**【B6+】AMER/EMEA/APAC各≥1.0，EMEA最紧。入池`0.6*group_scale(-ts_std_dev(returns,120),industry)+1.4*group_scale(-ts_av_diff(returns,60),industry)` d64 STAT。pv1口径已被4件占满⇒该族新变体SELF0.76~0.99全拒。
- **EUR**【B2】卡LOW_SUB_UNIVERSE_SHARPE，STATISTICAL必需。【B3】分组subindustry0.57(lim1.28)/industry0.80(lim1.39)/sector0.64(lim1.01)。【A】SUB limit≈0.52×S(6次复验)，降S救不了SUB。fundamental23 uc极低(cash159/debt_lt122/ebit217/assets1144)。
- **CHN**【B6全灭】卡LOW_ROBUST_UNIVERSE_SHARPE.WITH_RATIO，limit≈0.40×S，硬门S≥2.07。短反转S2.35/2Y2.97/tS3.26但ROBUST v死卡0.51~0.55，5轴无解。
- **ASI**【单次】LOW_INVESTABILITY_CONSTRAINED_SHARPE。**JPN**【未验证】池空pv1齐，GLB配方迁移S仅1.23。**★USA也有LOW_SUB_UNIVERSE_SHARPE门**。
- 【A】SUB/ROBUST value必须靠机制本身(小盘股强信号)抬，不能靠调S/分组/decay。

## 五 SUPER 专项（当前主线）
- **机制**：SUPER=已提交alpha的组合，**不受ATOM约束**(AGENTS.md §49)。selection选组件(须≥10)、selectionHandling/selectionLimit在settings内(type=SUPER,limit须整数)；combo为加权式。组件池按region隔离(OS: USA355/GLB5/EUR4⇒只有USA够)。
- 【A+B3入池】settings startDate=2014-01-01/endDate=2023-12-31/testPeriod=P0Y0M(10年IS阶梯)；旧super_sweep用2019起+P1Y⇒IS_LADDER算不出全废。
- 必须先PATCH：combo.description与selection.description各≥100字符，否则403(COMBO/SELECTION_DESCRIPTION_LENGTH FAIL 0)；必须先PATCH再POST。
- 三态：201=受理(轮询等判决)／403+checks=拒(零配额)／200空body=排队(≠通过≠拒)。
- 【A+B直证33件】裸`1-self_correlation`族11-16两批33件全被SELF/PROD拒(SELF0.7074~0.9969)⇒已在池裸族不可再投。
- 【A+B4档】裸族decay每+6压SELF≈−0.004但抬PROD≈+0.008⇒两门反向，decay单独压不下来⇒**杠杆在selection主题(换组件族=换corr邻居池)**。
- 【免费预检·11-14实证4/4 delta=0】`GET /alphas/{id}/correlations/prod`与`/self`未提交SUPER秒回`{schema,records,min,max}`，max与403判决书数值级一致(VkNK869J0.7666/WjlK1b2k0.8856/O0WKQGoJ0.9271/QP0mXGY5 0.8263)⇒提交前查prod.max≤0.69且self.max≤0.69才POST。⚠`super_fast.py`对该端点曾返self==prod⇒不作真值，以判决账本为准。
- 【★★A+B直证·11-18破局超级1/1】**已入池 Xga8dZjz S2.42/F1.70**：selection=`(1-self_correlation)*in(datasets,"model51")` + **neutralization=STATISTICAL** + decay20/limit10/USA TOP3000/combo=1。三墙同破机理：①STATISTICAL换风险基底⇒SELF从SUBINDUSTRY的0.71降到0.55(躲开我方3件SUBINDUSTRY老SUPER wpoXaojQ/d5almKdJ/P05eKkr7)；②model51=已验证小盘稳健组件族(d5almKdJ同主题SUB_UNIVERSE2.07/1.38)⇒SUB_UNIVERSE过；③PROD随组件族重掷也过。**光STATISTICAL不够**：同法裸1-self_corr(d20/d25)卡SUB_UNIVERSE0.86/0.9+PROD0.78，analyst4主题卡SUB1.13/1.17。⇒降SUPER自相关=STATISTICAL(破SELF)+数据集主题(破PROD/SUB)两件套。
- 【A:机制】SUB_UNIVERSE limit=0.75*sqrt(1000/3000)*主S=**0.433×S**(官方consultant-faqs/how-pass，7件判决复验：S2.07→0.9/S2.7→1.17/S3.63→1.57)；sub分=alpha pasteurize到TOP1000重算PnL。低self_corr冷门组件偏小盘⇒pasteurize后信号塌⇒每件精确差0.04，降S救不了(比值恒定)。⇒组件族必须本身小盘稳健。
- 【A:机制】SELF对手=我方已提交池(老SUPER全SUBINDUSTRY)，PROD对手=全平台同形态；两门反向(AGENTS§114)，decay只破一边。判决一次只报1个FAIL，未报项=PENDING=没轮到检查≠PASS(11-18误读d25的PROD=PENDING为过，d20暴露PROD0.7834才纠正)。
- 【预检坑·11-18】批量模拟20+条后corr接口返回HTTP200空body+Retry-After1.0(osmosis排队)，此时corr=None≠相关低，须重读或改用提交判决书(秒回403带精确corr)。corr在0.7~0.8区间预检max与判决精确一致(d20预检0.7834=判决0.7834)。
- 11-18早批独立通道实测(全REJECTED，已被上条破局覆盖，留作反例)：裸族外主题SUBINDUSTRY下SELF卡0.70~0.87：analyst4 d25 0.7345、option8 d25 0.8669、fund6 d25 0.7041/d31 0.7103、pv1 0.8063。全质量门PASS，挡路=SELF/PROD。⇒换主题必须配合换neutralization，单换主题无效。
- ⚠【11-17自查】旧记忆9个selection主题PROD数值经判决表grep全0命中，来源super_fast.py可疑读数⇒已删不得引用。

## 六 工具与坑
- 台账`data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`(只追加、utf-8-sig、id第0列)；判决同目录`SUBMIT_VERDICTS.csv`。Python一律 `D:/ProgramData/Miniforge3/envs/bigmodel/python.exe`。
- WorkBuddy独立件：`_grid/sim_workbuddy.py`(串行conc=1)、`_grid/super_workbuddy.py`、`_grid/mined_workbuddy/`、`_grid/submit_ids_workbuddy.py`；独立账本`IDEA_LOOP_LEDGER_workbuddy.csv`／`SUBMIT_VERDICTS_workbuddy.csv`／`SUPER_LEDGER_workbuddy.csv`／`SUPER_VERDICTS_workbuddy.csv`。
- ★★`| head -N`用SIGPIPE杀sim_run⇒绝不接提前关闭管道。`nohup &`被回收⇒用run_in_background；stdout块缓冲⇒查落盘文件。Git Bash `ps -ef`查不到python⇒用TaskStop。bash双引号包python -c写中文会被吃⇒写文件再追加。
- `sim_run.py`吃JSON[{cid,code,expression,settings,mech,idea_id,idea}]，落mined/<cid>.json。工具(`_grid/`)：submit_ids_raw.py｜analyze_verdict_families.py｜super_patch_submit.py｜super_check_inflight.py｜sim_run.py｜corr_*｜prescreen_full.py。
- 字段缓存region专属`all_fields_{usa_top3000,eur_top2500,glb_top3000,chn_top2000}.json`⇒合并串味。实测uc:close USA68272/EUR4062/GLB1822。option8入池样板QPK3n9Zw=`1.3*group_rank(iv_call_90/iv_put_90-1,industry)+0.7*group_rank(iv_call_90-iv_call_30,industry)`(S2.20/F2.36,d60/MARKET)。

## 七 Universe/算子边界
- 可用USA(TOP3000/1000/500)、GLB(MINVOL1M/TOP3000)、EUR(TOP2500)、ASI(MINVOL1M)、CHN(TOP2000U)、JPN(TOP1600)。摘除KOR/TWN/EUR MINVOL1M/ASI TOP1500。
- 不可用算子：ts_skewness/kurtosis/co_skewness/regression_neut/vector_neut/floor/tanh/sigmoid/ts_decay_exp_window/ts_median/scale_down/arc_tan；上限64。`?:`易触发CONCENTRATED_WEIGHT⇒用if_else。VECTOR字段须包vec_avg(隐式pv1依赖风险⇒优先MATRIX)。
- 字段逐区不同，缓存仅USA/EUR/GLB/CHN。【11-17】JPN无enterprise_value｜GLB无cashflow_op/ebit、无ai_equity_alpha｜EUR/CHN/JPN的ai_equity_alpha只有accounting_forensics_factor(_2)⇒该集只USA有信号。

## 八 已验证过门样本（事实）
| id | 市场 | S/F | 机制 |
|---|---|---|---|
| O0WEE6zJ | USA混血 | 2.07/1.24 self.6548 prod.683 | zscore外层+嵌套双权重+252窗口 |
| pwaAzrrX | USA混血 | 1.89/1.32 self.638 prod.6991 | 同上(四腿) |
| QPK3n9Zw | USA option8 | 2.20/2.36 | call-put偏斜+期限结构 |
| 1YwKML56 | USA fundamental23 | 2.21/1.75 | group_rank(ts_av_diff(cfop/ev,60),industry) |
| ZY07MXgd | USA fundamental6 | 2.46/2.35 | 三腿cfop/ev+xopr/assets+cash/assets |
| d5al5ljw等4件 | GLB pv1 | 2.50~2.85/1.73~2.01 | 波动+换手双腿(族已占满) |
| P05eKkr7等3件 | SUPER | 2.78~3.63/2.32~3.72 | 低self-corr组件等权合成 |

## 九 待修BUG
B1 atom.py EUR/GLB分区域映射缺失(USA已修)｜B2 diversity的idea维度靠cid前缀凑｜B3 DIMS缺field/skeleton维度｜B4 corr_gate未接提交通道｜B5 /data-fields参数形式已变｜B6 atom.judge()返回3元组｜B7字段映射缓存缺JPN。
