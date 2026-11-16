# -*- coding: utf-8 -*-
"""op_ban.py —— 算子禁用登记簿（强制拦截，不靠人工自觉）

指令来源：李江波 2026-11-15 12:55
  原文：「最近 10 天禁止使用 group_rank 这个算子，我只能这么下达指令了」

生效窗口：2026-11-15 起连续 10 个自然日（含 11-15，止于 11-24）。
到期后 BANS 记录保留不删，仅 is_active 自动转 False，便于复盘。

设计原则：
  · 所有生成路径（模板库 build / 批次脚本 / 提交器）写盘或发模拟前必须过 guard()。
  · 命中即抛 OpBanned，绝不静默过滤 —— 静默过滤会让人以为"跑过了"。
  · 只做词边界匹配，避免 group_rank 误伤 group_rank_xxx 之类不存在的名字。
"""
import re
from datetime import date

# (算子名, 起始日, 结束日, 指令来源)
BANS = [
    ('group_rank', date(2026, 11, 15), date(2026, 11, 24), '李工指令：最近10天禁用'),
]


class OpBanned(Exception):
    pass


def active_bans(today=None):
    t = today or date.today()
    return [b for b in BANS if b[1] <= t <= b[2]]


def banned_tokens(today=None):
    return {b[0] for b in active_bans(today)}


def is_banned(expr, today=None):
    """返回命中的禁用算子列表（空 = 干净）"""
    s = str(expr)
    return [tok for tok in banned_tokens(today)
            if re.search(r'(?<![A-Za-z0-9_])%s(?![A-Za-z0-9_])' % re.escape(tok), s)]


def guard(expr, cid='', today=None):
    """命中禁用算子直接抛异常。返回 True 表示通过。"""
    hit = is_banned(expr, today)
    if hit:
        raise OpBanned('%s 命中禁用算子 %s（%s ~ %s）'
                       % (cid or '(no-id)', hit,
                          active_bans(today)[0][1], active_bans(today)[0][2]))
    return True


def guard_batch(items, key='code', idkey='cid'):
    """批量校验，返回 (通过列表, 被拦列表[(id, 原因)])"""
    ok, bad = [], []
    for it in items:
        try:
            guard(it.get(key), it.get(idkey, ''))
            ok.append(it)
        except OpBanned as e:
            bad.append((it.get(idkey, ''), str(e)))
    return ok, bad


if __name__ == '__main__':
    print('今日生效禁用:', banned_tokens())
    for probe in ['group_rank(a,industry)', 'group_zscore(a,industry)',
                  'rank(a)*group_rank(b,subindustry)']:
        print(('BLOCK' if is_banned(probe) else 'PASS '), probe)
