# -*- coding: utf-8 -*-
"""atom_single.py — 单字段（Single-Field）复杂 ATOM 模板库

规矩来源（docs/forum/atom_pack/post_main.txt 原文）：
  · ATOM 定义 = 整个表达式只用同一个数据集的字段（第 14 行）
  · 单字段是 ATOM 的特例，但只有 ATOM 才能把 Avg distinct Fields 压到 1（第 23 行）
  · IQC 复盘第一条忠告：尽量选单字段的、能出 atom 的模板（第 52 行）
  · 4 套官方/社区单字段模板（第 105-175 行）
  · 硬红线：绝不用 convert()/inst_pnl()；绝不用 cap/close/returns/vwap 做 bucket 或 vector_neut（第 27-31 行）

本库的"复杂"指同一字段反复使用 + 多算子嵌套，字段数恒为 1：
  复杂度来自 ts_mean/ts_delta/ts_std_dev/ts_rank/ts_zscore/ts_decay_linear/ts_regression 的层叠，
  不是靠混数据集。

每个模板返回 (name, expr, n_ops)，{F} 为字段占位符。
"""
import re

TEMPLATES = [
    # 帖子原文模板 1（长短周期均值比）
    # 2026-11-15 李工禁 group_rank：外层改全市场 rank，无分组
    ('P1_长短均值比',
     'rank(ts_mean({F},20)/ts_mean({F},120))'),

    # 帖子原文模板 2（时序标准化 + 行业内中性化）
    ('P2_时序标准化中性',
     'group_neutralize(ts_zscore({F},60),subindustry)'),

    # 帖子原文模板 3（一年期分位反转，低换手）
    ('P3_分位一年反转',
     'ts_decay_linear(-ts_rank({F},252),10)'),

    # 帖子原文模板 4（差分除以自身波动，行业内排名）
    # 同核改用纯时序 z 承接横截面（平台 neutralization 已在组合层去行业均值）
    ('P4_信噪比差分',
     'ts_zscore(ts_delta({F},20)/ts_std_dev({F},60),250)'),

    # ---- 以下为按"单字段+多算子"扩写的复杂版（字段数仍为 1）----
    ('S1_双周期比+趋势确认',
     'group_zscore(ts_decay_linear(ts_mean({F},20)/ts_mean({F},120)-1,10)'
     '+0.5*ts_rank(ts_delta({F},20)/ts_std_dev({F},60),120),subindustry)'),

    ('S2_分位反转+波动归一差分',
     'quantile(ts_decay_linear(-ts_rank({F},252),10)'
     '+ts_zscore(ts_delta({F},5)/ts_std_dev({F},20),120),driver="gaussian")'),

    ('S3_长期偏离+加速度',
     'group_neutralize(ts_decay_linear('
     'ts_zscore({F},60)-ts_zscore({F},250)+ts_delta(ts_zscore({F},60),20)'
     ',15),subindustry)'),

    ('S4_信噪动量+短期反转',
     'group_scale(ts_decay_linear(ts_delta({F},20)/ts_std_dev({F},60),10)'
     '-0.5*ts_zscore(ts_mean({F},5)/ts_mean({F},60),120),industry)'),

    ('S5_趋势震荡条件分支',
     'if_else(ts_zscore(ts_mean({F},20)-ts_mean({F},120),250)>0,'
     'rank(ts_decay_linear(ts_zscore({F},60),10)),'
     'rank(ts_decay_linear(-ts_zscore({F},250),10)))'),

    ('S6_多尺度波动调整动量',
     'ts_quantile(ts_decay_linear('
     'ts_zscore({F},60)/ts_std_dev(ts_zscore({F},60),120)'
     '+0.5*ts_rank(ts_delta({F},60),250),10),250)'),

    # ---- 以下**刻意不用 group_rank**（来源：AI 工作流帖已验证模式，改成 ATOM 安全版）----
    # 原作者写法 rank(ts_rank(X/close,40))，/close 属 pv1 会破 ATOM，改成分母用自身长周期均值
    ('N1_无分组_时序分位排名',
     'rank(ts_rank({F}/ts_mean({F},120),40))'),

    # 原作者写法 rank(X)*rank(ts_rank(X/close,40))，双腿乘法
    ('N2_无分组_乘法双确认',
     'rank({F}/ts_mean({F},120))*rank(ts_rank({F},40))'),

    # 原作者 finetune 里的信号增强写法 signed_power(expr,2)
    ('N3_无分组_符号平方增强',
     'signed_power(ts_zscore({F}/ts_mean({F},120),60),2)'),

    # 原作者 finetune 里的 group_zscore 包裹（外层是 group_zscore 不是 group_rank）
    ('N4_分组标准化_非排名',
     'group_zscore(ts_rank({F}/ts_mean({F},120),40),subindustry)'),

    # 减法组合：短期反转 + 长期动量（无 group_rank、无分组）
    ('N5_无分组_反转减动量',
     'ts_decay_linear(-ts_rank({F},20)+ts_rank({F},250),10)'),

    # 三目写法（原作者模式 4 的 ATOM 安全版）
    ('N6_三目阈值切换',
     'rank(ts_sum({F}/ts_mean({F},120),60))>0.5'
     '?rank(ts_delta({F},20)):rank(-ts_delta({F},60))'),
]

# ATOM 硬红线：这些 token 一旦出现在表达式里，直接判非单数据集（帖子第 27-31 行）
PV1_TOKENS = ('close', 'cap', 'returns', 'vwap', 'volume', 'high', 'low', 'open',
              'adv20', 'sharesout', 'inst_pnl', 'convert(')
EXEMPT_GROUPS = ('country', 'exchange', 'market', 'sector', 'industry', 'subindustry')

FIELD_RE = re.compile(r'\b([a-z][a-z0-9_]{3,})\b')


def n_ops(expr):
    return len(re.findall(r'([a-z_][a-z0-9_]{2,})\s*\(', expr))


def fields_in(expr, known):
    """表达式里用到的真实字段（用已知字段清单过滤，避免把算子当字段）"""
    return sorted({t for t in FIELD_RE.findall(expr) if t in known})


def check(expr, known, dataset='?'):
    """单字段 ATOM 自检，返回 (verdict, msg)"""
    fs = fields_in(expr, known)
    if len(fs) != 1:
        return 'REJECT', '字段数 %d != 1: %s' % (len(fs), fs)
    hit = [t for t in PV1_TOKENS if re.search(r'\b%s\b' % re.escape(t), expr)]
    if hit:
        return 'REJECT', '含 pv1 token: %s' % hit
    ops = n_ops(expr)
    if ops < 4:
        return 'WARN', '算子数 %d 偏少' % ops
    return 'OK', '单字段 %s | 算子 %d' % (fs[0], ops)


def build(field, only=None, tpls=None):
    out = []
    for name, tpl in (tpls or TEMPLATES):
        if only and name not in only:
            continue
        out.append((name, tpl.replace('{F}', field), n_ops(tpl)))
    return out
