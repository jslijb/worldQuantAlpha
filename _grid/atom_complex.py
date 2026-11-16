# -*- coding: utf-8 -*-
"""atom_complex.py — 单数据集「复杂配方」模板库（2026-11-15）

两条硬约束（李工 11-15 指令）：
  1. 单数据集：模板只用同一 dataset 的字段 + 6 个豁免分组字段（country/exchange/
     market/sector/industry/subindustry）。模板结构上就杜绝跨数据集拼腿。
  2. 禁止裸原子：每条表达式由 3~4 个同数据集字段 + 10~20 个算子构成，
     不再出现 ts_zscore(单字段, 60) 这种 2 算子裸写法。

依据（论坛原文，见 docs/forum/atom_pack/）：
  - 主帖 44770798147735：ATOM 定义、木桶倍率、隐式 pv1 三坑
  - 43712961725335：金字塔 = region+delay+category，混 3 类计 0
  - 40018929254935：「新手尽量不要碰过于复杂的模板，尽量选单字段的能出 atom 的模板」
  - 44645223044247：atom 比例 81.7%→50.5% 导致 VF 0.97→0.39

用法：
    from _grid.atom_complex import build, TEMPLATES
    exprs = build({'f1': 'a', 'f2': 'b', 'f3': 'c', 'f4': 'd'})
"""
import re

# 模板：{f1}~{f4} 全部来自同一数据集
# f4 约定为「同数据集内的市值/规模字段」，用于分桶与残差化（绝不用 pv1 的 cap）
TEMPLATES = [
    ('C1_三腿时序共振', (
        'group_zscore(ts_decay_linear('
        'ts_zscore(ts_mean({f1},20)-ts_mean({f1},120),120)'
        '+ts_zscore(ts_delta({f2},20)/ts_std_dev({f2},60),120)'
        '-ts_zscore(ts_std_dev({f3},60)/ts_mean({f3},250),120)'
        ',10),subindustry)'), 12),

    ('C2_同集市值桶中性', (
        'group_neutralize(ts_decay_linear('
        'rank(ts_zscore({f1},250))+rank(ts_zscore({f2},120))-rank(ts_zscore({f3},60))'
        ',15),bucket(rank({f4}),range="0,1,0.2"))'), 11),

    ('C3_状态切换', (
        'if_else(ts_zscore({f4},250)>0,'
        'quantile(ts_decay_linear(ts_delta({f2},20)/ts_std_dev({f2},60),10),driver="gaussian"),'
        'quantile(ts_decay_linear(-ts_delta({f2},20)/ts_std_dev({f2},60),10),driver="gaussian"))'), 12),

    ('C4_残差化去市值暴露', (
        'ts_quantile(ts_decay_linear('
        'ts_zscore({f1},120)-ts_regression(ts_zscore({f1},120),ts_zscore({f4},120),250,rettype=3)'
        '+0.5*(ts_zscore({f2},60)-ts_regression(ts_zscore({f2},60),ts_zscore({f4},60),120,rettype=3))'
        '+rank(ts_delta({f3},20)/ts_std_dev({f3},60))'
        ',10),subindustry)'), 13),

    ('C5_四字段加权打分', (
        'group_zscore(ts_decay_linear('
        '0.35*ts_rank({f1},250)+0.25*ts_rank({f2},120)'
        '+0.20*ts_rank({f3},60)+0.20*ts_rank({f4},20)'
        ',20),subindustry)'
        '+0.3*group_scale(ts_zscore(ts_mean({f1},20)-ts_mean({f1},120),250),subindustry)'), 14),

    ('C6_相关性分歧', (
        'rank(ts_decay_linear('
        'ts_zscore(ts_corr({f1},{f2},120)-ts_corr({f3},{f2},60),250)'
        '+0.5*ts_zscore(ts_corr({f1},{f4},60)-ts_corr({f3},{f4},120),120)'
        '-0.3*ts_zscore(ts_std_dev({f1},60)/ts_mean({f1},250),120)'
        ',10),subindustry)'), 14),
]

# ---------------- 基本面族模板（model109 内分析师/财务字段，11-15 追加） ----------------
# 说明：与 C 系同构，但字段换成同一 dataset 内的修正/增长/质量类，信号强度更高。
FUND_TEMPLATES = [
    ('D1_修正增长质量三腿', (
        'group_zscore(ts_decay_linear('
        'ts_zscore(ts_mean({f1},20),250)'
        '+ts_zscore({f2},250)'
        '-ts_zscore({f3},250)'
        '+0.5*rank(ts_delta({f4},60)/ts_std_dev({f4},250))'
        ',20),subindustry)'), 12),

    ('D2_预期实现增长差', (
        'group_scale(ts_decay_linear('
        'ts_zscore({f1},250)-ts_zscore({f2},250)'
        '+0.5*ts_zscore(ts_delta({f3},20)/ts_std_dev({f3},120),250)'
        '-0.3*ts_zscore({f4},120)'
        ',15),subindustry)'), 12),

    ('D3_质量条件分支', (
        'if_else(ts_zscore({f4},250)<0,'
        'quantile(ts_decay_linear(ts_zscore({f1},120)+ts_zscore({f2},250),15),driver="gaussian"),'
        'quantile(ts_decay_linear(ts_zscore({f1},120)-ts_zscore({f2},250),15),driver="gaussian"))'), 10),

    ('D4_四字段打分加市值桶', (
        'group_neutralize(ts_decay_linear('
        '0.30*ts_rank({f1},250)+0.25*ts_rank({f2},250)'
        '+0.25*ts_rank({f3},250)-0.20*ts_rank({f4},250)'
        ',20),bucket(rank({f5}),range="0,1,0.2"))'), 12),

    ('D5_修正残差化', (
        'ts_scale(ts_decay_linear('
        'ts_zscore({f1},120)'
        '-ts_regression(ts_zscore({f1},120),ts_zscore({f2},120),250,rettype=3)'
        '+0.5*ts_zscore(ts_delta({f3},60)/ts_std_dev({f3},250),250)'
        ',15),subindustry)'), 11),
]

EXEMPT = ('country', 'exchange', 'market', 'sector', 'industry', 'subindustry')
FORBIDDEN_OPS = ('convert(', 'inst_pnl(')
FORBIDDEN_FIELDS = ('cap', 'close', 'returns', 'vwap', 'open', 'high', 'low', 'volume')

# 表达式里出现的字段名（粗抽：字母开头的标识符，排除算子名）
_TOKEN = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')


def fields_in(expr, known_fields):
    """返回表达式实际用到的数据集字段（按 known_fields 白名单过滤）。"""
    toks = set(_TOKEN.findall(expr))
    return sorted(t for t in toks if t in known_fields)


def check(expr, known_fields, dataset):
    """单数据集 + 禁裸原子 自检，返回 (ok, 说明)。"""
    used = fields_in(expr, known_fields)
    if not used:
        return False, '未识别到任何数据集字段'
    bad_ops = [o for o in FORBIDDEN_OPS if o in expr]
    if bad_ops:
        return False, '隐式引 pv1 算子: %s' % bad_ops
    bad_f = [f for f in FORBIDDEN_FIELDS if re.search(r'(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])' % f, expr)]
    # 这些名字若是数据集自带字段（如 logarithm_float_market_cap 不是 cap），需白名单豁免
    bad_f = [f for f in bad_f if f not in known_fields]
    if bad_f:
        return False, '引了 pv1 字段: %s' % bad_f
    # 分组字段只允许豁免 6 个
    grp = re.findall(r',\s*([a-z_]+)\s*\)', expr)
    illegal = [g for g in grp if g not in EXEMPT and g not in known_fields]
    if illegal:
        return False, '分组字段非法: %s' % illegal
    n_ops = len(re.findall(r'[a-z_]+\s*\(', expr))
    if n_ops < 8:
        return False, '算子数 %d < 8，属裸原子' % n_ops
    return True, '单数据集 %s，字段 %d 个，算子 %d 个' % (dataset, len(used), n_ops)


def build(role_fields, dataset='unknown', only=None, tpls=None):
    """role_fields: {'f1':..,'f2':..,'f3':..,'f4':..}，全部必须同属 dataset。
    返回 [(名字, 表达式, 说明)]。"""
    known = set(role_fields.values())
    out = []
    for name, tpl, _ops in (tpls or TEMPLATES):
        if only and name not in only:
            continue
        expr = tpl.format(**role_fields)
        ok, msg = check(expr, known, dataset)
        out.append((name, expr, msg if ok else 'REJECT: ' + msg))
    return out
