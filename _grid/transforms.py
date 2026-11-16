# -*- coding: utf-8 -*-
"""transforms.py — 变换族库（v3, 2026-11-15 李工禁 group_rank 后重写）

背景：
  v1 (11-14) 7 族，外壳仍是 group_* 为主 —— 李工判"外壳多样性是假的"。
  v2 (11-15 上午) 剥掉 tsZ/tsQ/tsSc 外层 group 壳，但 gRank 仍在族内。
  v3 (11-15 12:55) 李工下令「最近 10 天禁止使用 group_rank」。本版把 gRank 移出
    轮换池，改为 11 族，其中 8 族不含任何 group_ 前缀算子。

为什么可以不用 group：
  平台 neutralization 设置本身就是横截面中性化（SUBINDUSTRY/INDUSTRY/MARKET），
  组合层已经做了去均值。表达式的横截面层不是必须再由 group_rank 承担。
  已实证：同核换外壳 S 变动仅 ±0.02（ENG_*_gRank/gZs/gSc 三连 2.29/2.28/2.27），
  换外壳是"相关性重掷"杠杆，不是"抬 S"杠杆。

族的分工（几何形状互不相同，不是换名字）：
  · 排名类（均匀分布）：rank / ts_rank / group_zscore(组内)
  · 标准化类（近似正态）：zscore / group_zscore / ts_zscore
  · 分位映射类（非线性压缩）：quantile / ts_quantile
  · 缩放类（有界）：scale / group_scale / ts_scale
  · 离散化类（丢信息换鲁棒）：bucket
  · 截尾类（削极值降换手）：winsorize / hump
  · 幂变换类（保号压缩）：signed_power
  · 中性化类（去组均值）：group_neutralize
"""
import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
from op_ban import is_banned

# (族名, 包装函数, 说明) —— 顺序即轮换顺序
FAMILIES = [
    # ---- 不含任何 group_ 前缀（8 族，主力）----
    ('rk',    lambda a: 'rank(%s)' % a,
     '全市场横截面均匀排名，无分组，输出 [-0.5,0.5] 天然防权重集中'),
    ('zs',    lambda a: 'zscore(%s)' % a,
     '全市场横截面标准化（正态），无分组'),
    ('qt',    lambda a: 'quantile(%s, driver="gaussian")' % a,
     '全市场分位→高斯映射，非线性压缩尾部'),
    ('tsRk',  lambda a: 'ts_rank(%s, 250)' % a,
     '纯时序排位：自己过去一年中的位置，完全不做横截面'),
    ('tsZs',  lambda a: 'ts_zscore(%s, 250)' % a,
     '纯时序 z：距自身 250 日均值几个标准差'),
    ('tsQt',  lambda a: 'ts_quantile(%s, 250)' % a,
     '纯滚动分位变换（11-14 实测同原子 SF 1.38 为族内最高）'),
    ('tsSc',  lambda a: 'ts_scale(%s, 250)' % a,
     '纯时序 0~1 缩放（语义换轴：自己在历史中的位置）'),
    ('sigP',  lambda a: 'signed_power(%s, 0.5)' % a,
     '保号开方：压缩极值但保留方向与量级'),
    # ---- 分组族，但都不是 group_rank（3 族）----
    ('gZs',   lambda a: 'group_zscore(%s, industry)' % a,
     '组内标准化（配方3 实证 corr 重掷 0.749→0.660）'),
    ('gSc',   lambda a: 'group_scale(%s, industry)' % a,
     '组内缩放到 0~1，跨组可比'),
    ('gNu',   lambda a: 'group_neutralize(%s, subindustry)' % a,
     '组内去均值（只扣行业均值，不重排）'),
    # ---- 离散化 / 截尾（2 族，主打降换手与防集中）----
    ('bkt',   lambda a: 'bucket(rank(%s), range="0,1,0.1")' % a,
     '十分位桶编号：只留 10 个取值，换手极低'),
    ('wz',    lambda a: 'winsorize(%s, std=4)' % a,
     '4σ 截尾：削掉极端值但不动中段排序'),
]

# 只降换手、不改信号方向的"后处理"族（可叠加在任一隔层外面）
POST = [
    ('hump', lambda a: 'hump(%s, hump=0.01)' % a,
     '变化小于阈值不动仓，直接砍换手'),
    ('jdec', lambda a: 'jump_decay(%s, 20)' % a,
     '跳跃后按 20 日衰减，平滑跳变'),
]


def _clean(expr):
    return [t for t in (is_banned(expr) or [])]


def wrap(atom_expr, fam_name):
    """原子表达式按族名包装；命中禁用算子返回 None。"""
    for name, fn, _note in FAMILIES:
        if name == fam_name:
            out = fn(atom_expr)
            return None if _clean(out) else out
    for name, fn, _note in POST:
        if name == fam_name:
            out = fn(atom_expr)
            return None if _clean(out) else out
    return None


def fam_names():
    return [f[0] for f in FAMILIES] + [f[0] for f in POST]


def audit():
    """自检：跑一个假原子，确认没有任何族产出禁用算子。"""
    bad = []
    for name, fn, _ in FAMILIES + POST:
        out = fn('X')
        if _clean(out):
            bad.append((name, out))
    return bad


if __name__ == '__main__':
    print('族数:', len(FAMILIES), '+ 后处理', len(POST))
    print('自检禁用算子:', audit() or '无')
    for n, f, _ in FAMILIES:
        print('%-7s %s' % (n, f('X')))
