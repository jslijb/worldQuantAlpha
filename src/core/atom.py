# -*- coding: utf-8 -*-
"""ATOM 判定器 —— 判断一条表达式是不是「单一数据集 Alpha」。

为什么需要它：
    Pyramid 倍率按最低数据集结算，混 3 个以上直接计 0 个金字塔。
    这是 VF 上不去的结构性原因。生成候选时先过这一关，比交完再后悔便宜。

用法：
    from core.atom import judge, dataset_of
    ok, ds, bad = judge("group_rank(fnd6_xopr/assets, subindustry)")
    # ok=True, ds={'fundamental6'}, bad=[]

    # 检查整批
    python -m src.core.atom spec.json
"""
import io
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.core.knowledge import (  # noqa: E402
    ATOM_EXEMPT_GROUP_FIELDS, ATOM_FORBIDDEN_OPERATORS, ATOM_FORBIDDEN_FIELDS,
    PYRAMID_ZERO_THRESHOLD_DATASETS,
)

# 字段名 -> 数据集。按前缀匹配，越具体的放越前面。
# 只覆盖常用族；查不到的字段返回 None，由调用方决定是否放行。
DATASET_PREFIXES = [
    # 价量（最拥挤，倍率垫底）
    ('pv1', ('close', 'open', 'high', 'low', 'volume', 'vwap', 'returns', 'cap',
             'adv20', 'sharesout', 'dividend', 'split', 'sector', 'industry',
             'subindustry', 'market', 'exchange', 'country')),
    # 财报
    ('fundamental6', ('fnd6_', 'assets', 'liab', 'sales', 'cogs', 'inventory',
                      'cashflow_', 'enterprise_value', 'ebit', 'ebitda', 'ni_',
                      'operating_expense', 'xrent', 'xopr', 'cicurr', 'tstkc',
                      'xintopt', 'intc', 'mfma', 'newa2v', 'ppent', 'capx',
                      # 以下均为 data-fields 逐条核过 dataset=fundamental6 的字段
                      'cash', 'goodwill', 'interest_expense', 'bookvalue_ps')),
    ('fundamental2', ('fnd2_', 'other_comprehensive_income', 'lease_cur',
                      'sbp_nonvst', 'dbt_issue')),
    ('fundamental23', ('fnd23_', 'cumulative_', 'benefit_expense',
                       'dividends_withheld', 'financials_reporting_currency')),
    # 分析师
    ('analyst4', ('anl4_',)),
    ('analyst15', ('anl15_',)),
    ('analyst27', ('anl27_',)),
    ('analyst7', ('est_',)),
    ('model26', ('mdl26_', 'count_analyst_', 'avg_pct_change_estimate',
                 'new_model_activity', 'analysts_count_revising',
                 'count_positive_bold', 'count_negative_bold',
                 'primary_earnings_measure', 'is_parent_entity')),
    ('model31', ('mdl31_', 'last_year_', 'auditor_switch')),
    # 注意：不要用 'long_term_' 这种宽前缀，会把 risk62 的 long_term_momentum_score 抢走
    ('model38', ('backfill_projected', 'projected_dividends', 'long_term_assumed',
                 'long_term_dividend_payout', 'steady_state_backfill',
                 'earnings_measure_type')),
    ('model77', ('mdl77_', 'mdl177_')),
    ('model109', ('mdl109_', 'detrended_price', 'mass_index',
                  'high_low_midpoint', 'logarithmic_market_cap',
                  'analyst_revenue_revision', 'return_on_invested_capital',
                  'triple_exponential_oscillator')),
    ('model110', ('mdl110_',)),
    ('model246', ('mdl246_',)),
    # 新闻/情绪
    ('news12', ('news_pct_', 'news_max_', 'news_tot_', 'news_mins_', 'news_open_',
                'news_spy_', 'nws12_')),
    # news18: 情绪类聚合字段（实测 2026-11-13 查 data-fields 确认 dataset=news18）
    ('news18', ('nws18_', 'mean_equity_sentiment', 'mean_news_impact',
                'mean_composite_sentiment', 'mean_sentiment', 'scl12_sentiment')),
    ('news79', ('earnings_release_headline', 'earnings_headline_tone',
                'editorial_commentary', 'creditworthiness_sentiment',
                'document_sentiment')),
    ('mmp_nlp_sentiment', ('afinn_', 'advertisement_mention')),
    ('socialmedia', ('snt_', 'social_', 'twitter_')),
    # 期权
    ('option8', ('implied_volatility', 'breakeven', 'pcr_', 'parkinson',
                 'option_', 'put_', 'call_')),
    # continuation_score：技术形态相似度（cov 1.00，alphaCount 0~2，几乎无人挖）
    ('continuation_score', ('dead_cat_bounce_', 'bearish_rectangle_', 'bullish_pennant_',
                            'bearish_pennant_', 'gap_up_continuation_', 'ascending_',
                            'ascending_channel_', 'ascending_scallop_', 'continuation_')),
    # risk62：标准风格因子库（2026-04 上线，alphaCount 2~10）
    ('risk62', ('factor_covariance_', 'earnings_per_share_to_price', 'debt_to_equity_ratio',
                'factor_return_', 'long_term_momentum', 'short_term_momentum',
                'book_value_to_market_value', 'factor_specific_return',
                'net_income_per_employee', 'gross_profit_margin')),
    ('model246', ('mdl246_',)),
    # 风险/其他
    ('pattern_scores', ('pattern_',)),
]

# 算子白名单（出现这些 token 时不算字段）
OPERATORS = set('''
group_rank group_zscore group_neutralize group_backfill group_mean group_max
group_min group_sum group_scale group_vector_neut rank zscore scale winsorize
normalize quantile rank_by_side vector_neut regression_neut ts_rank ts_delta
ts_mean ts_std_dev ts_av_diff ts_backfill ts_decay_linear ts_decay_exp_window
ts_zscore ts_scale ts_sum ts_delay ts_corr ts_covariance ts_regression
ts_product ts_quantile ts_argmax ts_argmin ts_count_nans ts_step ts_ir
ts_returns ts_median ts_min ts_max ts_skewness ts_kurtosis ts_entropy
ts_moment ts_co_skewness ts_co_kurtosis ts_theilsen ts_triple_corr
bucket range if_else logical_and logical_or logical_not less greater equal
add subtract multiply divide signed_power log sqrt abs sign power reverse
inverse floor ceiling round min max trade_when hump jump_decay kth_element
pasteurize densify nan_mask nan_out filter arc_tan sigmoid tanh exp
vec_avg vec_sum vec_ir vec_max vec_min vec_count vec_skewness vec_kurtosis
inst_tvr days_from_last_change last_diff_value convert inst_pnl
'''.split())

TOKEN_RE = re.compile(r'[a-zA-Z_][a-zA-Z0-9_]*')

# 算子的**命名参数**（不是算子本身，也不是字段）。
# 例：quantile(x, driver="gaussian")、winsorize(x, std=4)、bucket(x, range="0,1,0.1")
# 去字符串后参数名会留在表达式里，若不排除会被当成字段（曾导致 driver/std 被算进字段集，
# 进而让「单条 alpha 字段数」与「atom 判定」出错）。
PARAM_NAMES = {
    'driver', 'range', 'std', 'stddev', 'rettype', 'limit', 'sigma', 'hump',
    'sensitivity', 'force', 'weight', 'useStd', 'skipBoth', 'constant',
    'buckets', 'NaNGroup', 'longscale', 'shortscale', 'named', 'nan', 'inf',
    'none', 'true', 'false', 'unit', 'axis', 'lag', 'window', 'period',
}

# ---------------------------------------------------------------------------
# 2026-11-13 根因修复：DATASET_PREFIXES 只覆盖老数据集，新数据集
# (ai_equity_alpha / analyst_consensus / analyst69 / predictive_starmine / ...)
# 一律查不到 -> unknown -> judge() 判非 ATOM，把平台已认证的单数据集 Alpha 全杀了。
# 断点：平台 classifications 里 DATA_USAGE:SINGLE_DATA_SET 有 138 条零 FAIL 候选，
# 本地 judge 报 0 条。修复 = 字段归属改查本地 data-fields 全量缓存。
# ---------------------------------------------------------------------------
PROJ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_FIELD_MAP = None


def _load_field_map():
    """合并本地各市场 data-fields 缓存：{字段名: 数据集id}。

    ★ 11-16 修复：`all_fields_*.json`（26333 条）覆盖不全，缺 `beta_prediction_dispersion`
      等字段 ⇒ dataset_of() 返 None ⇒ judge() 误判"无法判定数据集归属" ⇒ ATOM 门误杀。
      新增 `src/core/pull_field_map.py` 从平台 GET /data-fields 拉**权威**全量映射，
      落 `field_ds_map.json`（合并版）+ `field_ds_map_by_region.json`（分区域版）。
      优先级：平台权威合并表 > all_fields_*.json > 硬编码前缀。
    """
    global _FIELD_MAP
    if _FIELD_MAP is not None:
        return _FIELD_MAP
    import glob
    d = os.path.join(PROJ, 'data', 'alpha_quality_analysis')
    m = {}

    # ① 平台权威合并表（11-16 新增，最优先）
    for name in ('field_ds_map.json',):
        p = os.path.join(d, name)
        if os.path.exists(p):
            try:
                for k, v in (json.load(io.open(p, encoding='utf-8')) or {}).items():
                    if v:
                        m.setdefault(k.lower(), v)
            except Exception:
                pass

    # ② 历史 all_fields_*.json（补缺，不覆盖①）
    for p in glob.glob(os.path.join(d, 'all_fields_*.json')):
        try:
            for name, meta in json.load(io.open(p, encoding='utf-8')).items():
                ds = (meta or {}).get('ds')
                if ds:
                    m.setdefault(name.lower(), ds)
        except Exception:
            pass

    _FIELD_MAP = m
    return m


_FIELD_MAP_BY_REGION = None


def load_field_map_by_region(region):
    """{region: {字段名: dataset_id}}。11-16 新增：修跨市场串味。

    同一字段名在不同 region 可能属不同数据集；合并表只留第一个命中 ⇒ 串味。
    判定时按表达式所在 region 查分区域表，查不到再回落合并表。
    """
    global _FIELD_MAP_BY_REGION
    if _FIELD_MAP_BY_REGION is None:
        p = os.path.join(PROJ, 'data', 'alpha_quality_analysis',
                         'field_ds_map_by_region.json')
        if os.path.exists(p):
            try:
                _FIELD_MAP_BY_REGION = json.load(io.open(p, encoding='utf-8')) or {}
            except Exception:
                _FIELD_MAP_BY_REGION = {}
        else:
            _FIELD_MAP_BY_REGION = {}
    return _FIELD_MAP_BY_REGION.get((region or '').upper(), {})


def atom_from_platform(alpha):
    """以平台 classifications 为唯一权威判 ATOM（优先于本地 judge）。"""
    cls = [c.get('id') for c in (alpha.get('classifications') or [])]
    return any('SINGLE_DATA_SET' in (c or '') for c in cls)


def platform_fails(alpha):
    """平台 checks 的 FAIL 列表 [(name, value)]；PENDING / WARNING 不算 FAIL。"""
    chk = ((alpha.get('is') or {}).get('checks') or [])
    return [(c.get('name'), c.get('value')) for c in chk if c.get('result') == 'FAIL']


def normalize_group_field(name):
    """分组字段名在表达式里可能是裸名，也可能是参数位置。"""
    return name.lower()


def fields_of(expr):
    """提取表达式里的字段（排除算子、数字、字符串字面量）。"""
    if not expr:
        return set()
    e = re.sub(r'"[^"]*"', ' ', expr)          # 去字符串
    e = re.sub(r'//.*|#.*', ' ', e)            # 去注释
    toks = set(TOKEN_RE.findall(e))
    out = set()
    for t in toks:
        tl = t.lower()
        if tl in OPERATORS:
            continue
        if tl in PARAM_NAMES:
            continue
        if len(tl) <= 2:
            continue
        if tl.isdigit():
            continue
        out.add(tl)
    return out


def dataset_of(field, _cache={}):
    """字段属于哪个数据集。

    顺序：本地 data-fields 全量缓存（覆盖新增数据集） -> 硬编码前缀（老数据集兜底）。
    查不到返回 None。
    """
    f = field.lower()
    if f in _cache:
        return _cache[f]
    ds = _load_field_map().get(f)
    if ds:
        _cache[f] = ds
        return ds
    for ds, prefixes in DATASET_PREFIXES:
        for p in prefixes:
            if f == p or f.startswith(p):
                _cache[f] = ds
                return ds
    _cache[f] = None
    return None


def judge(expr):
    """判一条表达式。

    返回 (is_atom, datasets, reasons)
        is_atom  : True 表示单数据集（ATOM 合格）
        datasets : 识别到的数据集集合
        reasons  : 不合格的具体原因；合格时为空
    """
    reasons = []
    if not expr or not expr.strip():
        return False, set(), ['表达式为空']

    flds = fields_of(expr)
    if not flds:
        return False, set(), ['没解析出任何字段']

    # 坑 1: 禁用算子
    for op in ATOM_FORBIDDEN_OPERATORS:
        if re.search(r'\b%s\s*\(' % op, expr, re.I):
            reasons.append('用了 %s()，底层会调 pv1' % op)

    # 坑 2/3: 禁用字段（cap/close/returns/vwap 等属于 pv1）
    exempt = set(ATOM_EXEMPT_GROUP_FIELDS)
    hit_forbidden = sorted(f for f in flds if f in ATOM_FORBIDDEN_FIELDS and f not in exempt)
    if hit_forbidden:
        # 只有跟其他数据集混用时才是硬伤；单独用 pv1 字段本身也是 pv1 单数据集
        reasons.append('出现 pv1 字段: %s（若与其他数据集混用则破坏 ATOM）'
                       % ', '.join(hit_forbidden[:5]))

    # 统计数据集
    ds_hit = {}
    unknown = []
    for f in flds:
        if f in exempt:
            continue
        d = dataset_of(f)
        if d:
            ds_hit.setdefault(d, []).append(f)
        elif f not in ATOM_FORBIDDEN_FIELDS:
            unknown.append(f)

    datasets = set(ds_hit)

    if len(datasets) >= PYRAMID_ZERO_THRESHOLD_DATASETS:
        detail = '; '.join('%s(%d)' % (d, len(v)) for d, v in sorted(ds_hit.items()))
        reasons.append('混了 %d 个数据集 = 金字塔计 0 个 [%s]' % (len(datasets), detail))
    elif len(datasets) == 2:
        detail = '; '.join('%s(%d)' % (d, len(v)) for d, v in sorted(ds_hit.items()))
        reasons.append('混了 2 个数据集，Pyramid 倍率按最低的算 [%s]' % detail)

    if unknown:
        reasons.append('无法判定数据集归属的字段 %d 个: %s'
                       % (len(unknown), ', '.join(sorted(unknown)[:5])))

    is_atom = len(datasets) <= 1 and not unknown
    return is_atom, datasets, reasons


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print('用法: python -m src.core.atom <spec.json>')
        return
    spec = json.load(io.open(sys.argv[1], encoding='utf-8'))
    ok_n = 0
    for cid, v in spec.items():
        expr = v['expr'] if isinstance(v, dict) else v
        ok, ds, why = judge(expr)
        if ok:
            ok_n += 1
            print('✅ %-40s %s' % (cid[:40], '/'.join(sorted(ds)) or '?'))
        else:
            print('❌ %-40s %s' % (cid[:40], ' | '.join(why)[:150]))
    print('\nATOM 合格 %d / %d' % (ok_n, len(spec)))


if __name__ == '__main__':
    main()
