# -*- coding: utf-8 -*-
"""平台规则常量 —— 每一条都带出处，改之前先看证据。

这个文件的目的：把散在 docs/ 和论坛里的结论，变成代码能直接引用的常量。
文档负责讲"为什么"，这里负责讲"是多少"。两边不一致时，以带日期的实测为准。

出处分三类：
  DOC  = 官方文档（docs/learn/，已下载到本地）
  FORUM= 顾问中文论坛（docs/forum/，已下载到本地）
  TEST = 本项目实测（带日期）
"""

# ============================================================
# 一、ATOM（单一数据集 Alpha）
# ============================================================
# 定义: 整个表达式只使用同一个数据集中的字段；分组字段豁免。
# 出处: FORUM 44941181410455《BRAIN Tips 001｜Power Pool + ATOM》
#       官方 Theme #2: ATOM
ATOM_EXEMPT_GROUP_FIELDS = (
    'country', 'exchange', 'market', 'sector', 'industry', 'subindustry',
)

# 隐式破坏 ATOM 身份的常见写法（帖子原文列的三个坑）
# 坑 1: convert() / inst_pnl() —— 底层自动调用 pv1 价格/汇率
# 坑 2: 用 cap / close / returns / vwap 做 bucket() 分组 —— 它们属于 pv1
# 坑 3: vector_neut(x, cap) / vector_neut(x, returns) —— 引入 pv1 字段
ATOM_FORBIDDEN_OPERATORS = ('convert', 'inst_pnl')
ATOM_FORBIDDEN_FIELDS = ('cap', 'close', 'returns', 'vwap', 'open', 'high', 'low', 'volume')

# ============================================================
# 二、Pyramid 倍率（Quality Factor 的核心组成）
# ============================================================
# 铁律 1: 混用多个数据集时，Pyramid 倍率按「最低的那个」结算（木桶短板）。
#         1.8x 稀缺数据集 + 1.0x pv1 = 按 1.0x 结算，稀缺红利归零。
# 铁律 2: 表达式里混入 3 个及以上不同 Dataset Category 的字段，
#         Genius 金字塔评定直接计 0 个 Pyramid（不计入任何金字塔）。
# 出处: FORUM 44941181410455；配套 FORUM 44770798147735
PYRAMID_WEAKEST_LINK = True
PYRAMID_ZERO_THRESHOLD_DATASETS = 3

# ============================================================
# 三、平台提交硬门（9 项，全过才算「能交」）
# ============================================================
# 出处: DOC consultant-information/consultant-submission-tests
PLATFORM_GATES = {
    'LOW_FITNESS': 1.0,           # Fitness > 1.0
    'LOW_SHARPE': 1.58,           # Sharpe > 1.58
    'LOW_TURNOVER': 0.01,         # Turnover >= 1%
    'HIGH_TURNOVER': 0.70,        # Turnover <= 70%
    'CONCENTRATED_WEIGHT': 0.10,  # 单股权重 < 10%
    'LOW_SUB_UNIVERSE_SHARPE': None,   # 子universe夏普，平台算，无固定阈值
    'LOW_2Y_SHARPE': 1.58,        # 近两年夏普，与 LOW_SHARPE 同线
                                  # 实测 2026-11-13: f6_12 全期 S=1.90 但 2Y=1.56 ⇒ FAIL
    'SELF_CORRELATION': 0.70,     # 与自己已交的 alpha
    'PROD_CORRELATION': 0.70,     # 与全平台生产库
    'IS_LADDER_SHARPE': None,     # 分段一致性，阈值随 alpha 变
}
# 另外两项会直接判死提交（不在 9 项里但实测存在）
PLATFORM_EXTRA_CHECKS = {
    'MATCHES_PYRAMID': 'PASS 表示落入金字塔；ATOM 单数据集才会 PASS（实测 2026-11-13）',
    'DATA_DIVERSITY': '数据多样性，混太多数据集会挂',
    'OSMOSIS_ALLOCATION': '分配项，WARNING 不影响提交',
    'OLD_SIMULATION': '模拟太旧，须重跑；实测窗口 1~2 天，不是固定 24 小时',
    'CLUSTER_TEST': '与同类簇的相关性；今天交的两条是 1.61 / 1.50，线 1.58',
}

# SuperAlpha 的 turnover 区间与常规不同
SUPER_ALPHA_TURNOVER_RANGE = (0.02, 0.40)
SUPER_ALPHA_SELECTION_LIMIT_MIN = 10

# ============================================================
# 四、提交配额
# ============================================================
# 出处: TEST 2026-11-13 平台 /check 返回 REGULAR_SUBMISSION limit=4
#       历史记录: 2026-10-13 曾连交 5 条全部 ACCEPTED（额度可能已收紧）
REGULAR_SUBMISSION_LIMIT = 4
SUPER_ALPHA_SUBMISSION_LIMIT = 1

# Power Pool 配额：纯 Power Pool Alpha 每天 1 个、每范围每月 10 个；
# 但 [Power Pool + ATOM] 或 [Power Pool + Regular] 双标签不受这两项限制。
# 出处: FORUM 44941181410455
POWER_POOL_DAILY_LIMIT = 1
POWER_POOL_MONTHLY_LIMIT = 10
POWER_POOL_ATOM_EXEMPT = True
POWER_POOL_CURRENT_THEME = {
    'name': "GLB/D1 Power Pool Nov'26",
    'window': ('2026-10-26', '2026-11-22'),
    'region': 'GLB', 'delay': 1,
    'requirement': 'AMER Sharpe > 1',
    # 推荐数据集 33 个，帖子点名: pv1, model77, model110, model26,
    # analyst15, fundamental23, model38
    'suggested_datasets': ('pv1', 'model77', 'model110', 'model26',
                           'analyst15', 'fundamental23', 'model38'),
}

# ============================================================
# 五、模拟配额
# ============================================================
# 所有成功模拟都计入额度，重复模拟不剔除。
# 出处: DOC brain-api/understanding-simulation-limits
SIM_CONCURRENCY_LIMIT = 3   # 实测 429 CONCURRENT_SIMULATION_LIMIT_EXCEEDED 的边界
DUPLICATE_SIM_COUNTS = True

# ============================================================
# 六、找字段的正确姿势
# ============================================================
# 错误做法: 只按 alphaCount == 0 升序找。
#   老数据集里 alphaCount 长期为 0 的字段，大概率是全平台用脚本犁过、
#   数据本身缺失或没有信号的死字段。
# 正确做法: 按 dateCreated（上线时间）降序，再叠 alphaCount 升序。
#   刚 onboard 的新字段具备三大优势: prodCorr 低、Pyramid 倍率高、无人挖。
# 出处: FORUM 44941181410455 第四节；官方 11-09 定制建议「用 Date Added 筛选最近新增字段」
FIELD_SORT_PRIMARY = '-dateCreated'   # /data-fields 接口实测可用
FIELD_SORT_SECONDARY = 'alphaCount'   # 升序
# /data-fields 必填参数（缺 instrumentType/universe 会返回 400）
FIELD_QUERY_REQUIRED = ('instrumentType', 'region', 'delay', 'universe')

# ============================================================
# 七、收入三要素
# ============================================================
# 出处: FORUM 32032776365079 最高赞回复
#       「高 value factor + 因子稳健性 + 因子数量是赚钱 3 要素」
# Value Factor 的正道是分散化（多建金字塔），不是把单条做到极致。
# 出处: DOC consultant-information/brain-genius（金字塔至少 3 条 Alpha）
PYRAMID_MIN_ALPHAS = 3

# ============================================================
# 八、本项目被证伪的（不要重试）
# ============================================================
# 这些是花过钱买来的结论，写在这里防止重复踩坑。
DEAD_ENDS = {
    'news_option_recipe': '新闻35%+期权43% 配方只能用一次；第二批换新闻字段后 '
                          'selfCorr 0.80~0.91（TEST 2026-11-13）',
    'mix_3plus_datasets': '混 3 个以上数据集 = 金字塔计 0，VF 必低（FORUM 44941181410455）',
    'alpha_count_zero_only': '只按 alphaCount==0 找字段 = 找死字段（FORUM 44941181410455）',
    'old_stock_resubmit': '过期库存直接提交必 OLD_SIMULATION FAIL，须重跑（TEST 2026-11-13）',
    'self_made_sign_gate': '官方 sign test 对强度型 alpha 结构性不可过，已停（TEST 2026-11-13）',
}
