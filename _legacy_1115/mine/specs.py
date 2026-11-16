# -*- coding: utf-8 -*-
"""specs.py —— 各挖矿批次的配方与生成逻辑（从 mine_wNNN_*.py 逐字搬迁，方法零改动）

每个 build_wNNN() 对应原批次脚本：独有配置（EXPR/MAINS/权重/过滤/配额）+ 枚举逻辑原样保留，
共享脚手架（认证/PnL拉取/日期对齐/落盘）统一调 src/core/combo_gen.py。
运行入口见 gen_combos.py。
"""
import sys, pathlib as _pl
_src = _pl.Path(__file__).resolve().parent.parent
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))
import csv, itertools, json, time
import numpy as np
from core import combo_gen as cg

cg.project_root()  # 切到项目根，相对路径才生效
import os  # NOTE: 原批次脚本的功能行 os.makedirs(PCACHE, exist_ok=True) 依赖 os，搬迁文件头未含故此处补导入


def build_w200():
    """w200 日内主导组合批生成器（2026-09-19 凌晨）
    背景诊断（见 .workbuddy/memory/2026-09-18.md 23:38 节）：
    - 共享腿（引擎+标准PV）权重占比 ≥35% 的组合，真实 corr 必然 0.8+
    - leg_lab 的 wp=2.0 会把组合推向 PV 主导 → 撞自己人
    - 本批设计：日内/隔夜几何主导（池子 86 条无一此几何）+ 引擎腿 0.5 + 零标准PV腿
    用法：python src/mine/mine_w200_intraday.py  → 落盘 _autologs/search_combos_w200.json
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        # 日内/隔夜族（主腿）
        'P_on5':  G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_int20': G_EXPR('-ts_rank(close/open - 1, 20)'),
        'P_vd':   G_EXPR('(close - vwap)/vwap'),
        # 引擎腿（降权 0.5，唯一共享源）
        'L_cfo':  G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        # 独有锚（0.75 辅助权）
        'L_xr':   G_EXPR('fnd6_xrent/assets'),
        'L_int':  G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':  G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc': G_EXPR('fnd6_intc/assets'),
        'M_g12':  G_EXPR('fnd6_newqv1300_glcea12/assets'),
        'M_debt': G_EXPR('debt_st/assets'),
        'M_tstk': G_EXPR('fnd6_tstkc/assets'),
        'M_accI': G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intI': G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq': G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['P_on5', 'P_int20', 'P_vd']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'

    ALIAS = {'P_int20': 'x180_leg_int'}

    # ---------- 池子：只认台账；拉取失败必须报警（leg_lab 静默丢成员的教训） ----------
    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('⚠️ 以上成员不在池内，pred 会漏掉与它们的碰撞（rY07MXgd 教训）')

    # ---------- 腿 PnL 装载 ----------
    load = cg.load_legs(MAINS + ANCHORS + [ENGINE], alias=ALIAS)
    legs = [l for l in MAINS + ANCHORS + [ENGINE] if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    # ---------- 枚举组合 ----------
    MIN_S = 2.2
    cands = []
    n_eval = 0
    for k in range(1, len(MAINS) + 1):
        for mains in itertools.combinations(MAINS, k):
            # 主腿权重：首腿 2.0 或 1.5，次腿 1.5 或 1.0，三腿 1.0
            wschemes = []
            if k == 1:
                wschemes = [(2.0,), (1.5,)]
            elif k == 2:
                wschemes = [(2.0, 1.5), (2.0, 1.0), (1.5, 1.0)]
            else:
                wschemes = [(2.0, 1.5, 1.0), (2.0, 1.0, 1.0), (1.5, 1.0, 1.0)]
            for mw in wschemes:
                for na in range(0, 3):
                    for extras in itertools.combinations(ANCHORS, na):
                        for eng in (True, False):
                            w = np.zeros(len(legs))
                            for l, wt in zip(mains, mw):
                                w[idx[l]] = wt
                            for x in extras:
                                w[idx[x]] = 0.75
                            if eng:
                                w[idx[ENGINE]] = 0.5
                            var = float(w @ G @ w)
                            if var <= 0:
                                continue
                            n_eval += 1
                            c = w @ Lraw
                            S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                            if S < MIN_S:
                                continue
                            cvec = (Mmat @ w) / (var ** .5)
                            mx = float(cvec.max())
                            tot = float(np.abs(w).sum())
                            shared = (0.5 if eng else 0.0) / tot
                            cands.append((S, mx, mains, mw, extras, eng, shared,
                                          pids[int(cvec.argmax())], w.copy()))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S≥{MIN_S} 的 {len(cands)} 条')

    # ---------- 选样：按主腿签名配额（每签名 ≤4 条），兄弟组合交给真实判决分高下 ----------
    TAKE = 24
    PER_SIG = 4
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (tuple(item[2]), item[5])  # mains + engine 开关
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} → {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, eng, shared, hit, w) in enumerate(keep):
        parts = []
        for l, wt in zip(mains, mw):
            parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
        for x in extras:
            parts.append(f'0.75*{EXPR[x]}')
        if eng:
            parts.append(f'0.5*{EXPR[ENGINE]}')
        expr = ' + '.join(parts)
        cid = f'w200_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                     'engine': eng, 'shared_frac': round(shared, 3)}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} shared={shared:.2f} 撞{hit} | {expr[:130]}')

    OUTP = '_autologs/search_combos_w200.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w201():
    """w201 日内轴扩展批（2026-09-19）
    - 新腿：P_int10/40/60（窗口）、P_int20I/C/V（换分组）——standalone S 1.67~2.02
    - 隔夜族（P_on*）standalone 为负，弃用
    - 选样约束：引擎共享占比 ≤0.10（w200 实测：shared=0 偏移 ±0.05，0.14 偏移 +0.1）
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G = lambda x: f'group_rank({x}, subindustry)'
    GI = lambda x: f'group_rank({x}, industry)'
    GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
    GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

    EXPR = {
        'P_int10': G('-ts_rank(close/open - 1, 10)'),
        'P_int20': G('-ts_rank(close/open - 1, 20)'),
        'P_int40': G('-ts_rank(close/open - 1, 40)'),
        'P_int60': G('-ts_rank(close/open - 1, 60)'),
        'P_int20I': GI('-ts_rank(close/open - 1, 20)'),
        'P_int20C': GC('-ts_rank(close/open - 1, 20)'),
        'P_int20V': GV('-ts_rank(close/open - 1, 20)'),
        # 隔夜/vwap 族：standalone S 为负，仅作低权去相关装饰腿
        'P_on5':  G('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_on10': G('-ts_mean(open/ts_delay(close,1) - 1, 10)'),
        'P_vd5':  G('ts_mean((close - vwap)/vwap, 5)'),
        'L_cfo':  G('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':   G('fnd6_xrent/assets'),
        'L_int':  G('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':  G('fn_accrued_liab_curr_a/assets'),
        'M_intc': G('fnd6_intc/assets'),
        'M_g12':  G('fnd6_newqv1300_glcea12/assets'),
        'M_debt': G('debt_st/assets'),
        'M_tstk': G('fnd6_tstkc/assets'),
        'M_accI': G('fn_accrued_liab_curr_a/assets'),
        'M_intI': G('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq': G('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['P_int10', 'P_int20', 'P_int40', 'P_int60', 'P_int20I', 'P_int20C', 'P_int20V']
    DECOR = ['P_on5', 'P_on10', 'P_vd5']  # 可选装饰腿 0.5 权
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 1.8
    MAX_SHARED = 0.10
    MAX_PRED = 0.66  # 共享≤0.10 区实测偏移 ±0.05 → pred≤0.66 才有 real≤0.685 的机会
    ALIAS = {'P_int20': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('⚠️ 以上成员不在池内，pred 会漏掉与它们的碰撞')

    load = cg.load_legs(MAINS + ANCHORS + [ENGINE] + DECOR, alias=ALIAS)
    legs = [l for l in MAINS + ANCHORS + [ENGINE] + DECOR if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    cands = []
    n_eval = 0
    for k in range(1, len(MAINS) + 1):
        for mains in itertools.combinations(MAINS, k):
            if k == 1:
                wschemes = [(2.0,), (1.5,)]
            elif k == 2:
                wschemes = [(2.0, 1.5), (2.0, 1.0), (1.5, 1.0)]
            else:
                wschemes = [(2.0, 1.5, 1.0), (1.5, 1.0, 1.0)]
            for mw in wschemes:
                for na in range(0, 3):
                    for extras in itertools.combinations(ANCHORS, na):
                        for eng in (True, False):
                            for nd in (0, 1, 2):
                                for decs in itertools.combinations(DECOR, nd):
                                    w = np.zeros(len(legs))
                                    for l, wt in zip(mains, mw):
                                        w[idx[l]] = wt
                                    for x in extras:
                                        w[idx[x]] = 0.75
                                    if eng:
                                        w[idx[ENGINE]] = 0.5
                                    for x in decs:
                                        w[idx[x]] = 0.5
                                    tot = float(np.abs(w).sum())
                                    shared = (0.5 if eng else 0.0) / tot
                                    if shared > MAX_SHARED:
                                        continue
                                    var = float(w @ Gm @ w)
                                    if var <= 0:
                                        continue
                                    n_eval += 1
                                    c = w @ Lraw
                                    S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                                    if S < MIN_S:
                                        continue
                                    cvec = (Mmat @ w) / (var ** .5)
                                    mx = float(cvec.max())
                                    if mx > MAX_PRED:
                                        continue
                                    cands.append((S, mx, mains, mw, extras, eng, shared,
                                                  pids[int(cvec.argmax())], w.copy(), decs))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S≥{MIN_S} 且 shared≤{MAX_SHARED} 且 pred≤{MAX_PRED} 的 {len(cands)} 条')

    TAKE = 16
    PER_SIG = 3
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (tuple(item[2]), item[5], item[9])
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} → {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, eng, shared, hit, w, decs) in enumerate(keep):
        parts = []
        for l, wt in zip(mains, mw):
            parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
        for x in extras:
            parts.append(f'0.75*{EXPR[x]}')
        if eng:
            parts.append(f'0.5*{EXPR[ENGINE]}')
        for x in decs:
            parts.append(f'0.5*{EXPR[x]}')
        expr = ' + '.join(parts)
        cid = f'w201_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                     'engine': eng, 'shared_frac': round(shared, 3), 'decor': list(decs)}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} shared={shared:.2f} 撞{hit} | {expr[:120]}')

    OUTP = '_autologs/search_combos_w201.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w203():
    """w203 低共享扩展批（2026-09-19）
    基于 w200/w201 框架：日内主腿 + 独有锚 + 共享占比 <=0.12 + pred<=0.65
    变化：权重网格铺全（主腿/锚/装饰腿多档），TAKE=20
    标定依据（w200 实测 8 条判决）：shared<=0.10 偏移 -0.03~+0.05，shared=0.14 偏移 +0.07~+0.11
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G = lambda x: f'group_rank({x}, subindustry)'
    GI = lambda x: f'group_rank({x}, industry)'
    GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
    GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

    EXPR = {
        'P_int10': G('-ts_rank(close/open - 1, 10)'),
        'P_int20': G('-ts_rank(close/open - 1, 20)'),
        'P_int40': G('-ts_rank(close/open - 1, 40)'),
        'P_int60': G('-ts_rank(close/open - 1, 60)'),
        'P_int20I': GI('-ts_rank(close/open - 1, 20)'),
        'P_int20C': GC('-ts_rank(close/open - 1, 20)'),
        'P_int20V': GV('-ts_rank(close/open - 1, 20)'),
        'P_on5':  G('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_on10': G('-ts_mean(open/ts_delay(close,1) - 1, 10)'),
        'P_vd5':  G('ts_mean((close - vwap)/vwap, 5)'),
        'L_cfo':  G('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':   G('fnd6_xrent/assets'),
        'L_int':  G('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':  G('fn_accrued_liab_curr_a/assets'),
        'M_intc': G('fnd6_intc/assets'),
        'M_g12':  G('fnd6_newqv1300_glcea12/assets'),
        'M_debt': G('debt_st/assets'),
        'M_tstk': G('fnd6_tstkc/assets'),
        'M_accI': G('fn_accrued_liab_curr_a/assets'),
        'M_intI': G('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq': G('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['P_int10', 'P_int20', 'P_int40', 'P_int60', 'P_int20I', 'P_int20C', 'P_int20V']
    DECOR = ['P_on5', 'P_on10', 'P_vd5']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 2.0
    MAX_SHARED = 0.12
    MAX_PRED = 0.65
    MAIN_W = [2.5, 2.0, 1.5, 1.25]
    ANCH_W = [1.0, 0.75, 0.5]
    DEC_W = [0.75, 0.5, 0.25]
    ALIAS = {'P_int20': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内，pred 会漏掉与它们的碰撞')

    load = cg.load_legs(MAINS + ANCHORS + [ENGINE] + DECOR, alias=ALIAS)
    legs = [l for l in MAINS + ANCHORS + [ENGINE] + DECOR if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    cands = []
    n_eval = 0
    for k in range(1, len(MAINS) + 1):
        for mains in itertools.combinations(MAINS, k):
            if k == 1:
                wschemes = [(w,) for w in MAIN_W]
            elif k == 2:
                wschemes = [(a, b) for a in MAIN_W for b in MAIN_W if a > b]
            else:
                wschemes = [(2.5, 1.5, 1.0), (2.0, 1.5, 1.0), (2.0, 1.0, 0.75)]
            for mw in wschemes:
                for na in range(0, 4):
                    for extras in itertools.combinations(ANCHORS, na):
                        for aw in ANCH_W[:1] if na < 2 else ANCH_W:
                            for eng in (True, False):
                                for nd in (0, 1, 2):
                                    for decs in itertools.combinations(DECOR, nd):
                                        for dw in DEC_W[:1] if nd < 2 else DEC_W:
                                            w = np.zeros(len(legs))
                                            for l, wt in zip(mains, mw):
                                                w[idx[l]] = wt
                                            for x in extras:
                                                w[idx[x]] = aw
                                            if eng:
                                                w[idx[ENGINE]] = 0.5
                                            for x in decs:
                                                w[idx[x]] = dw
                                            tot = float(np.abs(w).sum())
                                            shared = (0.5 if eng else 0.0) / tot
                                            if shared > MAX_SHARED:
                                                continue
                                            var = float(w @ Gm @ w)
                                            if var <= 0:
                                                continue
                                            n_eval += 1
                                            c = w @ Lraw
                                            S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                                            if S < MIN_S:
                                                continue
                                            cvec = (Mmat @ w) / (var ** .5)
                                            mx = float(cvec.max())
                                            if mx > MAX_PRED:
                                                continue
                                            cands.append((S, mx, mains, mw, extras, aw, eng,
                                                          shared, pids[int(cvec.argmax())],
                                                          w.copy(), decs, dw))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 shared<={MAX_SHARED} 且 pred<={MAX_PRED} 的 {len(cands)} 条')

    TAKE = 20
    PER_SIG = 4
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (tuple(item[2]), item[6], tuple(item[4]))
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, aw, eng, shared, hit, w, decs, dw) in enumerate(keep):
        parts = []
        for l, wt in zip(mains, mw):
            parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
        for x in extras:
            parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
        if eng:
            parts.append(f'0.5*{EXPR[ENGINE]}')
        for x in decs:
            parts.append(f'{dw}*{EXPR[x]}')
        expr = ' + '.join(parts)
        cid = f'w203_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                     'engine': eng, 'shared_frac': round(shared, 3), 'decor': list(decs)}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} shared={shared:.2f} hit={hit} | {expr[:110]}')

    OUTP = '_autologs/search_combos_w203.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w204():
    """w204 跨几何组合批（2026-09-19）
    主腿 P_int10 系（含换几何版）+ 换几何锚（industry/市值桶/波动率桶）。
    目标：与 zq8Xeo2R（P_int10+subindustry 锚）、3qXd5vg0（P_int20+subindustry 锚）去相关。
    标定：shared<=0.10 偏移 -0.03~+0.05 → pred<=0.65 才有 real<=0.685 机会。
    """
    # NOTE: 原文件 cid2id 为简化版（只直查 {cid}.json + _cid 扫描，不查 ALIAS；ALIAS 定义存在但未被 cid2id 使用），
    # 按搬迁规格统一改调 cg.cid2id，ALIAS 字典照原样保留（同样不被使用）。
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G = lambda x: f'group_rank({x}, subindustry)'
    GI = lambda x: f'group_rank({x}, industry)'
    GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
    GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

    EXPR = {
        'P_int10':  G('-ts_rank(close/open - 1, 10)'),
        'P_int5':   G('-ts_rank(close/open - 1, 5)'),
        'P_int15':  G('-ts_rank(close/open - 1, 15)'),
        'P_int30':  G('-ts_rank(close/open - 1, 30)'),
        'P_int10I': GI('-ts_rank(close/open - 1, 10)'),
        'P_int10C': GC('-ts_rank(close/open - 1, 10)'),
        'P_int10V': GV('-ts_rank(close/open - 1, 10)'),
        'A_xr_I':   GI('fnd6_xrent/assets'),
        'A_xr_C':   GC('fnd6_xrent/assets'),
        'A_xr_V':   GV('fnd6_xrent/assets'),
        'A_intc_I': GI('fnd6_intc/assets'),
        'A_intc_C': GC('fnd6_intc/assets'),
        'A_debt_I': GI('debt_st/assets'),
        'A_acc_I':  GI('fn_accrued_liab_curr_a/assets'),
        'A_int_I':  GI('-annual_intangible_assets_net_carrying_value/assets'),
        'A_lnoq_I': GI('fnd6_newqv1300_lnoq/assets'),
        'A_g12_I':  GI('fnd6_newqv1300_glcea12/assets'),
    }
    MAINS = ['P_int10', 'P_int5', 'P_int15', 'P_int30', 'P_int10I', 'P_int10C', 'P_int10V']
    ANCHORS = ['A_xr_I', 'A_xr_C', 'A_xr_V', 'A_intc_I', 'A_intc_C',
               'A_debt_I', 'A_acc_I', 'A_int_I', 'A_lnoq_I', 'A_g12_I']
    MIN_S = 2.0
    MAX_SHARED = 0.0    # 不带引擎腿/共享腿，全独有成分
    MAX_PRED = 0.65
    MAIN_W = [2.0, 1.5, 1.25]
    ANCH_W = [1.0, 0.75, 0.5]
    ALIAS = {'P_int10': 'w203leg_P_int10', 'P_int20': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内，pred 会漏掉与它们的碰撞')

    load = cg.load_legs(MAINS + ANCHORS, plain8=False)
    legs = [l for l in MAINS + ANCHORS if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    cands = []
    n_eval = 0
    for mains in MAINS:
        if mains not in load:
            continue
        for mw in MAIN_W:
            for na in range(2, 5):
                for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                    for aw in ANCH_W:
                        w = np.zeros(len(legs))
                        w[idx[mains]] = mw
                        for x in extras:
                            w[idx[x]] = aw
                        tot = float(np.abs(w).sum())
                        var = float(w @ Gm @ w)
                        if var <= 0:
                            continue
                        n_eval += 1
                        c = w @ Lraw
                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                        if S < MIN_S:
                            continue
                        cvec = (Mmat @ w) / (var ** .5)
                        mx = float(cvec.max())
                        if mx > MAX_PRED:
                            continue
                        cands.append((S, mx, mains, mw, extras, aw,
                                      pids[int(cvec.argmax())], w.copy()))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 shared=0 且 pred<={MAX_PRED} 的 {len(cands)} 条')

    TAKE = 16
    PER_SIG = 3
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (item[2], tuple(item[4]))
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, aw, hit, w) in enumerate(keep):
        parts = []
        parts.append(f'{mw}*{EXPR[mains]}' if mw != 1 else EXPR[mains])
        for x in extras:
            parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
        expr = ' + '.join(parts)
        cid = f'w204_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': [mains], 'anchors': list(extras),
                     'engine': False, 'shared_frac': 0}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} hit={hit} | {expr[:110]}')

    OUTP = '_autologs/search_combos_w204.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w205():
    """w205 严格档（2026-09-19）：w204 实测跨几何锚偏移 +0.08~+0.10 → MAX_PRED 压到 0.58。
    主腿改窗口/几何错开的双主腿（与 zq8Xeo2R=P_int10系、3qXd5vg0=P_int20 去相关）。
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G = lambda x: f'group_rank({x}, subindustry)'
    GI = lambda x: f'group_rank({x}, industry)'
    GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
    GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

    EXPR = {
        'P_int5':   G('-ts_rank(close/open - 1, 5)'),
        'P_int15':  G('-ts_rank(close/open - 1, 15)'),
        'P_int30':  G('-ts_rank(close/open - 1, 30)'),
        'P_int10I': GI('-ts_rank(close/open - 1, 10)'),
        'P_int10C': GC('-ts_rank(close/open - 1, 10)'),
        'P_int10V': GV('-ts_rank(close/open - 1, 10)'),
        'P_on5':    G('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_vd5':    G('ts_mean((close - vwap)/vwap, 5)'),
        'A_xr_I':   GI('fnd6_xrent/assets'),
        'A_xr_C':   GC('fnd6_xrent/assets'),
        'A_xr_V':   GV('fnd6_xrent/assets'),
        'A_intc_I': GI('fnd6_intc/assets'),
        'A_acc_I':  GI('fn_accrued_liab_curr_a/assets'),
        'A_int_I':  GI('-annual_intangible_assets_net_carrying_value/assets'),
        'L_xr':     G('fnd6_xrent/assets'),
        'L_int':    G('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':    G('fn_accrued_liab_curr_a/assets'),
        'M_intc':   G('fnd6_intc/assets'),
    }
    MAINS = ['P_int5', 'P_int15', 'P_int30', 'P_int10I', 'P_int10C', 'P_int10V', 'P_on5', 'P_vd5']
    ANCHORS = ['A_xr_I', 'A_xr_C', 'A_xr_V', 'A_intc_I', 'A_acc_I', 'A_int_I',
               'L_xr', 'L_int', 'L_acc', 'M_intc']
    MIN_S = 1.9
    MAX_PRED = 0.58
    MW_SCHEMES = [(1.5, 1.0), (1.25, 1.0), (1.0, 1.0), (1.5, 0.75), (2.0, 1.0)]
    ANCH_W = [0.75, 0.5]

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内')

    load = cg.load_legs(MAINS + ANCHORS, plain8=False)
    legs = [l for l in MAINS + ANCHORS if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    avail = [m for m in MAINS if m in load]
    cands = []
    n_eval = 0
    for mains in itertools.combinations(avail, 2):
        for mw in MW_SCHEMES:
            for na in range(2, 5):
                for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                    for aw in ANCH_W:
                        w = np.zeros(len(legs))
                        for l, wt in zip(mains, mw):
                            w[idx[l]] = wt
                        for x in extras:
                            w[idx[x]] = aw
                        var = float(w @ Gm @ w)
                        if var <= 0:
                            continue
                        n_eval += 1
                        c = w @ Lraw
                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                        if S < MIN_S:
                            continue
                        cvec = (Mmat @ w) / (var ** .5)
                        mx = float(cvec.max())
                        if mx > MAX_PRED:
                            continue
                        cands.append((S, mx, mains, mw, extras, aw,
                                      pids[int(cvec.argmax())], w.copy()))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 pred<={MAX_PRED} 的 {len(cands)} 条')

    TAKE = 16
    PER_SIG = 2
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (tuple(item[2]), tuple(item[4]))
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, aw, hit, w) in enumerate(keep):
        parts = []
        for l, wt in zip(mains, mw):
            parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
        for x in extras:
            parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
        expr = ' + '.join(parts)
        cid = f'w205_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                     'engine': False, 'shared_frac': 0}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} hit={hit} | {expr[:110]}')

    OUTP = '_autologs/search_combos_w205.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w206():
    """w206 精调批（2026-09-19）：w203 家族差 0.02~0.05 过墙（0.7021/0.7061/0.7096），
    质量富余 SF 4.2~4.6。用装饰腿 + 锚权重微调 + pred<=0.61 把 corr 压下 0.03。
    标定：P_int10+subindustry 锚偏移 +0.05~+0.08 → pred<=0.61 才有 real<=0.685。
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G = lambda x: f'group_rank({x}, subindustry)'
    GI = lambda x: f'group_rank({x}, industry)'
    GC = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
    GV = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'

    EXPR = {
        'P_int10': G('-ts_rank(close/open - 1, 10)'),
        'P_int5':  G('-ts_rank(close/open - 1, 5)'),
        'P_int15': G('-ts_rank(close/open - 1, 15)'),
        'P_on5':   G('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_on10':  G('-ts_mean(open/ts_delay(close,1) - 1, 10)'),
        'P_vd5':   G('ts_mean((close - vwap)/vwap, 5)'),
        'L_cfo':   G('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':    G('fnd6_xrent/assets'),
        'L_int':   G('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':   G('fn_accrued_liab_curr_a/assets'),
        'M_intc':  G('fnd6_intc/assets'),
        'M_g12':   G('fnd6_newqv1300_glcea12/assets'),
        'M_debt':  G('debt_st/assets'),
        'M_tstk':  G('fnd6_tstkc/assets'),
        'M_accI':  G('fn_accrued_liab_curr_a/assets'),
        'M_intI':  G('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq':  G('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['P_int10']
    DECOR = ['P_on5', 'P_on10', 'P_vd5']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 2.3
    MAX_SHARED = 0.12
    MAX_PRED = 0.61
    MAIN_W = [2.5, 2.0, 1.5, 1.25]
    ANCH_W = [1.0, 0.75, 0.6, 0.5]
    DEC_W = [0.5, 0.35, 0.25]
    ENG_W = [0.4, 0.3]
    ALIAS = {'P_int10': 'w203leg_P_int10', 'P_int20': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内')

    load = cg.load_legs(MAINS + ANCHORS + [ENGINE] + DECOR, alias=ALIAS)
    legs = [l for l in MAINS + ANCHORS + [ENGINE] + DECOR if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    cands = []
    n_eval = 0
    for mw in MAIN_W:
        for na in range(1, 4):
            for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                for aw in ANCH_W:
                    for eng in (True, False):
                        for ew in (ENG_W if eng else [0]):
                            for nd in (0, 1, 2):
                                for decs in itertools.combinations([d for d in DECOR if d in load], nd):
                                    for dw in (DEC_W if nd else [0]):
                                        w = np.zeros(len(legs))
                                        w[idx['P_int10']] = mw
                                        for x in extras:
                                            w[idx[x]] = aw
                                        if eng:
                                            w[idx[ENGINE]] = ew
                                        for x in decs:
                                            w[idx[x]] = dw
                                        tot = float(np.abs(w).sum())
                                        shared = (ew if eng else 0.0) / tot
                                        if shared > MAX_SHARED:
                                            continue
                                        var = float(w @ Gm @ w)
                                        if var <= 0:
                                            continue
                                        n_eval += 1
                                        c = w @ Lraw
                                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                                        if S < MIN_S:
                                            continue
                                        cvec = (Mmat @ w) / (var ** .5)
                                        mx = float(cvec.max())
                                        if mx > MAX_PRED:
                                            continue
                                        cands.append((S, mx, mw, extras, aw, eng, ew,
                                                      shared, pids[int(cvec.argmax())],
                                                      w.copy(), decs, dw))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 shared<={MAX_SHARED} 且 pred<={MAX_PRED} 的 {len(cands)} 条')

    TAKE = 16
    PER_SIG = 3
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (item[2], tuple(item[3]), item[5], tuple(item[10]))
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mw, extras, aw, eng, ew, shared, hit, w, decs, dw) in enumerate(keep):
        parts = []
        parts.append(f'{mw}*{EXPR["P_int10"]}' if mw != 1 else EXPR['P_int10'])
        for x in extras:
            parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
        if eng:
            parts.append(f'{ew}*{EXPR[ENGINE]}')
        for x in decs:
            parts.append(f'{dw}*{EXPR[x]}')
        expr = ' + '.join(parts)
        cid = f'w206_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': ['P_int10'], 'anchors': list(extras),
                     'engine': eng, 'shared_frac': round(shared, 3), 'decor': list(decs)}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} shared={shared:.2f} hit={hit} | {expr[:110]}')

    OUTP = '_autologs/search_combos_w206.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w208():
    """w208 未开采主腿批（2026-09-19）：w200 的 2016 组合里 P_on5/P_vd 主腿从未被模拟（配额被 P_int20 占满）。
    新约束（本周实测标定）：主腿占比 <=0.45（占比高 → 偏移失控，w206 教训）、pred<=0.63。
    """
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        'P_on5':  G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
        'P_on20': G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 20)'),
        'P_vd':   G_EXPR('(close - vwap)/vwap'),
        'P_vd5':  G_EXPR('ts_mean((close - vwap)/vwap, 5)'),
        'P_int20': G_EXPR('-ts_rank(close/open - 1, 20)'),
        'L_cfo':  G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':   G_EXPR('fnd6_xrent/assets'),
        'L_int':  G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':  G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc': G_EXPR('fnd6_intc/assets'),
        'M_g12':  G_EXPR('fnd6_newqv1300_glcea12/assets'),
        'M_debt': G_EXPR('debt_st/assets'),
        'M_tstk': G_EXPR('fnd6_tstkc/assets'),
        'M_accI': G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intI': G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq': G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['P_on5', 'P_on20', 'P_vd', 'P_vd5', 'P_int20']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 2.0
    MAX_MAIN_FRAC = 0.45
    MAX_SHARED = 0.12
    MAX_PRED = 0.63
    ALIAS = {'P_int20': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内')

    load = cg.load_legs(MAINS + ANCHORS + [ENGINE], alias=ALIAS)
    legs = [l for l in MAINS + ANCHORS + [ENGINE] if l in load]
    print(f'腿库 {len(legs)}: {" ".join(legs)}')

    M = cg.align_dates(pool, load)
    dates, T, legs, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    avail = [m for m in MAINS if m in load]
    cands = []
    n_eval = 0
    for k in range(1, 3):
        for mains in itertools.combinations(avail, k):
            if k == 1:
                wschemes = [(2.0,), (1.5,)]
            else:
                wschemes = [(1.5, 1.0), (1.5, 1.5), (2.0, 1.0)]
            for mw in wschemes:
                for na in range(1, 4):
                    for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                        for aw in (0.75, 0.5):
                            for eng in (True, False):
                                w = np.zeros(len(legs))
                                for l, wt in zip(mains, mw):
                                    w[idx[l]] = wt
                                for x in extras:
                                    w[idx[x]] = aw
                                ew = 0.5 if eng else 0.0
                                if eng:
                                    w[idx[ENGINE]] = ew
                                tot = float(np.abs(w).sum())
                                main_frac = mw[0] / tot
                                if main_frac > MAX_MAIN_FRAC:
                                    continue
                                shared = ew / tot
                                if shared > MAX_SHARED:
                                    continue
                                var = float(w @ Gm @ w)
                                if var <= 0:
                                    continue
                                n_eval += 1
                                c = w @ Lraw
                                S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                                if S < MIN_S:
                                    continue
                                cvec = (Mmat @ w) / (var ** .5)
                                mx = float(cvec.max())
                                if mx > MAX_PRED:
                                    continue
                                cands.append((S, mx, mains, mw, extras, aw, eng,
                                              main_frac, shared, pids[int(cvec.argmax())], w.copy()))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 main_frac<={MAX_MAIN_FRAC} 且 pred<={MAX_PRED} 的 {len(cands)} 条')

    TAKE = 12
    PER_SIG = 3
    keep = []
    sig_cnt = {}
    for item in cands:
        sig = (tuple(item[2]), item[6])
        if sig_cnt.get(sig, 0) >= PER_SIG:
            continue
        keep.append(item)
        sig_cnt[sig] = sig_cnt.get(sig, 0) + 1
        if len(keep) >= TAKE:
            break
    print(f'配额选样：{len(cands)} -> {len(keep)} 条（签名 {len(sig_cnt)} 个）')

    COMB = {}
    for i, (S, mx, mains, mw, extras, aw, eng, mfrac, shared, hit, w) in enumerate(keep):
        parts = []
        for l, wt in zip(mains, mw):
            parts.append(f'{wt}*{EXPR[l]}' if wt != 1 else EXPR[l])
        for x in extras:
            parts.append(f'{aw}*{EXPR[x]}' if aw != 1 else EXPR[x])
        if eng:
            parts.append(f'0.5*{EXPR[ENGINE]}')
        expr = ' + '.join(parts)
        cid = f'w208_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'mains': list(mains), 'anchors': list(extras),
                     'engine': eng, 'shared_frac': round(shared, 3), 'main_frac': round(mfrac, 3)}
        print(f'  {cid} S={S:.2f} maxcorr={mx:.3f} mainf={mfrac:.2f} shared={shared:.2f} hit={hit} | {expr[:110]}')

    OUTP = '_autologs/search_combos_w208.json'
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w210():
    """w210 离线拼装（2026-09-19）：社区灵感三帖的 17 条事件时点/热度交互腿 + 独有锚。
    输出：离线组合 S 与 pred corr；MIN_S=1.5（腿弱，先看上限在哪）。
    """
    # NOTE: 偏离标准模式——原文件腿装载用 noleg 收集缺失（非逐条 WARN），腿序变量叫 names（= list(load)），
    # 无 legs 过滤行；循环原样保留（仅 cid2id/get_pnl 改调 cg），names 绑定 M['legs']（同序）。
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        'argmin60':    G_EXPR('ts_arg_min(returns, 60)'),
        'argmin20':    G_EXPR('ts_arg_min(returns, 20)'),
        'argshort10':  G_EXPR('-ts_arg_min(returns, 10)'),
        'argmaxvol20': G_EXPR('ts_arg_max(volume, 20)'),
        'heat_c_pv10': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_corr(rank(close), rank(volume), 10))'),
        'heat_c_rv10': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_corr(rank(returns), rank(volume), 10))'),
        'heat_c_dcv5': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_corr(rank(ts_delta(close, 2)), rank(volume), 5))'),
        'heat_volrev': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_delta(volume, 5))'),
        'heat_tailvol':G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_std_dev(returns, 10))'),
        'argmin60s':   G_EXPR('ts_arg_min(ts_mean(returns, 5), 60)'),
        'argmin_d5':   G_EXPR('ts_arg_min(ts_delta(close, 5), 60)'),
        'heat_argmin': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_arg_min(returns, 10))'),
        'heat_argmin60':G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * ts_arg_min(returns, 60)'),
        'heat_argmaxret':G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_arg_max(returns, 20))'),
        'heat_c_pv20': G_EXPR('rank(ts_zscore(ts_sum(volume, 20), 252)) * (-ts_corr(rank(close), rank(volume), 20))'),
        'heat60_c_pv10':G_EXPR('rank(ts_zscore(ts_sum(volume, 60), 252)) * (-ts_corr(rank(close), rank(volume), 10))'),
        'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':        G_EXPR('fnd6_xrent/assets'),
        'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc':      G_EXPR('fnd6_intc/assets'),
        'M_g12':       G_EXPR('fnd6_newqv1300_glcea12/assets'),
        'M_debt':      G_EXPR('debt_st/assets'),
        'M_tstk':      G_EXPR('fnd6_tstkc/assets'),
        'M_accI':      G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intI':      G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['argmin60', 'argmin20', 'argshort10', 'argmaxvol20', 'heat_c_pv10', 'heat_c_rv10',
             'heat_c_dcv5', 'heat_volrev', 'heat_tailvol', 'argmin60s', 'argmin_d5',
             'heat_argmin', 'heat_argmin60', 'heat_argmaxret', 'heat_c_pv20', 'heat60_c_pv10']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 1.5
    MAX_MAIN_FRAC = 0.45
    MAX_SHARED = 0.12
    MAX_PRED = 0.63
    LEG_CID = {k: f'w210leg_{k}' for k in EXPR if k not in ('L_cfo','L_xr','L_int','L_acc','M_intc','M_g12','M_debt','M_tstk','M_accI','M_intI','M_lnoq')}
    LEG_CID.update({'argmin60s': 'w210b_argmin60s', 'argmin_d5': 'w210b_argmin_d5',
                    'heat_argmin': 'w210b_heat_argmin', 'heat_argmin60': 'w210b_heat_argmin60',
                    'heat_argmaxret': 'w210b_heat_argmaxret', 'heat_c_pv20': 'w210b_heat_c_pv20',
                    'heat60_c_pv10': 'w210b_heat60_c_pv10'})
    ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_xr': 'x180_leg_xr', 'L_int': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内')

    load = {}
    noleg = []
    for l in MAINS + ANCHORS + [ENGINE]:
        aid = cg.cid2id(l, extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False)
        if not aid:
            noleg.append(l); continue
        p = cg.get_pnl(aid)
        if not p:
            noleg.append(l); continue
        load[l] = p
    print(f'腿库 {len(load)}/{len(MAINS+ANCHORS+[ENGINE])}；缺: {noleg}')

    M = cg.align_dates(pool, load)
    dates, T, names, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    # 每条主腿单独 vs 池子的最大 corr（回答"池子里有没有这个几何"）
    print('--- 单腿 vs 池子 max corr ---')
    for m in MAINS:
        if m not in idx:
            continue
        cs = Mmat[:, idx[m]] / (Lraw[idx[m]].std(ddof=1) + 1e-12)
        print(f'  {m}: maxcorr={cs.max():.3f} hit={pids[int(cs.argmax())]}')

    avail = [m for m in MAINS if m in load]
    cands = []
    n_eval = 0
    for m in avail:
        for mw in (2.0, 1.5):
            for na in range(1, 4):
                for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                    for aw in (0.75, 0.5):
                        for eng_w in (0.5, 0.25, 0.0):
                            w = np.zeros(len(names))
                            w[idx[m]] = mw
                            for x in extras:
                                w[idx[x]] = aw
                            if eng_w > 0:
                                w[idx[ENGINE]] = eng_w
                            tot = float(np.abs(w).sum())
                            main_frac = mw / tot
                            if main_frac > MAX_MAIN_FRAC:
                                continue
                            shared = eng_w / tot
                            if shared > MAX_SHARED:
                                continue
                            var = float(w @ Gm @ w)
                            if var <= 0:
                                continue
                            n_eval += 1
                            c = w @ Lraw
                            S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                            if S < MIN_S:
                                continue
                            cvec = (Mmat @ w) / (var ** .5)
                            mx = float(cvec.max())
                            if mx > MAX_PRED:
                                continue
                            cands.append((S, mx, m, mw, extras, aw, eng_w,
                                          main_frac, shared, pids[int(cvec.argmax())]))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 main_frac<={MAX_MAIN_FRAC} 且 pred<={MAX_PRED} 的 {len(cands)} 条')
    for S, mx, m, mw, extras, aw, eng, mf, sh, hit in cands[:20]:
        print(f'  S={S:.2f} maxcorr={mx:.3f} main={m}({mw}) anchors={extras}(w{aw}) eng={eng} mainf={mf:.2f} hit={hit}')

    OUTP = '_autologs/search_combos_w210v2.json'
    COMB = {}
    for i, (S, mx, m, mw, extras, aw, eng, mf, sh, hit) in enumerate(cands[:20]):
        parts = [f'{mw}*{EXPR[m]}'] + [f'{aw}*{EXPR[x]}' for x in extras]
        if eng > 0:
            parts.append(f'{eng}*{EXPR[ENGINE]}')
        COMB[f'w211_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3), 'maxcorr': round(mx, 4)}
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w213():
    """w213 离线拼装（2026-09-20）：事件条件化 argmin 腿（帖 1 原意：回撤超阈值才发信号）。
    框架同 mine_w210_assemble.py：主腿 + 独有锚 + 引擎（0.5/0.25/0），主腿占比≤0.45、shared≤0.12、pred≤0.63。
    """
    # NOTE: 偏离标准模式——同 build_w210：noleg 收集缺失、腿序变量叫 names（= list(load)），循环原样保留（仅改调 cg）。
    MINED, PCACHE, LEDGER = cg.MINED, cg.PCACHE, cg.LEDGER
    os.makedirs(PCACHE, exist_ok=True)

    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        'ev60a':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 60)'),
        'ev60b':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 0)'),
        'ev60nb':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0)'),
        'ev60db':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.15, ts_arg_min(returns, 60), 0)'),
        'ev120b':  G_EXPR('if_else(close/ts_delay(close, 120) - 1 < -0.15, ts_arg_min(returns, 120), 0)'),
        'ev20b':   G_EXPR('if_else(close/ts_delay(close, 20) - 1 < -0.07, ts_arg_min(returns, 20), 0)'),
        'evsum10': G_EXPR('if_else(ts_sum(returns, 10) < -0.10, -ts_arg_min(returns, 10), 0)'),
        'evh60a':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0)'),
        'evh60b':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, ts_arg_max(returns, 60), 0)'),
        'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':        G_EXPR('fnd6_xrent/assets'),
        'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc':      G_EXPR('fnd6_intc/assets'),
        'M_g12':       G_EXPR('fnd6_newqv1300_glcea12/assets'),
        'M_debt':      G_EXPR('debt_st/assets'),
        'M_tstk':      G_EXPR('fnd6_tstkc/assets'),
        'M_accI':      G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intI':      G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    MAINS = ['ev60a', 'ev60b', 'ev60nb', 'ev60db', 'ev120b', 'ev20b', 'evsum10', 'evh60a', 'evh60b']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = float(os.environ.get('W213_MIN_S', '1.5'))
    MAX_MAIN_FRAC = 0.45
    MAX_SHARED = 0.12
    MAX_PRED = 0.63
    LEG_CID = {k: f'w213leg_{k}' for k in MAINS}
    ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_xr': 'x180_leg_xr', 'L_int': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')
    if missing:
        print('WARN 以上成员不在池内')

    load = {}
    noleg = []
    for l in MAINS + ANCHORS + [ENGINE]:
        aid = cg.cid2id(l, extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False)
        if not aid:
            noleg.append(l); continue
        p = cg.get_pnl(aid)
        if not p:
            noleg.append(l); continue
        load[l] = p
    print(f'腿库 {len(load)}/{len(MAINS+ANCHORS+[ENGINE])}；缺: {noleg}')

    M = cg.align_dates(pool, load)
    dates, T, names, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    print('--- 单腿 vs 池子 max corr ---')
    for m in MAINS:
        if m not in idx:
            continue
        cs = Mmat[:, idx[m]] / (Lraw[idx[m]].std(ddof=1) + 1e-12)
        print(f'  {m}: maxcorr={cs.max():.3f} hit={pids[int(cs.argmax())]}')

    avail = [m for m in MAINS if m in load]
    cands = []
    n_eval = 0
    for m in avail:
        for mw in (2.0, 1.5):
            for na in range(1, 4):
                for extras in itertools.combinations([a for a in ANCHORS if a in load], na):
                    for aw in (0.75, 0.5):
                        for eng_w in (0.5, 0.25, 0.0):
                            w = np.zeros(len(names))
                            w[idx[m]] = mw
                            for x in extras:
                                w[idx[x]] = aw
                            if eng_w > 0:
                                w[idx[ENGINE]] = eng_w
                            tot = float(np.abs(w).sum())
                            main_frac = mw / tot
                            if main_frac > MAX_MAIN_FRAC:
                                continue
                            shared = eng_w / tot
                            if shared > MAX_SHARED:
                                continue
                            var = float(w @ Gm @ w)
                            if var <= 0:
                                continue
                            n_eval += 1
                            c = w @ Lraw
                            S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                            if S < MIN_S:
                                continue
                            cvec = (Mmat @ w) / (var ** .5)
                            mx = float(cvec.max())
                            if mx > MAX_PRED:
                                continue
                            cands.append((S, mx, m, mw, extras, aw, eng_w,
                                          main_frac, shared, pids[int(cvec.argmax())]))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 main_frac<={MAX_MAIN_FRAC} 且 pred<={MAX_PRED} 的 {len(cands)} 条')
    for S, mx, m, mw, extras, aw, eng, mf, sh, hit in cands[:20]:
        print(f'  S={S:.2f} maxcorr={mx:.3f} main={m}({mw}) anchors={extras}(w{aw}) eng={eng} mainf={mf:.2f} hit={hit}')

    OUTP = '_autologs/search_combos_w213.json'
    COMB = {}
    for i, (S, mx, m, mw, extras, aw, eng, mf, sh, hit) in enumerate(cands[:20]):
        parts = [f'{mw}*{EXPR[m]}'] + [f'{aw}*{EXPR[x]}' for x in extras]
        if eng > 0:
            parts.append(f'{eng}*{EXPR[ENGINE]}')
        COMB[f'w213_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3), 'maxcorr': round(mx, 4)}
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w213b():
    """w213b 混合拼装（2026-09-20）：已验证主腿 -ts_arg_min(returns,10)@2.0 + 事件条件化腿（去相关佐腿）
    + 0~1 独有锚 + 引擎@0.5。目标：把 w210 的 miss（corr 0.6968~0.7359）压回 0.685 内同时保 SF>=4.0。
    约束：离线 S>=2.2，pred<=0.58（标定偏移 +0.07~0.12 → 预期 real 0.65~0.70）。
    """
    # NOTE: 偏离标准模式——原文件无 os.makedirs；腿装载用 noleg 收集且随后 assert not noleg；
    # 腿序变量叫 names（= list(load)），并额外绑定 i_main/i_eng；均原样保留（仅 cid2id/get_pnl 改调 cg）。
    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        'argshort10': G_EXPR('-ts_arg_min(returns, 10)'),
        'ev60a':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 60)'),
        'ev60b':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 0)'),
        'ev60nb':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0)'),
        'ev60db':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.15, ts_arg_min(returns, 60), 0)'),
        'ev120b':  G_EXPR('if_else(close/ts_delay(close, 120) - 1 < -0.15, ts_arg_min(returns, 120), 0)'),
        'ev20b':   G_EXPR('if_else(close/ts_delay(close, 20) - 1 < -0.07, ts_arg_min(returns, 20), 0)'),
        'evsum10': G_EXPR('if_else(ts_sum(returns, 10) < -0.10, -ts_arg_min(returns, 10), 0)'),
        'evh60a':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0)'),
        'evh60b':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, ts_arg_max(returns, 60), 0)'),
        'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_xr':        G_EXPR('fnd6_xrent/assets'),
        'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc':      G_EXPR('fnd6_intc/assets'),
        'M_g12':       G_EXPR('fnd6_newqv1300_glcea12/assets'),
        'M_debt':      G_EXPR('debt_st/assets'),
        'M_tstk':      G_EXPR('fnd6_tstkc/assets'),
        'M_accI':      G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intI':      G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    MAIN = 'argshort10'
    EVENTS = ['ev60a', 'ev60b', 'ev60nb', 'ev60db', 'ev120b', 'ev20b', 'evsum10', 'evh60a', 'evh60b']
    ANCHORS = ['L_xr', 'L_int', 'L_acc', 'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_lnoq']
    ENGINE = 'L_cfo'
    MIN_S = 2.05
    MAX_PRED = 0.60
    LEG_CID = {k: f'w213leg_{k}' for k in EVENTS}
    LEG_CID['argshort10'] = 'w210leg_argshort10'
    ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_xr': 'x180_leg_xr', 'L_int': 'x180_leg_int'}

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')

    load = {}
    noleg = []
    for l in [MAIN] + EVENTS + ANCHORS + [ENGINE]:
        aid = cg.cid2id(l, extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False)
        if not aid:
            noleg.append(l); continue
        p = cg.get_pnl(aid)
        if not p:
            noleg.append(l); continue
        load[l] = p
    print(f'腿库 {len(load)}/{21+len(ANCHORS)}；缺: {noleg}')
    assert not noleg, noleg

    M = cg.align_dates(pool, load)
    dates, T, names, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')
    i_main = idx[MAIN]; i_eng = idx[ENGINE]

    # 佐腿与主腿/池子的相关性画像
    print('--- 事件腿画像（vs 主腿 corr / vs 池子 maxcorr） ---')
    lv = Lraw[i_main] / (Lraw[i_main].std(ddof=1) + 1e-12)
    for e in EVENTS:
        i = idx[e]
        c_main = float(np.dot(Lraw[i], Lraw[i_main]) / T / (Lraw[i].std(ddof=1) * Lraw[i_main].std(ddof=1) + 1e-12))
        cs = Mmat[:, i] / (Lraw[i].std(ddof=1) + 1e-12)
        print(f'  {e}: corr(main)={c_main:+.3f} maxcorr(pool)={cs.max():.3f}')

    cands = []
    n_eval = 0
    for ne in (1, 2):
        for evs in itertools.combinations(EVENTS, ne):
            for ew in (0.5, 0.75, 1.0):
                for na in (0, 1):
                    for anc in itertools.combinations([a for a in ANCHORS if a in load], na):
                        w = np.zeros(len(names))
                        w[i_main] = 2.0
                        for e in evs:
                            w[idx[e]] = ew
                        for a in anc:
                            w[idx[a]] = 0.75
                        w[i_eng] = 0.5
                        tot = float(np.abs(w).sum())
                        shared = 0.5 / tot
                        if shared > 0.13:
                            continue
                        var = float(w @ Gm @ w)
                        if var <= 0:
                            continue
                        n_eval += 1
                        c = w @ Lraw
                        S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                        if S < MIN_S:
                            continue
                        cvec = (Mmat @ w) / (var ** .5)
                        mx = float(cvec.max())
                        if mx > MAX_PRED:
                            continue
                        cands.append((S, mx, evs, ew, anc, shared, pids[int(cvec.argmax())]))

    cands.sort(key=lambda t: (-t[0], t[1]))
    print(f'评估 {n_eval}，S>={MIN_S} 且 pred<={MAX_PRED} 的 {len(cands)} 条')
    for S, mx, evs, ew, anc, sh, hit in cands[:20]:
        print(f'  S={S:.2f} pred={mx:.3f} ev={evs}(w{ew}) anc={anc} shared={sh:.3f} hit={hit}')

    OUTP = '_autologs/search_combos_w213b.json'
    COMB = {}
    for i, (S, mx, evs, ew, anc, sh, hit) in enumerate(cands[:20]):
        parts = [f'2.0*{EXPR[MAIN]}'] + [f'{ew}*{EXPR[e]}' for e in evs] + \
                [f'0.75*{EXPR[a]}' for a in anc] + [f'0.5*{EXPR[ENGINE]}']
        COMB[f'w213b_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3), 'maxcorr': round(mx, 4)}
    cg.dump_combos(COMB, OUTP)
    return COMB


def build_w213c():
    """w213c 加挂拼装（2026-09-20）：w210 已验证达标结构（2.0 主腿 + 双基本面锚 + 0.5 引擎）不动，
    第 5 条腿加挂事件条件化腿（0.5/0.75），目标：corr 0.6968~0.7359 → <0.685，SF 保 4.0+。
    """
    # NOTE: 偏离标准模式——原文件无 os.makedirs；腿列表由 need = ['argshort10'] + EVENTS + list(EXPR)[5:] 构成，
    # 装载用 noleg 收集且随后 assert not noleg；腿序变量叫 names（= list(load)）；无配额选样，直接全量 rows 落盘。
    # 均原样保留（仅 cid2id/get_pnl 改调 cg）。
    G_EXPR = lambda x: f'group_rank({x}, subindustry)'

    EXPR = {
        'argshort10': G_EXPR('-ts_arg_min(returns, 10)'),
        'ev60a':   G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.10, ts_arg_min(returns, 60), 60)'),
        'ev60nb':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 < -0.07, ts_arg_min(returns, 60), 0)'),
        'evh60a':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, -ts_arg_max(returns, 60), 0)'),
        'evh60b':  G_EXPR('if_else(close/ts_delay(close, 60) - 1 > 0.10, ts_arg_max(returns, 60), 0)'),
        'L_cfo':       G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
        'L_int':       G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
        'L_acc':       G_EXPR('fn_accrued_liab_curr_a/assets'),
        'M_intc':      G_EXPR('fnd6_intc/assets'),
        'M_lnoq':      G_EXPR('fnd6_newqv1300_lnoq/assets'),
    }
    # w210 达标结构的锚权重（实测）
    STRUCTS = {
        'A_E5pYLQPL': {'L_int': 1.5, 'M_intc': 0.75},
        'B_0mX95n5p': {'L_acc': 0.75, 'L_int': 0.75, 'M_lnoq': 0.75},
        'C_YPbnYzol': {'L_int': 1.5, 'M_lnoq': 0.75},
    }
    EVENTS = ['ev60a', 'ev60nb', 'evh60a', 'evh60b']
    EWS = (0.75, 0.5)
    LEG_CID = {'ev60a': 'w213leg_ev60a', 'ev60nb': 'w213leg_ev60nb',
               'evh60a': 'w213leg_evh60a', 'evh60b': 'w213leg_evh60b',
               'argshort10': 'w210leg_argshort10'}
    ALIAS = {'L_cfo': 'x180_leg_cfo', 'L_int': 'x180_leg_int', 'L_acc': 'x180_leg_acc',
             'M_intc': None, 'M_lnoq': None}

    need = ['argshort10'] + EVENTS + list(EXPR)[5:]

    pool, missing = cg.load_pool()
    print(f'池子 {len(pool)} 条；拉取失败 {len(missing)} 条: {missing}')

    load = {}
    noleg = []
    for l in need:
        aid = cg.cid2id(l, extra=(LEG_CID.get(l), ALIAS.get(l)), plain8=False)
        if not aid:
            noleg.append(l); continue
        p = cg.get_pnl(aid)
        if not p:
            noleg.append(l); continue
        load[l] = p
    print(f'腿库 {len(load)}/{len(need)}；缺: {noleg}')
    assert not noleg, noleg

    M = cg.align_dates(pool, load)
    dates, T, names, Lraw = M['dates'], M['T'], M['legs'], M['Lraw']
    Mmat, idx, pids = M['Mmat'], M['idx'], M['pids']
    G = Gm = M['Gm']  # 两个名字都绑定，原文件用哪个都能跑
    print(f'对齐日期 {T} 天')

    rows = []
    for sname, anchors in STRUCTS.items():
        for ev in EVENTS:
            if ev not in idx:
                continue
            for ew in EWS:
                w = np.zeros(len(names))
                w[idx['argshort10']] = 2.0
                for a, aw in anchors.items():
                    w[idx[a]] += aw
                w[idx[ev]] = ew
                w[idx['L_cfo']] = 0.5
                tot = float(np.abs(w).sum())
                var = float(w @ Gm @ w)
                if var <= 0:
                    continue
                c = w @ Lraw
                S = float(c.mean() / c.std(ddof=1) * (252 ** .5))
                cvec = (Mmat @ w) / (var ** .5)
                mx = float(cvec.max())
                hit = pids[int(cvec.argmax())]
                rows.append((S, mx, sname, ev, ew, hit, tot))
                print(f'  {sname} +{ev}(w{ew}): S={S:.2f} pred={mx:.3f} hit={hit}')

    rows.sort(key=lambda r: (-r[0], r[1]))
    OUTP = '_autologs/search_combos_w213c.json'
    COMB = {}
    for i, (S, mx, sname, ev, ew, hit, tot) in enumerate(rows):
        parts = [f'2.0*{EXPR["argshort10"]}']
        for a, aw in STRUCTS[sname].items():
            parts.append(f'{aw}*{EXPR[a]}')
        parts.append(f'{ew}*{EXPR[ev]}')
        parts.append(f'0.5*{EXPR["L_cfo"]}')
        COMB[f'w213c_{i:02d}'] = {'expr': ' + '.join(parts), 'S': round(S, 3),
                                  'maxcorr': round(mx, 4), 'struct': sname, 'ev': ev, 'ew': ew}
    cg.dump_combos(COMB, OUTP)
    return COMB
