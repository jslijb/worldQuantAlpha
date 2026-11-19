# -*- coding: utf-8 -*-
"""op_ban.py —— 算子禁用登记簿（强制拦截，不靠人工自觉）

指令来源：李江波 2026-11-15 12:55
  原文：「最近 10 天禁止使用 group_rank 这个算子，我只能这么下达指令了」

★ 11-16 16:25 指令变更（李工）：
  「甚至 group_rank 这个算子从黑名单剔除。」
  ⇒ **group_rank 的 10 天禁令撤销**（该禁令曾导致 11-15~11-16 把 group_rank 整批
    替换成 group_scale，实测同骨架换外壳 group_rank 2.05 / group_scale 1.16
    = **降级 43%**，且禁令把骨架内部的 group_rank 一起砍了 ⇒ 构造深度塌陷）。
  ⇒ BANS 记录**保留**（不删，便于复盘），仅生效状态转 False。

生效窗口：2026-11-15 起连续 10 个自然日（含 11-15，止于 11-24）。
到期后 BANS 记录保留不删，仅 is_active 自动转 False，便于复盘。

设计原则：
  · 所有生成路径（模板库 build / 批次脚本 / 提交器）写盘或发模拟前必须过 guard()。
  · 命中即抛 OpBanned，绝不静默过滤 —— 静默过滤会让人以为"跑过了"。
  · 只做词边界匹配，避免 group_rank 误伤 group_rank_xxx 之类不存在的名字。
"""
import re
from datetime import date

# (算子名, 起始日, 结束日, 指令来源, 是否仍生效)
BANS = [
    # ★ 已撤销（李工 2026-11-16 16:25）：group_rank 从黑名单剔除
    ('group_rank', date(2026, 11, 15), date(2026, 11, 24),
     '李工指令：最近10天禁用', False),
]


class OpBanned(Exception):
    pass


def active_bans(today=None):
    """当前生效的禁用算子。

    ★ 11-16 16:25：BANS 记录保留但带生效位；group_rank 已被李工撤销 ⇒ 不再拦截。
    """
    t = today or date.today()
    out = []
    for b in BANS:
        name, d0, d1, src = b[0], b[1], b[2], b[3]
        still_on = b[4] if len(b) > 4 else True
        if still_on and d0 <= t <= d1:
            out.append((name, d0, d1, src))
    return out


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
        _b = active_bans(today)[0]
        raise OpBanned('%s 命中禁用算子 %s（%s ~ %s）'
                       % (cid or '(no-id)', hit, _b[1], _b[2]))
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
