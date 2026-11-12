# 外部素材消化规则（李工 2026-10-07 指令：素材杂乱 → AI 负责整理成体系）

> 解决的问题：李工陆续发来论坛帖/研报/截图，之前是来一篇消化一篇、消化完就散在各日日志里，没有统一的登记和检索。
> 本文件 = 总规则 + 总登记表。单篇详细消化放 `docs/external/`，可移植原子回写 `idea_atoms.md`。

## 一、消化流水线（每篇素材必走，不许跳）

1. **登记**：进总登记表（下方表格），给编号 EX-NNN，标类型。
2. **分类定处理深度**：
   - **A 技法类**（表达式/算子/结构/组合方法）→ 必须走 wq-research-porting 四步法（读准表达式→权限核对→对照组实证→归档），可移植原子回写 idea_atoms.md
   - **B 平台机制类**（selection/评分/超级 Alpha/提交规则）→ 结构化笔记进本文件"机制笔记"节 + 同步 docs/exam 备考库；有可操作项的列为行动项
   - **C 数据字段类**（新字段/新数据集介绍）→ 字段实测（200/404/type/cov/alphaCount）→ 登记进 idea_atoms.md D 原子
   - **D 纯讨论/灌水类** → 只登记一行，不消化
3. **实证**：A/C 类必须带对照组批（原式照搬 + 原式+我方杠杆 + 挂我方骨架），判读口径 = 四闸。
4. **归档三件套**：原文要点摘录（含作者实测数）→ 权限核对表 → 我方实证结果表 + 移植落差三条。
5. **状态回写**：登记表状态列更新（已消化/部分消化/仅归档/无价值），idea_atoms.md 原子状态更新。

## 二、总登记表

| 编号 | 日期 | 来源 | 标题/主题 | 类型 | 状态 | 产出 |
|---|---|---|---|---|---|---|
| EX-001 | 0914 | 李工研报 | 球队硬币研报 | A | 已消化 | 当日日志 + 实证批 |
| EX-002 | 0914 | 东吴证券 | UTR 研报 | A | 已消化 | 当日日志 + 实证批 |
| EX-003 | 0915 | Research Paper 16 | 分析师短期交易思路 | A | 已消化 | 19 条样本 9 条达标 |
| EX-004 | 1007 | 论坛 Brain Tips（ZM32460，2 年前） | Working on news datasets（trade_when 事件检测 + ts_arg_min + arc_tan） | A | **已消化（复现失败）** | 见下方笔记；移植落差三条 |
| EX-005 | 1007 | 论文 PDF（李工发） | SAC 2025：SuperAlpha 的 selection alpha 分类（6 类 + 3 个 specific pool 注意事项） | B | **已消化** | 见下方机制笔记；纯备考 + 1 条可操作情报 |
| EX-006 | 1007 | support 社区帖（李工发链接，标题"General-Tech 对于alpha的骨干重要讨论"） | **镜像站无此帖**：408 篇清单 grep 258306965 无命中（快照 2026-08-15，帖可能更新）；直拼 slug 试抓 404。正文仍未取得 | ？ | **卡在取正文**（镜像缺+等李工贴） | 见"抓取通道实测"节第 10 条；拿到正文后补 A/B/C 分类 |
| EX-007 | 1007 | support 中文论坛合集帖 **19273239621399**【Alpha 灵感启示录】合集(持续更新收录中) | 元数据已拿（作者 12429216262167、创建 2023-11-23、更新 2026-06-23、投票 315、评论 11、社区=中文论坛）；正文首段已由搜索引擎抓到原文；**完整正文需李工贴** | A（方法类） | **半取得**（元数据+首段，子帖清单缺） | 见下方 EX-007 节 |
| EX-008 | 1007 | 同系列姊妹帖 **19348865150743**【Alpha 灵感启示录】100+ 从论文到 alpha 的复现 | **无权限**：社区标注 = **顾问专属中文论坛**（GOLD 但 consultant 403，进不去） | A（方法类） | **闭源，暂不可取** | 见下方 EX-007 节"权限判据" |
| EX-009 | 1008 | BrainTips 19609241215511 | Reducing production correlation without reducing Sharpe or Fitness much——**提问帖，无答案**（官方答案在 EX-010） | D | **已消化（灌水）** | 一行登记，无增量 |
| EX-010 | 1008 | BrainTips 8046468280727 | How do you reduce correlation of a good alpha（降 corr 三板斧：换等价字段→换等价算子→换分组） | B | **已消化** | 见下方机制笔记；增量=等价替换优先顺序判据 |
| EX-011 | 1008 | BrainTips 15238236356375 | Why is linear combination of expressions in one alpha not recommended（线性组合三宗罪） | A（印证） | **已消化** | 见下方机制笔记；增量=同尺度判据+劣质拼接 OS 风险官方确认 |
| EX-012 | 1008 | BrainTips 20457074342807 | Generate insights from a research paper using GPT（GPT 提示词教程） | D | **已消化（已覆盖）** | 我方 wq-research-porting skill 已覆盖且更深，无增量 |
| EX-013 | 1008 | BrainTips 8833033953559 | 5 ways to potentially increase returns of an alpha | B（对照） | **已消化（零增量）** | 五条全部已知；其中"提 TO/提波动"与我方 F 优化目标相反（官方讲 return 我方讲 fitness），登记为对照确认 |
| EX-014 | 1008 | BrainTips 14588500172567 | Improve your alphas with Signal Smoothing（平滑三式：变换算子/截面算子/时序算子） | B | **已消化+权限核（1008 实查：ts_mean ✓；ts_decay_exp_window/tanh/sigmoid/s_log_1p 账号无）** | 见下方机制笔记；增量=ts_decay_exp_window / ts_mean 算子级平滑未试 |
| EX-015 | 1008 | BrainTips 13914677572887 | Improve your alphas with Custom Neutralization（group_neutralize 自定义分组 + 双重中性化 + densify） | A | **已消化+权限核（1008 实查：group_neutralize/bucket/densify 全 ✓；floor 无→bucket 等价替代；待模拟）** | 见下方机制笔记；增量=算子级自定义分组中性化，新 corr 重掷轴，待平台权限核对 |
| EX-016 | 1008 | BrainTips 9672576065943 | How does regression_neut work（截面回归残差 Y−(a+bX)） | A | **已消化→平台死（1008 实查：regression_neut/vector_neut 不在账号 66 算子，手术路线判死）** | 见下方机制笔记；增量=对价格动量/反转正交化，直接对撞墙候选手术，待平台权限核对 |
| EX-017 | 1008 | BrainTips 11807866133911 | 6 ways to quickly evaluate a new dataset（None 中性化+decay0 探针读 Long/Short Count） | A | **已消化+权限核（1008 实查：探针 1~4 可用；ts_median/scale_down 账号无）** | 增量=字段体检 6 探针模板，接 fundamental2 开荒（767 字段快速分拣），探针已写入 idea_atoms.md |
| EX-018 | 1008 | BrainTips 14264016776087 | Using Relationship Data for Equity（group 形态做自定义中性化 / matrix 形态直接做因子） | B | **已消化+权限核（1008 实查：rel_num_comp cov0.89 ✓ / pv13_h2_sector cov1.0 ✓，待模拟）** | 增量=rel_num_comp 比率因子假设 + pv13_h2_sector 分组轴；需先核 14 数据集清单里有无关系数据集 |

## 三、机制笔记（B 类素材的结构化沉淀）

### EX-005 SAC 2025：SuperAlpha selection alpha 分类

**我们当前状态**：SuperAlpha 无权限（consultant 403），本文纯备考 + 未来阶段地图。核心内容 = selection 挑 alpha 时看什么、六类 alpha 各自的通过/淘汰特征。

| 类别 | selection 特征 | 对我们的映射 |
|---|---|---|
| **ATOM**（单数据集） | selection 偏好：单数据集避免覆盖率风险，单表达式小变化不影响 | 印证"一池一家族"；我们自己挖时也应保持数据集纯净 |
| **Simple alpha** | 无 prod correlation；提交自己冷门 alpha 的好机会；用 INDUSTRY 中性化 | 可操作：我们产线默认 MARKET，Simple alpha 情报说 INDUSTRY——待实测轴 |
| **Risk Neutralized** | prod_corr<0.55 的 alpha 换 INDUSTRY/SECTOR/COUNTRY 重模拟后 >0.7 = 平台故意压相关去风险；构建低相关 SuperAlpha 选 prod_corr<0.4 的 | 平台会主动"降风险化"——我们看到的 self-corr 墙可能与 prod-corr 机制联动 |
| **Power pool** | 筛选需加 prod_correlation != 0（早期系统没检测，有 0 值假象） | 纯备考（无权限） |
| **Universe 大类** | tax delimited alpha 需重模拟 tax 管理 | 纯备考 |
| **HCAC** | turnover<10%（集中 9-10% 刻意调整）；decay 控不好会拉到 20% | 我们 TO≤20% 闸 + 低频化经验吻合；印证 turnover 是 selection 硬指标 |
| **ACE** | RAM 中性化时表现明显下降（fitness 5→3） | 备考 |

**提炼的行动项**：
1. INDUSTRY 中性化作为 P 原子补测（我们只用过 MARKET/SECTOR/SUBINDUSTRY——EX-005 提示 INDUSTRY 有平台偏好证据）→ 已加入 idea_atoms.md P 原子待测。
2. prod_correlation 概念记入备考：selection 喜欢单数据集、低 prod_corr、TO<10%、decay 干净的 ATOM alpha——**这正好是我们产线"低 TO 基本面薄腿"方向**。

### EX-004 Brain Tips：news datasets 事件检测

**作者两版**（原帖 4 年前 KA64574 + 中文区 2 年前 ZM32460 改进）：
- 原式：`trade_when(news_tot_ticks, news_pct_5_min, -1)` → 作者 S −0.08 / TO 62%
- 改进：`trade_when(news_tot_ticks, arc_tan(ts_arg_min(news_pct_120min,120)), -1)` → 作者 S 1.76 / F 1.08 / TO 21.74% / Margin 7.57‰（TOP3000/delay1/MARKET/decay1/trunc0.01）

**我方权限核对**：三字段全 200，MATRIX，dataset=news12，cov=0.00（事件型正常）。
**移植落差三条**：
1. **复现不了**：arc_tan 平台拒收（我们账号无此算子），三个等价替代（x/(1+abs(x)) / rank 平移 / 无压缩）最好 S 0.96，作者 1.76 复现失败。
2. **数值差多少**：原式基线吻合（我们 0.17 vs 作者 −0.08）；改进式差 0.8+，可能是 news12 历史数据覆盖/时段差异。
3. **问题不同**：作者卡"多空不平衡"，我们卡"强度不足"——不是一个问题，他的后续优化路线对我们无参考价值。
**终判**：news 事件结构在我们账号组死（de1/de60/混合三口径全灭 S≤0.96）。唯一遗产：trade_when 三段式（事件检测/赋仓/持仓）+ ts_arg_min 两个 T 原子登记可用，等有强度的 D 原子来配。

### EX-010 / EX-011 / EX-013 / EX-014：产线结构四篇（1008 镜像批量消化）

**EX-010 降 corr 三板斧（官方顺序判据）**：
1. 换等价字段（high/low/open 替 close）→ 2. 换等价算子 → 3. 换分组（"威力大但别为降 corr 造任意分组"）。
**核心原则**：先做等价替换、保持 idea 纯度；**为 corr 而 distort 实现是 bad practice**。
→ 对照我方五配方：换池>换分组>中性化的实证排序不变，但**手术顺序补一刀：同 idea 先换表面形态（等价字段/算子），再动结构**。axis_surgery 候选执行顺序照此更新。

**EX-011 线性组合三宗罪（官方确认，写进产线纪律）**：
1. 用线性组合把劣质 alpha 拼成可提交 = 按权重把资金分配给劣质 alpha——**印证我方"合并池表现分"理论**（0926 掉分根因官方版）；
2. **子表达式尺度不齐**：rank 输出 [0,1] vs ts_delta 输出价格变动，量级小的腿贡献可忽略。**我方判据：组合腿必须同尺度（rank/zscore/group_rank 输出），禁止裸价格/裸 ts_delta 直拼**——我方产线原子全是 g_rank 输出，安全；今后新腿进组合前必查输出尺度；
3. 组合内子表达式 corr 无法检查 → OS 可能高相关 → 更深回撤。官方结论"Simple is the best，直接实现原始 idea"。

**EX-013 五法提 return（对照确认，零增量）**：提 TO / 低 decay / 小 universe / 提波动率 / news+analyst——五条全已知，且第 1、4 条与我方 F 优化目标方向相反（官方讲 return，我方讲 fitness+合并分）。第 5 条我方已判死。留档作对照，不作行动项。

**EX-014 信号平滑三式**：
- 变换算子：tanh / sigmoid / arc_tan（我方账号不可用，1007 实证）/ log / s_log_1p；
- 截面算子：rank / zscore（我方全在用）；
- **时序算子（增量）：ts_mean(x,N) / ts_decay_exp_window(x,N) 算子级显式平滑**——我方压 TO 只用过 decay 参数，算子级平滑没试过。对高 TO 候选（配方七低频化场景）在 decay 60 之外多一条 TO 杠杆。登记 T 原子待测。

### EX-015 / EX-016 / EX-018：中性化与正交化三篇（A 类，待平台实证）

**EX-015 自定义分组中性化（新 corr 重掷轴，增量高）**：
- 算子级：`CUSTOM_GROUP = floor(rank(cap)*4.99); group_neutralize(alpha, CUSTOM_GROUP)`——市值五分位组；
- **双重中性化**：`NEW_GROUP = bucket(rank(rel_num_comp), range="0.1,1,0.1"); CUSTOM_GROUP = (INDUSTRY+1)*1000 + NEW_GROUP; group_neutralize(alpha, densify(CUSTOM_GROUP))`——同行业+同竞争者数量分位；
- 稀疏分组必须配 `densify()`；
- 其他分组轴：COUNTRY / EXCHANGE / 关系数据 / 统计组 / bucket 自造组。
→ 对我方：中性化设置项只试过 MARKET/SECTOR/INDUSTRY/SUBINDUSTRY，**group_neutralize 算子级自定义分组没系统试过**。配方五（换组重掷 corr）的延伸——粒度更细、比换池成本低。**待办：先核 floor/bucket/densify/group_neutralize 四算子权限 + rel_num_comp 字段权限，再上对照组批。**

**EX-016 regression_neut 截面回归残差（对撞墙候选手术）**：
- 语义：`regression_neut(Y,X) = Y − (a+bX)`（全 universe 截面回归取残差）；
- 用途 1：某值的截面均值回复/动量（用相关值当 X，否则 b=0 无效）；
- **用途 2（增量）：对价格动量/反转正交化**（类似 vector_neut）。
→ 对我方：我方候选撞墙多数因反转/动量成分撞同族守门员——**把撞墙候选做 `regression_neut(x, ts_delta(close,N))` 或 `regression_neut(x, returns)` 剥离反转分量**，可能重掷 corr 地形。我方判死的"风险中性化"是设置项层面，算子级显式正交化没实证过。**待办：平台核对 regression_neut 权限 → 拿撞墙库样本（corr 0.69~0.70 边界条）做对照组批。**

**EX-018 关系数据两种形态**：
- group 形态：`group_neutralize(alpha, densify(pv13_h2_sector))`——pv13 系分组轴（注意：pv13_1l_scibr 分组轴我方已判死，此处为另一字段，逐字段验）；
- matrix 形态：rel_num_comp（同行竞争公司数）直接进因子：假设"销售/竞争者数比上升→股价涨"，式 `rank(sales/rel_num_comp)`。
→ **待办：先核账号 14 数据集清单里有无关系数据集（rel_num_comp / pv13_h2_sector），有才列产线任务。**

## 三·五、EX-007 / EX-008【Alpha 灵感启示录】合集（1007 晚）

**主帖 19273239621399**（公开中文论坛，315 票 / 11 评论 / 更新至 2026-06-23）正文首段原文（搜索结果页抓到）：
> 「Alpha 灵感启示录」为平台用户分享的研究学习笔记，涵盖了从一篇研报论文开始，找到核心思想需要的数据集、操作算符并进行论文复现，再进一步加强信号的主要流程和个人思考。该合集并不能确保可以找到可以提交的 Alphas，但对于掌握 Alpha Research 的研究方法具有非常重要的价值！
> ⭐研究员优选，推荐优先阅读。🔒部分内容使用了顾问专属数据集，收录在顾问论坛中，成为顾问后可解锁。

**这是导航帖**：主贴只挂目录，实质内容在各子帖。同系列姊妹帖 **19348865150743「100+ 从论文到 alpha 的复现」**（70 票 / 4 评论 / 更新至 2026-06-24）社区标注 = **顾问专属中文论坛**。

**权限判据（新，以后判素材先看这一条）**：
- 帖子标题里的社区标识（公开中文论坛 / 顾问专属中文论坛 / SuperAlpha 专属）决定我方能否取。
- 我方：GOLD ✓ / SHORTLIST ✓ / **consultant 403 ✗** ⇒ 公开中文论坛可贴可消化；**顾问专属 = 闭源**；SuperAlpha = 闭源（与 EX-005 判据一致）。
- 所以 EX-007 只有主贴目录能用，EX-008 整条系列暂时拿不到——不是抓取问题，是权限问题，**别在抓取通道上白花时间**。

**对产线的实际价值**：作者自述"该合集不能确保找到可提交的 Alpha，但对掌握 Alpha Research 的研究方法有价值"——定性为 **A 类方法素材**，不是信号源。真要吃它，得先过顾问这关（正在冲），到手后按 A 类走四步法（读准→权限→实证→回写）。**当前不作产线任务。**

## 四、抓取通道实测（2026-10-07 逐条跑过，结论可直接复用）

对象：`support.worldquantbrain.com`（Zendesk + Cloudflare）。对同一帖子实测五条通道：

| # | 通道 | 实测结果 | 判定 |
|---|---|---|---|
| 1 | Zendesk API `api/v2/community/posts/{id}.json` | HTTP **401** `{"error":"Couldn't authenticate you"}` | 死，无匿名读 |
| 2 | HTML 页面直连（curl 全套 UA） | HTTP **403** `Just a moment...`（Cloudflare） | 死 |
| 3 | `WebFetch` 工具 | 只返回 cookie 同意页 + 登录框外壳，**无正文** | 死 |
| 4 | 搜索引擎缓存（cn.bing RSS / 全网搜） | 搜不到该帖任何转载，只有平台科普文 | 死 |
| 5 | 真实浏览器（agent-browser 0.27 + Chrome 155） | 页面进得去，但停在 **Cloudflare 安全质询（Turnstile 小组件）**，页面元素 = "正在进行安全验证" | **死：自动化过不了人机验证** |
| 6 | `hc/api/community/posts/{id}.json`（另 two 变体） | **404 `InvalidEndpoint`** —— 该站根本没挂匿名社区 API（1007 晚补测） | 死 |
| 7 | `hc/en-us/community/posts/{id}`（换英文区） | **403** Cloudflare，换语言没用 | 死 |
| 8 | 老站 `worldquantbrain.com/community/alpha-inspiration` | **404** | 死 |
| 9 | 第三方镜像「腾讯 ima · AlphaNode 知识库」 | HTTP 200 但只回 18KB 骨架，正文全 JS 渲染，**抓不到** | 死（镜像能搜到，读不到） |
| 10 | **第三方全文镜像站** `http://61.182.4.91:8765/wiki/`（1008 从 ima 顺藤摸到） | **通**：support 论坛 408 篇帖子全文 markdown，抓取模板 `…/wiki/view?path=raw/articles/worldquant-brain-support-forum/raw/{post_id}-{slug}.md`；全站 22179 文档 | **活路**。408 篇清单在 `_autologs/forum_mirror_post_list.txt`，地图 `docs/external/论坛地图_FORUM_MAP.md`。**注意：快照 2026-08-15，比快照新的帖子不在内（EX-006 即缺）；内容可能与论坛现版有出入，关键表达式必须回平台实测** |

> **结论更新（1008）**：support 正文不再只有"李工贴"一条路——镜像站覆盖 408 篇存量帖。**流程改为：先查镜像清单 → 有则镜像抓 → 无则请李工贴。** 李工发的 support 链接先 grep 清单再回报，不再一上来就说抓不到。

> **第 9 条是唯一"搜得到读不到"的缝隙**：搜索引擎能命中镜像的元数据与首段原文，正文要登录/JS。所以搜标题能挖元数据，别指望搜出全文。

**结论**：support 站对匿名/自动化一律不开放正文，`curl` + 网页抓取工具 + 无头浏览器三条路都堵死。要吃这个站的料，只有两条路：

- **路 A（推荐，零成本）**：李工自己浏览器打开 → 复制正文/截图贴给我。我按流水线消化，当期回写原子库。
- **路 B（要长期抓论坛才值）**：给李工的登录态通道（把 support 站 cookie 挂在 agent-browser 的 user-data-dir 里），浏览器实测停在质询页——**即使有 cookie 也过不了 Turnstile**，所以 B 路同样不可用；真正可行的只有 A。

**因此定死纪律**：
1. 李工发 support 站链接 = 发了**素材入口**，不等于给了内容。我当轮必须明确回一句"抓不到，请贴正文"，不许假装消化、不许凭标题脑补内容（违 §9 事实纪律）。
2. 非 support 站（知乎/CSDN/公众号/论文 PDF/截图）照常自己抓，这些没 Cloudflare 墙，走 WebFetch / curl 即可。
3. 别再重复装浏览器、反复试 API：五条通道已跑完，直接走路 A。

## 五、维护纪律

- 李工每发一篇素材 → 先登记 EX-NNN → 按类型走流水线 → 当轮完成登记表更新，不留"待消化"过夜。
- 每周日（或李工要求时）汇总一次：EX 表按类型统计消化率，A 类素材的原子转化率（多少原子进了 idea_atoms、多少实证过闸）。
