# AGENTS.md — WorldQuant BRAIN 研究顾问阶段工作规范

> 2026-11-14 重写。旧规则全部作废。本文件只保留当前阶段（研究顾问）可执行的红线与流程。

## 0. 阶段定位

研究顾问阶段。每日配额（按美东日期）：**4 条常规 REGULAR + 1 条超级 SUPER**。目标每天满额入池。

## 1. 最高规则：ATOM 单数据集（违反 = 追责）

- **REGULAR 提交必须是单数据集 ATOM**：整个表达式只允许出现一个数据集的字段。
  `country / exchange / market / sector / industry / subindustry` 这类分组字段豁免。
- **提交前必须过 `src.core.atom.judge()`，返回 False 一律不得 POST。无例外、无特赦、不先斩后奏。**
- 字段归属以平台 `/data-fields` 返回的官方 `dataset.id` 为准；归属不明的先查 API 再判，禁止猜。
- 已知易混点（GLB）：`tm_*` 全族 = `techindi_model`，`tcm_*` 全族 = `tech_chart_model`。**跨用即破坏 ATOM**。
  只能选其中一个数据集做主字段。
- **SUPER Alpha 是已提交 Alpha 的组合，不受 ATOM 约束。**

## 2. 提交质量门（本地预筛 = 平台硬线，POST 403 判决书为唯一判据）

提交质量门直接采用平台硬线，**不再自设更严的本地阈值**（旧四闸 / 三门作废，与 §0 重写口径一致）。

- **目的**：本地先模拟计算，本地过不了 → 平台模拟也过不了；用本地预筛拦截，省平台提交配额。
- **前提（必须验证，不能想当然）**：本地计算准确 ≠ 默认成立，必须先与**服务器模拟真值**比对验证，确认一致后才信任本地预筛。做法：用 `plat_sweep.py` 拉平台 SELF/PROD 真值、或 `GET /alphas/{id}/check` 取平台 SELF，与本地产出逐项比对；偏差超容差即停手，先修本地口径再继续。本地口径若失真，预筛等于没筛——会放行平台必杀的件，或误杀平台能过的件。

- 常规：S≥1.58 / F≥1.0 / 2Y≥1.58 / TO≤70% / SUB_UNIVERSE / LADDER≥2.02 / SELF≤0.70 / PROD≤0.70。
- GLB 附加：AMER / EMEA / APAC 各 ≥1.0。
- CHN：S≥2.07 + LOW_ROBUST_UNIVERSE_SHARPE（0.4×S）。
- **高 S 特赦（平台实测）**：S 显著高于全部 corr>0.7 对手 10% 时 PROD 可宽限。
  实证：KPgepR9k S7.54 / PROD0.788 PASS；超级 P05eKkr7 S3.63 / PROD0.7117 PASS。
- 判据链只有一条：`POST /alphas/{id}/submit` → 轮询 `GET /submit`，403 body 里的 checks 是唯一真值。
  GET /check 空 body ≠ PASS；落盘快照里 S 不达标标 WARNING，**勿当合格**。

### 2.1 相关性判断（仅平台规则）

- 平台两条相关性硬线：SELF_CORRELATION ≤ 0.70、PRODUCTION_CORRELATION ≤ 0.70（即 §2 的 SELF / PROD）。
- 提交前可用 `GET /alphas/{id}/check` 取平台 SELF_CORRELATION 真值，**不耗提交配额**；首调常空 body，轮询 1~2 轮出值，只有 `result==FAIL` 才算 FAIL（每条恒带 1 个 PENDING 的 SELF_CORRELATION，属正常，非判死）。PROD 无预检，只能在提交时由 403 出值。
- 最终判决以 `POST /submit` 后 403 body 的 checks 为准（见 §2 判据链）。
- **旧规则全部作废**：任何本地自设的相关性阈值或换算系数（本地 corr 换算系数、cmax≤0.65、0.70⇔0.6969、0.65 直通线等）一律不再使用；相关性判死只认平台返回值。

## 3. 提交流程（唯一口径）

1. 模拟 → 落盘零 FAIL → `judge()` 过 ATOM → `POST /submit` → 轮询至 403（判决）或 200+RA=0（受理）。
2. 受理确认以 `GET /alphas/{id}` 的 `status=ACTIVE` + `dateSubmitted` 为准，确认后才算入池。
3. 入池即追加台账 `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv`（utf-8-sig，id 第 0 列，只追加）。
4. SUPER 流程：`POST /simulations`（type=SUPER，selectionLimit 必须整数）→ PATCH 补 combo/selection 描述
   （各 ≥100 字符）→ POST /submit。返回 `SUPER_SUBMISSION=1` 表示已有超级在途，当日超级配额仅 1 条。
5. 并发上限 2~3，429 退避 20~30 秒重发。Python 统一 bigmodel 环境。

## 4. 已验证配方（11-13/14 实战）

- **STATISTICAL 中性化 = PROD 破解器**：同字段在 SUBINDUSTRY/MARKET 下全家 PROD 0.74~0.84 被杀，
  换 STATISTICAL 后 S 7.5+，触发高 S 特赦。
- 超级配方（11-14 实证池 354 条后唯一过线）：type=SUPER / USA TOP3000 / selection=`1-self_correlation` /
  **selectionLimit=10**（limit15 SELF 0.83 被杀）/ **decay=32**（楼梯：d20→PROD 0.7061 / d26→0.7002 /
  d32→PASS，每档 +6 ≈ −0.006）/ combo='1' / componentActivation IS / SUBINDUSTRY / trunc 0.08
  → wpoXaojQ S2.78 F2.32 TO0.04 ACTIVE。
- **★ PROD/SELF 免费预检接口（11-14 实证 4/4 对账 delta=0）**：`GET /alphas/{id}/correlations/prod`
  和 `/correlations/self` 直接可用，未提交 alpha 秒回 `{"schema","records","min","max"}`，**max 值与
  提交 403 判决书数值级一致（VkNK869J 0.7666 / WjlK1b2k 0.8856 / O0WKQGoJ 0.9271 / QP0mXGY5 0.8263 全中）**。
  已提交 alpha 需轮询；未提交秒回。→ 提交前必查：prod.max ≤ 0.69 且 self.max ≤ 0.69 才 POST，零浪费提交。
  来源：开源社区 superalpha 工具（devlg.com/caseinfo/17094）提示，本地实测验证。

## 11-14 晚间新增判据（全部实测）
- **group_rank 翻符号陷阱**：`group_rank(-x,g)` ≠ `-group_rank(x,g)`——rank 输出恒为正均匀分布，
  负号塞进去只是反转排序不是翻符号。正确翻法=负号放 group_rank 整体外面。
- **CHN TOP2000U STATISTICAL 符号不对称（判死）**：`group_rank(ts_delta(returns,5),subindustry)`
  S -7.33/RET -0.37，整体取负后只回 +0.4/RET +0.02（1YW6AoMX，两次复现）。平台侧非线性（疑风险模型
  拟合/集中度截断），"负 S 巨信号"在 CHN STATISTICAL 不可靠，勿再当金矿。
- **八市场权限实测**：USA(TOP3000/TOP1000) GLB(MINVOL1M/TOP3000) EUR(TOP2500/MINVOL1M) ASI(MINVOL1M)
  CHN(TOP2000U/TOP2000) JPN(TOP800) TWN(TOP500) 可用；KOR(TOP200) 探测通过但模拟 400 待修设置。
- **mine_grid.py 框架**：idea 驱动（105 原子溯源 idea_id/机制）+ 8 市场 supervisor 常驻 + 提交器
  （本地门+PROD/SELF 预检）。settings 必须含 pasteurization（用 mined BASE 打底）。KOR 400 待修。
- **开机自启**：start_mining.bat 已入 Windows 启动文件夹（C:\Users\jslij\...\Startup），登录即拉起
  supervisor+双提交器，不依赖 WorkBuddy 会话。
- **每周自检**：每周一 09:00 自动复盘全部已提交 Alpha（成功共性/失败模式/优化措施/VF 提速），
  验证经验回写本文档与 idea.md，报告落 docs/research/weekly_alpha_review_*.md。
- **超级 decay 楼梯压 PROD（11-14 实测，limit=10）**：decay20 → PROD 0.7061 / SELF 0.684；
  decay26 → PROD 0.7002（差 0.0002）；**decay32 → PROD PASS 入池 wpoXaojQ（S2.78/F2.32/TO0.04）**。
  每档 decay+6 压 PROD ≈0.006。池子涨到 354 条后 limit15 旧配方 SELF 0.83 被杀，
  **limit=10 小组件组 + decay32 是当前唯一实测过线配方**。
- decay 加大可压 PROD（12→20：0.73→0.72）；同骨架变体两两 SELF 0.99+，**一池一家族只吃一口**。
- GLB 单字段裸信号弱（S<1），组合强；EUR 单字段 STAT 卡 SUB（SUB 限额随 S 水涨，约 0.52×S）。
- 冷门字段侦察（ac=0 真冷门）单字段多数无信号，选字段优先看 -dateCreated 新数据集。
- **tm 族 GLB 线收口（11-14 实测）**：GLB MINVOL1M STATISTICAL 下 tm_16 单字段 PROD 0.8856、
  tm_15 单字段 0.9271、纯 tm 双腿组合 0.8263，全部 PROD>0.7 被杀；**S 8~9 不触发高 S 特赦**
  （特赦只在 PROD 处于稀疏区时有效，如 KPgepR9k 0.788）。tm/tcm 两族在 GLB 不再投入。
- **超级同配置去重（11-14 实测）**：与已提交超级完全同参数的模拟会返回原 alpha（P05eKkr7 本尊），
  POST submit 报 ALREADY_SUBMITTED FAIL。换任一参数（如 decay 20→24）才生成新件。
- 侦察字段源：GLB 缓存 `all_fields_glb_top3000.json` 结构为 {fid: {ds, cov, created, type}}，
  无 alphaCount；按 created 倒序找新数据集（2026-04: global_seasonal_model 196 字段未开荒 /
  model109 / predictive_starmine / intraday_pv_feats / model31 / macro_equity_signals）。

### 11-14 算子多样化改造（李工批准，当晚落地）

实测病根：台账 353 条常规表达式 group_rank 1926 次（平均每条 5.5 次，几乎条条有）；11-14 八市场
131 条模拟 100% group_rank 骨架；官方 58 算子我们常用仅约 25 个，33 个零使用
（group_scale/ts_scale/ts_quantile/ts_zscore/hump/days_from_last_change/last_diff_value/
ts_decay_linear/normalize/ts_winsorize 等）。

落地三件：
1. `_grid/transforms.py`：7 个变换族（gRank/gZs/gSc/tsZ/tsQ/tsSc/hump）+ wrap()；
   横截面层统一 group_rank/group_zscore/group_scale 承接（裸 zscore/normalize 作主形已证伪，禁用）；
   tsZ/tsQ/tsSc 语义换轴为"自己历史中的位置"，corr 重掷幅度预期最大。
2. `mine_grid.py load_ideas()` 加 `_unwrap_group()`：E 类原子自带 group_rank 壳一律剥壳存内核
  （括号配平找顶层逗号，兼容 bucket 组参数），交给变换族重新包装——否则族被锁死在 5 族。
3. `build_specs()`：每条 idea 产 2 个相邻变换族 spec，cid 格式 `区域_idea_族_中性decay`；
   480 条 specs 已重建（7 族 72~96 条/族，0 重复，0 %s 残留），运行中 supervisor 下一轮自动吃到。
   修复 bug：transforms.py hump 族 lambda 漏 `% a` 产生字面 %s（已修，specs 复检 0 残留）。

权限验证结果（_tfperm_1114.txt，16/18 完成，2026-11-14 USA TOP3000，S/F 低是预期——裸信号验权限不是验质量）：
- ✅ 有权限：group_scale / ts_zscore / ts_scale / ts_quantile / ts_decay_linear / normalize / last_diff_value
  （全部完成模拟，无算子类 HTTP 错；2 条 no_location 是瞬时失败，同算子孪生条目已证可用）。
- ⚠️ hump：权限有，但 hump=0.01 把 TO 压到 0.007 → LOW_TURNOVER FAIL（两条实证）——已移出轮换族，
  待 hump=0.001~0.002 重测后才可回族。
- ❌ days_from_last_change：两条均 CONCENTRATED_WEIGHT——禁入族（纪律维持）。
- 副产判据：tsSc/tsQ 在 E101 动量反转原子上 SF 1.38 为新族最高（>gSc 1.10 >norm 0.79）；
  E102 短反转原子全族强负 S（-1.5~-1.6, tS -2.8）→ 语义保真、符号由原子决定，换形未毁信号。
- specs.json 已按 6 族重建（每族 80 条，0 重复 0 hump 残留），supervisor 自动续吃。
**纪律（维持）：days_from_last_change 禁入族；hump 未重测前禁用；新算子未验证权限不得进配方；
tsSc/tsQ 方向语义变化，SF 与方向人工复核后再进提交池。**
### 11-14 后台进程监控（看门狗落地 + 两个真 bug）

- 真 bug①：`mine_grid.py submitter` 扫描模式 `out_w*.jsonl` 匹配不到八市场区域输出 `out_<REGION>.jsonl`
  → 自 17:47 起空转 2 小时（sub_done.json 都没建出来）。已改 `out_*.jsonl` 并实测生效
  （SKIP-LOCAL 日志已出现 CHN_E302_gSc 等新族 cid）。
- 真 bug②：本机 Win11 **无 wmic**（系统移除）——watchdog 第一版 alive() 用 wmic 探测恒 False，
  首轮把 3 个活进程全误判死、重复拉起（supervisor/psubmit3 双开风险）。已杀重复实例
  （保旧 supervisor 22320 / psubmit3 8768），alive() 改 powershell Get-CimInstance，
  探测异常时保守处理假定活、首轮只观察不拉起。
- 看门狗 `_autologs/_watchdog_1114.py`：60s 一轮，按命令行特征串守 3 进程
  (supervisor / grid_submitter / psubmit3)，缺则拉起，重启事件写 `_watchdog.log`。
  注册 `start_watchdog.bat`（Startup 文件夹，与 start_mining.bat 并存双保险；
  开机时 watchdog 先睡 90s 避竞态）。
- 遗留风险：watchdog 以本会话后台任务方式在跑，WorkBuddy 会话关闭时可能连带被杀——
  开机自启路径已备好；跨会话常驻需用户手动双击 start_watchdog.bat 或等下次开机。
- schtasks 被 WorkBuddy 安全策略封禁；Start-Process 因宿主注入重复 proxy 环境变量
  （https_proxy/HTTPS_PROXY 双键）报字典错误无法用——均记录为环境坑。
## 5. 工具导航

| 用途 | 位置 |
|---|---|
| 台账（唯一事实源） | `data/alpha_quality_analysis/SUBMITTED_LEDGER.csv` |
| ATOM 判定 | `src/core/atom.py`（`judge()` / `dataset_of()`），字段缓存 `data/alpha_quality_analysis/all_fields_*.json` |
| 通用模拟器 | `_autologs/_worker_1113.py`（吃 JSON[{cid,code}]） |
| 403 判决解析 | `_autologs/_show403_1113.py` |
| corr 预测（提交前必跑） | `corr_predict.py`；平台真值 `plat_sweep.py` |
| 凭据 | `brain_credentials.txt` |

### 8 进程架构修正（11-14 晚，李工追问后落实）

- **线程版已废弃**：supervisor 原为"1 进程 8 线程"，与李工"8 市场 8 py 进程"指令不符。
- 现架构：supervisor 只当孵化器（60s 巡检），8 个市场各跑独立 `worker_region <区域>` 子进程，
  死一个 60s 内自动拉起；子进程日志 `_grid/_worker_<区域>.log`。
- 当前进程树：supervisor 1 + 8 worker 子进程 + grid_submitter + psubmit3 + watchdog = 12。
- spec 池已补量：每市场 60→120 条（总 960），KOR/TWN 曾因 spec 耗尽 idle，补料后复工。
## 5.5 研究顾问方法论四原则（李工 2026-11-14 总结，最高优先）

1. **Alpha atom 类型分散多样化**——量价/基本面/分析师/事件/情绪等 atom 类型都要铺，不聚在一类。
2. **数据集分散多样化**——不死磕少数老数据集（实测病根：台账 353 条仅用 143/4361 字段=3.3%），
   每日保持新数据集/新字段开荒。
3. **算子分散多样化**——变换族轮换（_grid/transforms.py 6 族），不再单靠 group_rank。
4. **idea 分散多样化**，来源优先级（李工定）：
   ① 李工提供的 idea 灵感 → ② 论文 → ③ 开源社区 → ④ 互联网搜索。
   **只有①②实在挖不到才轮到③④。李工的灵感与论文不可能挖不到——若挖不到，必先反思
   代码层面哪里有问题（字段/算子/参数/实现），不得反过来判 idea 死刑。遇到困难时刻反思。**
### 全局并发名额防 429（11-14 晚落地，实测有效）

- 机制：`mine_grid.py` 顶部 slot_acquire/slot_release——`_grid/slots/slot{0,1}.lock` 文件锁（O_CREAT|O_EXCL 原子创建），
  8 个 worker 点火前必须抢到 2 个名额之一（留 1 个给手动批次 sim_run），抢不到等 5s 再试；名额持有期=从 POST 到
  拿回完整结果，40 分钟未释放视为死进程遗留可抢；429 重试逻辑保留作兜底。
- 实测（上线 5 分钟）：USA/ASI/CHN/EUR/JPN/Glb 共 21 次 fire 全 201，仅 GLB 1 次 429（切换期）；
  名额轮换正常（USA/GLB 先占，其余排队）。
- **429 语义（李工问）**：429 = POST 被拒、模拟根本没创建，无半成品、无需"重新回测"，重试成本=重发一次 POST；
  旧代码 5 次全败会把 spec 记 FIRE-429 写入输出（被误记账），名额机制上线后该路径基本不会走到。
- 注意：手动跑 sim_run.py 批次时请保持 --conc ≤1，与 8 worker 的 2 名额合计 ≤3（账户并发上限）。
- 遗留问题：KOR/TWN F 系 spec 连发 400（数据集在该区域不可用），每个 400 秒级释放名额不阻塞，
  但烧 spec 池（已各烧 60 条）——待修 KOR TOP200 universe 问题。
### 多样化架构 v2（李工 11-14 深夜定稿，取代旧 build_specs）

- **李工纠正**：①"分散压力大"是伪命题——集中压力才大（小角落交不出 Alpha 才是真压力）；
  ②每日配额口径=**4 条常规 + 1 条超级**（AGENTS.md §1 原文），当日阈值补不了，严禁口头说成"6 条"；
  ③idea 是最重要维度，必须全量覆盖（105 条 idea 每条都进每个市场）。
- **定义（李工）**：多样性维度=市场+idea+算子+universe+decay+中性化；**市场定死**（8 进程各守一市），
  其余 5 维联合多样化。
- **实现**：`build_specs(per_market=150)` 五维组合池 = 6族 × 该市场全部universe × decay{0,15,45,90} × 5中性化，
  每市场独立洗牌种子顺序采样；采样顺序=**先全量覆盖 105 条 idea（每条 1 组合）**，再回头补第二/三组合。
  实测：USA/GLB/EUR/ASI/CHN/JPN 各 150 条、KOR/TWN 各 110 条（单 universe 组合池小），
  idea 覆盖 98~101/105（缺的为 wrap 失败）；总队列 3984 条，NM/ENG 优先、WF 次之、新矩阵殿后。
- 验收指标：每周自检报告"新字段覆盖数/新数据集数/idea 覆盖数"，数字不涨=没分散。
### 踩坑记录制度（李工 11-14 深夜指令）

- **`docs/project/踩坑记录.md` 已建档**：凡是"实测推翻预期"的环境坑/平台坑/流程坑当场入档（坑号/现象/根因/正确做法），
  开工前必读，同类坑禁止二犯。首批入库：E-01~E-05（proxy注入/wmic缺失/名额锁遗留/
  **data-fields 200≠模拟可用★**/400无响应体）、P-01~P-05、F-01~F-02。
- **硬规则：新区域/新 universe 首次使用前必须手动 POST 一条哑模拟验证**，200/201 才准进 spec 生成。
  现状=6 市场（USA/GLB/EUR/ASI/CHN/JPN），KOR/TWN 区域级无权限已摘除，EUR 仅 TOP2500。
## 6. 纪律

- 每轮汇报必含：提交 id+指标 / 台账总数 / 当日美东计数 / 剩余配额。严禁空仓日。
- 一切数值以实测命令输出为准，禁止脑补；不知道直说不知道。
- 每次判墙 / 破门结论当天回写本文件 §4。
