# -*- coding: utf-8 -*-
"""depth_check.py — 构造深度检查器（2026-11-16）

为什么要有它
============
起因（李工 11-16 10:50 批评，实为事实）：
  11-15 那批"新数据集 ATOM 批"21 条，**S 全部在 -1.27 ~ 0.67**，
  我据此写下"新数据集过不了门 / 只能靠量价续命"的结论。
  李工指出：**这是拿浅构造测高价值数据，然后拿测试结果胡说八道。**

复盘落盘证据（`_autologs/_gen_atom_blue_1115.py` 注释原文）：
  「每个字段都是 used<=1 的蓝海字段，**表达式只做单字段变换**（ATOM 合规）」
  ⇒ ATOMB 11 条 = 单字段 + 1~2 层算子（如 `ts_rank({f},252)`）。
  ATOM1115 11 条 = 多字段但**各自独立归一化后任意符号相加**
  （`group_zscore(ts_decay_linear(ts_rank(A) ± ts_zscore(B) ± ts_mean(ts_zscore(C)),N),subindustry)`）
  ⇒ 21 条里只有 3 条含比值/乘法/条件，**字段之间的关系被抹掉**。

台账实测（360 条，本机解析）：
  算子数 ≤3 时 S≥1.58 比例 40~82%；**算子数 ≥4 时 100%**（n=302）。
  ⇒ "表达式必须复杂"成立；但"复杂"必须复杂在**关系与变换层数**上，不是算子个数。

三条判据（缺一即判定为"浅构造"）
================================
D1 关系型算子占比：表达式里必须出现 **≥1 个字段间关系算子**
   （除法 `/`、乘法 `*`、`if_else`、`trade_when`、`ts_corr`、`ts_regression`、`bucket`）。
   判据依据：活样板 `1YwKML56`（S2.21）= `group_rank(ts_av_diff(cashflow_op/enterprise_value,60),industry)`
   —— 只有 2 个算子，但**有比值**。

D2 变换层数：同一字段上必须有 **≥2 层连续变换**
   （如 `ts_av_diff(x,20)/ts_std_dev(x,60)` = 差分后再除波动，2 层；
    `ts_zscore(ts_mean(x,20)-ts_mean(x,120),120)` = 均值差再归一，2 层）。
   浅构造的特征是"字段 → 一次归一化 → 相加"，变换层数 = 1。

D3 禁止"独立归一化后相加"：**不允许**出现两个及以上
   `ts_rank(...)` / `ts_zscore(...)` / `ts_mean(...)` 直接以 `+`/`-` 相连
   （这是 11-15 那批的形态：信号互抵，S≈0）。

用法
====
    python _grid/depth_check.py "表达式"                      # 单条判定
    python _grid/depth_check.py --file cands.json            # 批量
    python _grid/depth_check.py --file cands.json --strict   # 有浅构造即非零退出

在流程中的位置
==============
本模块是**发模拟前**的自检，与 `op_ban.py`（算子禁用）、`diversity.py`（多样性）
并列，是三道发模拟前的门之一。

★ 重要纪律（李工 11-16 纠正）：
  **禁止用浅构造的结果给数据集/字段判死刑。**
  某数据集在浅构造下 S 低，只能得出"这个构造方式不行"，
  不能得出"这个数据集没用"。要判数据集死刑，必须先跑深构造。
"""
import io
import json
import os
import re
import sys

# ---------------------------------------------------------------- 关系型算子
# 表达式里出现即视为"含字段间关系"
REL_OPS = ('ts_corr', 'ts_regression', 'if_else', 'trade_when', 'bucket')
REL_SYMBOLS = ('/', '*')

# 归一化算子（用于 D3 检测）
NORM_OPS = ('ts_rank', 'ts_zscore', 'ts_mean', 'ts_scale', 'ts_quantile',
            'ts_std_dev', 'ts_delta', 'ts_av_diff')

_OP = re.compile(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(')


def _ops(expr):
    return _OP.findall(expr)


def has_relation(expr):
    """D1：是否含字段间关系。

    关系的三种形态（缺一即视为无关系）：
      R1 算子型：ts_corr / ts_regression / if_else / trade_when / bucket
      R2 符号型比值与乘积：'/' '*'
      R3 **字段间直接相减**（'a - b'，两个字段相减本身就是关系，
         如期限差 `pcr_oi_10 - pcr_oi_360`、价差 `call - put`）——
         ★ 2026-11-16 修正：原先 D1 只认 R1/R2，把「两期限直接相减」误判为无关系。
         活样板 `QPK3n9Zw` 的第二个腿 `implied_volatility_call_90 - implied_volatility_call_30`
         正是期限差，误杀会导致深度门不可信。

    判定 R3 时要排除「同一个归一化结果内部的减号」与「窗口参数里的负号」，
    做法：去掉所有窗口参数 `(x,250)` 的第二个参数后再找顶层减号。
    """
    ops = set(_ops(expr))
    if ops & set(REL_OPS):
        return True, sorted(ops & set(REL_OPS))
    if any(s in expr for s in REL_SYMBOLS):
        return True, [s for s in REL_SYMBOLS if s in expr]

    # R3：找减号两侧都是「字段/表达式」的位置（不限括号深度，
    # 但要排除窗口参数 `(x,250)` 里的负号与纯数字相减）。
    # 实现：把表达式按所有加减号切开，看两侧是否都含字母标识符。
    body = re.sub(r'"[^"]*"', '""', expr)
    # 去掉窗口参数（逗号后紧跟数字的第二个参数）
    body2 = re.sub(r',\s*-?\d+\s*\)', ')', body)
    parts = re.split(r'(?<![\w)])-(?![\w(])', body2)
    if len(parts) >= 2:
        for i in range(len(parts) - 1):
            l, r = parts[i].strip(), parts[i + 1].strip()
            # 两侧都要含标识符（排除 1-0 这种纯数字）
            lt = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', l)
            rt = re.findall(r'[A-Za-z_][A-Za-z0-9_]*', r)
            if lt and rt:
                return True, ['-']
    return False, []


def transform_layers(expr):
    """D2：同一字段上连续变换的层数。

    做法：对每个**字段叶子**，数它被多少层变换算子包裹（含并列的组合）。
    例：
      ts_av_diff(x,60)                      -> 1 层
      ts_av_diff(x,20)/ts_std_dev(x,60)     -> 2 层（差分后除波动 = 反复变换）
      ts_zscore(ts_mean(x,20)-ts_mean(x,120),120) -> 2 层（均值差再归一）
      ts_rank(x,250)                       -> 1 层
    实现：把每个变换算子的实参切出来，递归统计"该实参内部还含几个变换算子"，
          取最深路径；并列算子（/ * +）不增加层数但也不算浅。
    """
    s = expr
    best = 0

    def count_in(text):
        """text 里变换算子的最大嵌套深度。"""
        nonlocal best
        best_here = 0
        for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', text):
            name = m.group(1)
            if name not in NORM_OPS:
                continue
            d, i = 1, m.end()
            while i < len(text) and d > 0:
                if text[i] == '(':
                    d += 1
                elif text[i] == ')':
                    d -= 1
                i += 1
            inner = text[m.end():i - 1]
            sub = count_in(inner)
            best_here = max(best_here, 1 + sub)
        return best_here

    # 顶层：把表达式按最外层调用切开，逐段统计
    for m in re.finditer(r'([A-Za-z_][A-Za-z0-9_]*)\s*\(', s):
        d, i = 1, m.end()
        while i < len(s) and d > 0:
            if s[i] == '(':
                d += 1
            elif s[i] == ')':
                d -= 1
            i += 1
        inner = s[m.end():i - 1]
        best = max(best, count_in(inner))

    # 并列组合（/ * + - 连接的多个变换）也算"同一字段被反复变换"：
    # 统计顶层并列的变换算子个数，>=2 时至少 2 层
    top_level_norm = len(re.findall(
        r'(?:^|[+\-*/(,])\s*(ts_rank|ts_zscore|ts_mean|ts_scale|ts_quantile|ts_std_dev|ts_delta|ts_av_diff)\s*\(',
        s))
    best = max(best, min(top_level_norm, 2) if top_level_norm >= 2 else 0)
    return best


_NORM_CALL = re.compile(
    r'(ts_rank|ts_zscore|ts_mean|ts_scale|ts_quantile)\s*\([^()]*\)')


def parallel_sum(expr):
    """D3：是否存在"多个独立归一化直接相加"。

    检测：去掉所有空白后，找 `NORM(x) + NORM(y)` 或 `NORM(x) - NORM(y)` 形态。
    """
    body = re.sub(r'\s+', '', expr)
    calls = list(_NORM_CALL.finditer(body))
    for i in range(len(calls) - 1):
        a, b = calls[i], calls[i + 1]
        between = body[a.end():b.start()]
        # 中间只允许 + - （可带括号包裹）
        if re.fullmatch(r'[+\-()0-9.\*]*', between or '') and ('+' in between or '-' in between):
            # 排除一个归一化嵌套另一个的情况
            if a.start() < b.start() and a.end() <= b.start():
                if b.start() >= a.end():
                    return True, '%s ... %s 之间只有 +/-' % (a.group(1), b.group(1))
    return False, ''


def check(expr):
    """返回 (是否合格, 明细 dict)。"""
    e = str(expr)
    # SUPER 的 selection 表达式（如 "1 - self_correlation"）没有数据字段，
    # 不适用数据深度判据 —— 直接放行（台账里 P05eKkr7 S3.63 / wpoXaojQ S2.78 都是这种）。
    if 'self_correlation' in e and not re.search(r'[a-z][a-z0-9_]{2,}\s*\(', e.replace('self_correlation(', '')):
        return True, {'算子数': len(_ops(e)), '关系型': 'SUPER 豁免',
                      '变换层数': 0, '并行相加': '无', '不合格原因': []}
    ops = _ops(e)
    rel_ok, rel_why = has_relation(e)
    layers = transform_layers(e)
    par_ok, par_why = parallel_sum(e)

    detail = {
        '算子数': len(ops),
        '关系型': rel_why,
        '变换层数': layers,
        '并行相加': par_why or '无',
    }
    fails = []
    if not rel_ok:
        fails.append('D1 无字段间关系算子（除/乘/if_else/ts_corr/ts_regression）')
    # D2 与 D3 合并判定：**深挖 = 变换层数 ≥2（反复变换） 或 关系算子自带深挖语义**。
    #   依据活样板 1YwKML56(S2.21) = group_rank(ts_av_diff(cashflow_op/enterprise_value,60),industry)
    #   —— 层数只有 1，但比值本身就是"反复变换"（两个字段各自变换后再相除）。
    if layers < 2 and not rel_ok:
        fails.append('D2 变换层数 %d < 2 且无关系算子（字段只被变换了一次）' % layers)
    if par_ok and layers < 2:
        fails.append('D3 独立归一化后直接相加：%s' % par_why)
    detail['不合格原因'] = fails
    return (not fails), detail


# ---------------------------------------------------------------- CLI
def main():
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    if '--file' in argv:
        p = argv[argv.index('--file') + 1]
        items = json.load(io.open(p, encoding='utf-8'))
        if isinstance(items, dict):
            items = [items]
        strict = '--strict' in argv
        bad = 0
        for it in items:
            code = it.get('code') or it.get('expr') or ''
            cid = it.get('cid') or it.get('id') or ''
            ok, d = check(code)
            flag = 'PASS' if ok else 'SHALLOW'
            if not ok:
                bad += 1
            print('%-4s %-34s 算子=%-3d 层数=%-2d 关系=%-18s' % (
                flag, cid[:34], d['算子数'], d['变换层数'], str(d['关系型'])[:18]))
            if not ok:
                for r in d['不合格原因']:
                    print('       - %s' % r)
        print('\n合计 %d 条，浅构造 %d 条' % (len(items), bad))
        return 1 if (strict and bad) else 0

    ok, d = check(argv[0])
    print('结论: %s' % ('PASS 深构造合格' if ok else 'SHALLOW 浅构造'))
    for k, v in d.items():
        print('  %-12s %s' % (k, v))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
