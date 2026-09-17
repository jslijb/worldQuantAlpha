# -*- coding: utf-8 -*-
"""leg_lab.py —— 腿库离线拼装实验室（不发提交、不跑模拟）

原理：BRAIN alpha 的信号 = Σ w_i · group_rank(leg_i)，再经 subindustry 去均值 + decay + trunc。
      去均值与 decay 都是【线性】算子，trunc 只削尾部 → PnL 近似线性：
          PnL(Σ w_i·leg_i) ≈ Σ w_i · PnL(leg_i)
      Sharpe 与相关系数都对尺度不变 → 可以离线拼装任意权重组合，算出 S 与 max corr，
      只把最有希望的几条拿去真跑模拟。筛选成本归零。

用法：
  python src/analysis/leg_lab.py check <cid...>            # 验证线性：预测 vs 实测
  python src/analysis/leg_lab.py eval "L_pst:1.5, L_txs:1, P_tr20:1.5"
  python src/analysis/leg_lab.py search                     # 在腿库里网格搜索低相关高 Sharpe 组合
  python src/analysis/leg_lab.py search --min-s 2.1 --max-corr 0.67
"""
import os as _os, pathlib as _pl, sys, json, csv, itertools, random

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

import requests

MINED = 'data/alpha_quality_analysis/mined'
PCACHE = 'data/alpha_quality_analysis/pnl'
LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
_os.makedirs(PCACHE, exist_ok=True)

ARGS = [a for a in sys.argv[1:]]

G_EXPR = lambda x: f'group_rank({x}, subindustry)'
G_EXPR_I = lambda x: f'group_rank({x}, industry)'
G_EXPR_S = lambda x: f'group_rank({x}, sector)'
G_EXPR_C = lambda x: f'group_rank({x}, bucket(rank(cap), range="0.1, 1, 0.1"))'
G_EXPR_V = lambda x: f'group_rank({x}, bucket(rank(ts_std_dev(returns, 60)), range="0.1, 1, 0.1"))'
G_EXPR_L = lambda x: f'group_rank({x}, bucket(rank(volume), range="0.1, 1, 0.1"))'


def sess():
    s = requests.Session()
    s.auth = tuple(json.load(open('brain_credentials.txt')))
    assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201
    return s


_S = None


def get_pnl(aid):
    """返回【日】PnL dict；缓存里存的已是日 PnL"""
    cp = _pl.Path(PCACHE) / f'{aid}.json'
    if cp.exists():
        try:
            return json.load(open(cp, encoding='utf-8'))
        except Exception:
            pass
    global _S
    if _S is None:
        _S = sess()
    for _ in range(6):
        try:
            r = _S.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            import time; time.sleep(5); continue
        if r.status_code != 200 or r.headers.get('Retry-After'):
            import time; time.sleep(float(r.headers.get('Retry-After') or 4)); continue
        try:
            j = r.json()
        except Exception:
            import time; time.sleep(3); continue
        recs = sorted((str(x[0]), float(x[1])) for x in (j.get('records') or []) if len(x) >= 2 and x[1] is not None)
        if len(recs) < 60:
            import time; time.sleep(3); continue
        ser = {recs[k][0]: recs[k][1] - recs[k - 1][1] for k in range(1, len(recs))}
        json.dump(ser, open(cp, 'w', encoding='utf-8'))
        return ser
    return None


ALIAS = {'P_int20': 'x180_leg_int', 'M_cov': 'x180_leg_cov'}  # 腿名 -> mined 文件名


def cid2id(cid):
    if cid in ALIAS:
        p = _pl.Path(MINED) / f'{ALIAS[cid]}.json'
        if p.exists():
            d = json.load(open(p, encoding='utf-8'))
            if d.get('id'):
                return d['id']
    if len(cid) == 8 and cid.isalnum():
        return cid
    p = _pl.Path(MINED) / f'{cid}.json'
    if p.exists():
        d = json.load(open(p, encoding='utf-8'))
        if d.get('id'):
            return d['id']
    for h in _pl.Path(MINED).glob('*.json'):
        try:
            d = json.load(open(h, encoding='utf-8'))
        except Exception:
            continue
        if d.get('_cid') == cid and d.get('id'):
            return d['id']
    return None


def crr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 120:
        return None
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    n = len(x); mx = sum(x) / n; my = sum(y) / n
    cov = sum((p - mx) * (q - my) for p, q in zip(x, y))
    vx = sum((p - mx) ** 2 for p in x) ** .5; vy = sum((q - my) ** 2 for q in y) ** .5
    return None if vx == 0 or vy == 0 else cov / (vx * vy)


def shp(v):
    n = len(v); m = sum(v) / n
    sd = (sum((t - m) ** 2 for t in v) / (n - 1)) ** .5
    return 0 if sd == 0 else m / sd * (252 ** .5)


def add(dicts, weights):
    tot = {}
    for d, w in zip(dicts, weights):
        if d is None:
            return None
        for k, v in d.items():
            tot[k] = tot.get(k, 0.0) + w * v
    return tot


# ---------- 池子：只认台账 ----------
# ⚠️ 不能从 PnL 缓存目录取池子！缓存里混着数百条未提交候选/实验腿，
#    混进来会把 max corr 虚高压死（曾误把 433 条候选当池子 → 搜出 0 个可用组合）。
LSH = {}
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if len(row) >= 4 and len(row[0]) == 8:
        # 台账列序：id,expr,S,F,T,R,DD,selfCorr,... → S 是 row[2]！row[3] 是 Fitness（曾误用）
        try:
            LSH.setdefault(row[0], float(row[2]))
        except Exception:
            pass

pool = {}
for _pid in LSH:
    _v = get_pnl(_pid)
    if _v:
        pool[_pid] = _v

LEDGER_SET = set(LSH)


def eval_combo(spec, verbose=True, exclude_self=None):
    """spec: {'cid': weight, ...} 或 'cid:w, cid:w'"""
    if isinstance(spec, str):
        d = {}
        for part in spec.replace('，', ',').split(','):
            part = part.strip()
            if not part:
                continue
            k, _, w = part.partition(':')
            d[k.strip()] = float(w) if w else 1.0
        spec = d
    ds, ws, ok = [], [], True
    for cid, w in spec.items():
        aid = cid2id(cid)
        if aid is None:
            if verbose: print(f'  !! 找不到 {cid}')
            ok = False; continue
        p = get_pnl(aid)
        if p is None:
            if verbose: print(f'  !! {cid} 取不到 PnL')
            ok = False; continue
        ds.append(p); ws.append(w)
    if not ok or not ds:
        return None
    combo = add(ds, ws)
    ks = sorted(combo)
    S = shp([combo[k] for k in ks])
    res = []
    for pid, pp in pool.items():
        if pid == exclude_self:
            continue
        c = crr(combo, pp)
        if c is not None:
            res.append((c, pid, LSH.get(pid)))
    res.sort(reverse=True)
    mx = res[0][0] if res else 0
    ov = [(c, p, s) for c, p, s in res if c >= 0.7 and s]
    line = 1.1 * max(s for _, _, s in ov) if ov else None
    if verbose:
        print(f'  预测 S = {S:.3f}   max corr = {mx:.4f}   {"直通 OK" if mx < 0.68 else "有风险" if mx < 0.7 else "会被拒"}')
        for c, p, s in res[:5]:
            print(f'    {p}  {c:.4f}  S={s}')
        if line:
            print(f'    豁免线 = {line:.3f}')
    return {'S': S, 'maxcorr': mx, 'exempt': line, 'top': res[:5]}


# ---------- 命令 ----------
if not ARGS or ARGS[0] == 'help':
    print(__doc__); sys.exit(0)

cmd = ARGS[0]

if cmd == 'check':
    # 线性性验证：x155_a = A4 锚腿单独, x155_b = 价量腿单独(1.5*c5+1.6*v90)
    # w154_b 表达式 = A4 + 1.5*c5 + 1.6*v90 → 预测 PnL = x155_a + x155_b
    pred = add([get_pnl(cid2id('x155_a')), get_pnl(cid2id('x155_b'))], [1.0, 1.0])
    actual = get_pnl(cid2id('w154_b'))
    if pred is None or actual is None:
        print('缺 PnL，无法验证')
    else:
        kp = sorted(pred); ka = sorted(actual)
        print(f'预测 S = {shp([pred[k] for k in kp]):.3f}   实测 S = {shp([actual[k] for k in ka]):.3f}')
        print(f'预测 vs 实测 PnL corr = {crr(pred, actual):.4f}   （越接近 1 说明线性性越好）')

elif cmd == 'eval':
    print('组合:', ARGS[1])
    eval_combo(ARGS[1])

elif cmd == 'pair':
    # 腿两两互相关：找"长得不像"的腿
    legs = [a for a in ARGS[1:]]
    if not legs:
        legs = [c for c in ('L_pst','L_txs','L_mib','L_lqp','L_txt','L_aol','L_dpa','L_cash','L_cfo','L_ac',
                            'L_acc','L_bb','L_int','L_xr','P_c5','P_c2','P_c20','P_vw5','P_v90','P_v120',
                            'P_v60','P_tr20','P_am20','P_on5','P_sd20','P_vd')]
    P = {}
    for l in legs:
        aid = cid2id(l)
        if aid:
            p = get_pnl(aid)
            if p: P[l] = p
    print(f'腿库 {len(P)} 条\n       ' + ''.join(f'{l:>9}' for l in P))
    for a in P:
        line = f'{a:<7}'
        for b in P:
            c = crr(P[a], P[b])
            line += f'{(c if c is not None else float("nan")):>9.3f}'
        print(line)

elif cmd == 'search':
    # numpy 向量化：预计算 M(池×腿) 与 G(腿×腿)，则任意权重 w 的
    #   corr 向量 = (M @ w) / sqrt(w^T G w)，S = mean/std*sqrt(252)（尺度无关）
    # 一次矩阵乘法评完 62 个对手 → 几十万组合秒级扫完
    import numpy as np
    min_s = 2.0
    max_corr = 0.68
    for i, a in enumerate(ARGS):
        if a.startswith('--min-s'):
            min_s = float(a.split('=')[1]) if '=' in a else float(ARGS[i + 1])
        if a.startswith('--max-corr'):
            max_corr = float(a.split('=')[1]) if '=' in a else float(ARGS[i + 1])
    ANCH = ['L_pst', 'L_txs', 'L_mib', 'L_lqp', 'L_txt', 'L_aol', 'L_dpa',
            'L_cash', 'L_cfo', 'L_ac', 'L_acc', 'L_bb', 'L_int', 'L_xr']
    PVS = ['P_c5', 'P_c2', 'P_c20', 'P_vw5', 'P_v90', 'P_v120', 'P_v60',
           'P_tr20', 'P_am20', 'P_on5', 'P_sd20', 'P_vd']
    # 0916 扩容：b157 新腿（N_ = 老族价量腿扩窗口，M_ = 换分母/换算子/换分组的锚腿）
    for _l in ['N_tr5', 'N_tr60', 'N_am60', 'N_rvol']:
        if (_pl.Path(MINED) / f'{_l}.json').exists():
            PVS.append(_l)
    # b180 新腿：日内收益（gJbkQ31Q 获胜腿）、分析师覆盖数变化（池里零条几何）
    if (_pl.Path(MINED) / 'x180_leg_int.json').exists():
        PVS.append('P_int20')
    if (_pl.Path(MINED) / 'x180_leg_cov.json').exists():
        ANCH.append('M_cov')
    for _l in ['M_accI', 'M_intI', 'M_cfoQ', 'M_intc', 'M_tot', 'M_ni',
               'M_liab', 'M_txp', 'M_lnoq', 'M_g12', 'M_tfvce', 'M_debt',
               'M_opex', 'M_revt', 'M_cashZ', 'M_tstk']:
        if (_pl.Path(MINED) / f'{_l}.json').exists():
            ANCH.append(_l)
    # b158 新数据轴腿（option9/model51/news18/pv13）——单独成组，用 --k 才启用
    KLEGS = [k for k in ['K_cfoI', 'K_accI', 'K_impact', 'K_novel', 'K_page', 'K_auth',
                         'K_pcr10', 'K_pcr30', 'K_pcrall', 'K_esent', 'K_comp', 'K_carry',
                         'K_corr90', 'K_pcr_rev'] if (_pl.Path(MINED) / f'{k}.json').exists()]
    if '--k' in ARGS:
        ANCH.append('K_cfoI')
        PVS.extend([k for k in KLEGS if k not in ('K_cfoI',)])
    # b159 换分组/换算子腿（--q 启用）
    QANCH = [q for q in ['Q_xrI', 'Q_pstI', 'Q_cfoI', 'Q_accI', 'Q_xrS', 'Q_cfoS', 'Q_accS',
                         'Q_xrC', 'Q_cfoC', 'Q_accC', 'Q_xrV', 'Q_cfoV', 'Q_accV',
                         'Q_xrL', 'Q_cfoL', 'Q_accL'] if (_pl.Path(MINED) / f'{q}.json').exists()]
    QPVS = [q for q in ['Q_xrZ', 'Q_cfoQ', 'Q_accR', 'Q_pstZ',
                        'Q_rate1', 'Q_rate2', 'Q_rate3', 'Q_rate4'] if (_pl.Path(MINED) / f'{q}.json').exists()]
    if '--q' in ARGS:
        ANCH.extend(QANCH)
        PVS.extend(QPVS)
    # 对齐日期：以池子共有日期为准
    dates = None
    for ps in pool.values():
        ds = set(ps)
        dates = ds if dates is None else (dates & ds)
    dates = sorted(dates)
    T = len(dates)
    if T < 400:
        print(f'共有日期只有 {T} 天，太少'); sys.exit(1)
    print(f'对齐日期 {T} 天（{dates[0]} ~ {dates[-1]}）')
    load = {}
    for l in ANCH + PVS:
        aid = cid2id(l)
        if not aid:
            continue
        p = get_pnl(aid)
        if not p:
            continue
        try:
            load[l] = np.array([p[d] for d in dates], dtype=float)
        except KeyError:
            continue
    legs = list(load)
    print(f'腿库可用 {len(legs)}/{len(ANCH)+len(PVS)}：{" ".join(legs)}')
    Lraw = np.vstack([load[l] for l in legs])          # 原始日 PnL（算 Sharpe 必须用原始值）
    sd = Lraw.std(axis=1, ddof=1, keepdims=True); sd[sd == 0] = 1
    Lz = (Lraw - Lraw.mean(axis=1, keepdims=True)) / sd   # 去均值 z 化（算相关用）
    pids = list(pool)
    Pm = np.vstack([np.array([pool[q][d] for d in dates], dtype=float) for q in pids])
    Pm = Pm - Pm.mean(axis=1, keepdims=True)
    Psd = Pm.std(axis=1, ddof=1, keepdims=True); Psd[Psd == 0] = 1
    Pz = Pm / Psd
    Mmat = Pz @ Lraw.T / T        # 池 × 腿（PnL 可加 → 加权和对各池成员的相关贡献）
    G = Lraw @ Lraw.T / T         # 腿 × 腿（必须用原始 PnL，与 Mmat 同尺度）
    print(f'M {Mmat.shape}  G {G.shape}\n')
    idx = {l: i for i, l in enumerate(legs)}
    A = [l for l in ANCH if l in idx]; Vv = [l for l in PVS if l in idx]
    # 锚组合规模上限 & 锚分组过滤（腿库扩容到 30 条锚后会组合爆炸，必须限规模）
    NA_MAX = 4
    for _i, _a in enumerate(ARGS):
        if _a == '--na' or _a.startswith('--na='):
            NA_MAX = int(_a.split('=')[1]) if '=' in _a else int(ARGS[_i + 1])
    if '--anch' in ARGS:
        # 支持组合，如 --anch LQ（L_ 与 Q_ 都用）；过滤必须在 Q/M/K 追加之后生效
        _w = ARGS[ARGS.index('--anch') + 1].upper()
        _pre = tuple(f'{ch}_' for ch in _w if ch.isalpha())
        A = [l for l in A if l.startswith(_pre)]
    WITH = None
    for _i, _a in enumerate(ARGS):
        if _a == '--with' or _a.startswith('--with='):
            WITH = _a.split('=')[1] if '=' in _a else ARGS[_i + 1]
    if WITH:
        print(f'--with {WITH}：锚组合必须包含该腿')
    NV_MAX = 3
    for _i, _a in enumerate(ARGS):
        if _a == '--nv' or _a.startswith('--nv='):
            NV_MAX = int(_a.split('=')[1]) if '=' in _a else int(ARGS[_i + 1])
    print(f'锚候选 {len(A)} 条 × 价量候选 {len(Vv)} 条，最大锚数 {NA_MAX}，最大价量数 {NV_MAX}')
    hits = []; n_eval = 0

    def _eval_anchor_set(anchors):
        global n_eval
        wa = np.zeros(len(legs))
        for j, x in enumerate(anchors):
            wa[idx[x]] = 1.5 if j == 0 else 1.0
        for nv in range(1, NV_MAX + 1):
            for pvs in itertools.combinations(Vv, nv):
                wv = np.zeros(len(legs))
                for x in pvs:
                    wv[idx[x]] = 1.0
                for wp in (0.5, 0.75, 1.0, 1.25, 1.5, 2.0):
                    w = wa + wp * wv
                    var = float(w @ G @ w)
                    if var <= 0:
                        continue
                    n_eval += 1
                    cvec = (Mmat @ w) / (var ** .5)
                    mx = float(cvec.max())
                    if mx <= max_corr:
                        hits.append((mx, w, anchors, pvs, wp, int(cvec.argmax())))

    if WITH:
        _other = [l for l in A if l != WITH]
        for na in range(0, NA_MAX):
            for extras in itertools.combinations(_other, na):
                _eval_anchor_set((WITH,) + extras)
    else:
        for na in range(1, NA_MAX + 1):
            for anchors in itertools.combinations(A, na):
                _eval_anchor_set(anchors)
    print(f'评估 {n_eval} 个组合，max corr ≤ {max_corr} 的有 {len(hits)} 个')
    res = []
    for mx, w, anchors, pvs, wp, hit in hits:
        c = w @ Lraw                     # 原始 PnL 的加权和（尺度无关 → S 可直接算）
        S = c.mean() / c.std(ddof=1) * (252 ** .5)
        if not np.isfinite(S):
            continue
        if S >= min_s:
            res.append((S, mx, anchors, pvs, wp, pids[hit]))
    res.sort(key=lambda t: (-t[0], t[1]))
    print(f'其中 S ≥ {min_s} 的有 {len(res)} 个\n')
    # ---- 多样性筛选：同一"腿核心"只能吃一口，兄弟候选入池后必互撞 0.98+
    #  在同一批里贪心挑"彼此相关 < 0.60"的组合，一次能出多条可提交候选
    if '--diverse' in ARGS:
        DIV = 0.60
        for _i, _a in enumerate(ARGS):
            if _a == '--div' or _a.startswith('--div='):
                DIV = float(_a.split('=')[1]) if '=' in _a else float(ARGS[_i + 1])
        keep = []
        for item in res:
            _, _, anchors, pvs, wp, _ = item
            w = np.zeros(len(legs))
            for j, x in enumerate(anchors):
                w[idx[x]] = 1.5 if j == 0 else 1.0
            for x in pvs:
                w[idx[x]] = wp
            ok = True
            for k in keep:
                v = np.zeros(len(legs))
                for j, x in enumerate(k[2]):
                    v[idx[x]] = 1.5 if j == 0 else 1.0
                for x in k[3]:
                    v[idx[x]] = k[4]
                den = (float(w @ G @ w) * float(v @ G @ v)) ** .5
                if den > 0 and abs(float(w @ G @ v) / den) > DIV:
                    ok = False; break
            if ok:
                keep.append(item)
        print(f'多样性筛选：{len(res)} → {len(keep)} 条（两两相关 ≤{DIV}）')
        res = keep

    # 腿名 -> 表达式
    EXPR = {
     'L_pst':  G_EXPR('fnd6_pstkl/cap'),
     'L_txs':  G_EXPR('fnd6_txs/cap'),
     'L_mib':  G_EXPR('fnd6_mfmq_mibtq/cap'),
     'L_lqp':  G_EXPR('fnd6_lqpl1/cap'),
     'L_txt':  G_EXPR('fnd6_txtubadjust/cap'),
     'L_aol':  G_EXPR('fnd6_newa1v1300_aol2/cap'),
     'L_dpa':  G_EXPR('fnd6_newqv1300_dpactq/cap'),
     'L_cash': G_EXPR('ts_av_diff(cash/assets,45)'),
     'L_cfo':  G_EXPR('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'L_ac':   G_EXPR('ts_av_diff(assets_curr/assets,30)'),
     'L_acc':  G_EXPR('fn_accrued_liab_curr_a/assets'),
     'L_bb':   G_EXPR('authorized_stock_buyback_amount/assets'),
     'L_int':  G_EXPR('-annual_intangible_assets_net_carrying_value/assets'),
     'L_xr':   G_EXPR('fnd6_xrent/assets'),
     'P_c5':   G_EXPR('-ts_delta(close, 5)'),
     'P_c2':   G_EXPR('-ts_delta(close, 2)'),
     'P_c20':  G_EXPR('-ts_delta(close, 20)'),
     'P_vw5':  G_EXPR('-ts_delta(vwap, 5)'),
     'P_v90':  G_EXPR('volume/ts_mean(volume, 90)'),
     'P_v120': G_EXPR('volume/ts_mean(volume, 120)'),
     'P_v60':  G_EXPR('volume/ts_mean(volume, 60)'),
     'P_tr20': G_EXPR('-ts_rank(returns, 20)'),
     'P_am20': G_EXPR('-ts_mean(abs(returns)/volume, 20)'),
     'P_on5':  G_EXPR('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
     'P_sd20': G_EXPR('-ts_std_dev(returns, 20)'),
     'P_vd':   G_EXPR('(close - vwap)/vwap'),
     # ---- b180 新腿 ----
     'P_int20': G_EXPR('-ts_rank(close/open - 1, 20)'),
     'M_cov':   G_EXPR('ts_backfill(ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120)'),
     # ---- b157 扩容腿（N_ 价量 / M_ 锚）----
     'N_tr5':   G_EXPR('-ts_rank(returns, 5)'),
     'N_tr60':  G_EXPR('-ts_rank(returns, 60)'),
     'N_am60':  G_EXPR('-ts_mean(abs(returns)/volume, 60)'),
     'N_rvol':  G_EXPR('-ts_std_dev(returns, 60)'),
     'M_accI':  G_EXPR_I('fn_accrued_liab_curr_a/assets'),
     'M_intI':  G_EXPR_I('-annual_intangible_assets_net_carrying_value/assets'),
     'M_cfoQ':  'quantile(ts_av_diff(cashflow_op/enterprise_value,45))',
     'M_intc':  G_EXPR('fnd6_intc/assets'),
     'M_tot':   G_EXPR('anl4_fs_detail_estimate_1qf_v4_nd_totassets_mean/assets'),
     'M_ni':    G_EXPR('-(fnd6_newa2v1300_ni - cashflow_op)/assets'),
     'M_liab':  G_EXPR('liabilities_curr/assets'),
     'M_txp':   G_EXPR('fnd6_txtubpospinc/assets'),
     'M_lnoq':  G_EXPR('fnd6_newqv1300_lnoq/assets'),
     'M_g12':   G_EXPR('fnd6_newqv1300_glcea12/assets'),
     'M_tfvce': G_EXPR('fnd6_tfvce/assets'),
     'M_debt':  G_EXPR('debt_st/assets'),
     'M_opex':  G_EXPR('operating_expense/assets'),
     'M_revt':  G_EXPR('fnd6_mfma2_revt/assets'),
     'M_cashZ': 'zscore(ts_av_diff(cash/assets,45))',
     'M_tstk':  G_EXPR('fnd6_tstkc/assets'),
     # ---- b158 新数据轴腿 ----
     'K_cfoI':  G_EXPR_I('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'K_accI':  G_EXPR_I('fn_accrued_liab_curr_a/assets'),
     'K_impact':G_EXPR('mean_news_impact_projection'),
     'K_novel': G_EXPR('mean_event_novelty_score'),
     'K_page':  G_EXPR('pv13_com_page_rank'),
     'K_auth':  G_EXPR('pv13_com_rk_au'),
     'K_pcr10': G_EXPR('pcr_vol_10'),
     'K_pcr30': G_EXPR('pcr_oi_30'),
     'K_pcrall':G_EXPR('pcr_oi_all'),
     'K_esent': G_EXPR('mean_equity_sentiment_score'),
     'K_comp':  G_EXPR('mean_composite_sentiment_score'),
     'K_carry': G_EXPR('forward_price_90/forward_price_30 - 1'),
     'K_corr90':G_EXPR('correlation_last_90_days_spy'),
     'K_pcr_rev':G_EXPR('-pcr_vol_10'),
     # ---- b159 换分组 / 换算子腿 ----
     'Q_xrI':  G_EXPR_I('fnd6_xrent/assets'),
     'Q_pstI': G_EXPR_I('fnd6_pstkl/cap'),
     'Q_cfoI': G_EXPR_I('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'Q_accI': G_EXPR_I('fn_accrued_liab_curr_a/assets'),
     'Q_xrS':  G_EXPR_S('fnd6_xrent/assets'),
     'Q_cfoS': G_EXPR_S('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'Q_accS': G_EXPR_S('fn_accrued_liab_curr_a/assets'),
     'Q_xrC':  G_EXPR_C('fnd6_xrent/assets'),
     'Q_cfoC': G_EXPR_C('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'Q_accC': G_EXPR_C('fn_accrued_liab_curr_a/assets'),
     'Q_xrV':  G_EXPR_V('fnd6_xrent/assets'),
     'Q_cfoV': G_EXPR_V('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'Q_accV': G_EXPR_V('fn_accrued_liab_curr_a/assets'),
     'Q_xrL':  G_EXPR_L('fnd6_xrent/assets'),
     'Q_cfoL': G_EXPR_L('ts_av_diff(cashflow_op/enterprise_value,45)'),
     'Q_accL': G_EXPR_L('fn_accrued_liab_curr_a/assets'),
     'Q_xrZ':  'zscore(fnd6_xrent/assets)',
     'Q_cfoQ': 'quantile(ts_av_diff(cashflow_op/enterprise_value,45))',
     'Q_accR': 'rank(fn_accrued_liab_curr_a/assets)',
     'Q_pstZ': 'zscore(fnd6_pstkl/cap)',
     'Q_rate1': G_EXPR('vec_avg(anl4_basicdetailrec_ratingvalue)'),
     'Q_rate2': G_EXPR('vec_avg(anl4_fs_detail_rec_v4_nd_estimate)'),
     'Q_rate3': G_EXPR('vec_avg(anl4_total_rec)'),
     'Q_rate4': G_EXPR('-vec_avg(anl4_eaz2lrec_ratingvalue)'),
    }
    TAKE = 40
    if '--take' in ARGS:
        TAKE = int(ARGS[ARGS.index('--take') + 1])
    PFX = 'w158'
    if '--pfx' in ARGS:
        PFX = ARGS[ARGS.index('--pfx') + 1]
    COMB = {}
    for i, (S, mx, anchors, pvs, wp, hit) in enumerate(res[:TAKE]):
        parts = []
        for j, a in enumerate(anchors):
            w = 1.5 if j == 0 else 1.0
            parts.append(f'{w}*{EXPR[a]}' if w != 1 else EXPR[a])
        for x in pvs:
            pv = EXPR[x]
            parts.append(f'{wp}*{pv}' if wp != 1 else pv)
        expr = ' + '.join(parts)
        cid = f'{PFX}_{i:02d}'
        COMB[cid] = {'expr': expr, 'S': round(S, 3), 'maxcorr': round(mx, 4),
                     'nearest': hit, 'anchors': list(anchors), 'pvs': list(pvs), 'wp': wp}
        print(f'  S={S:.3f} maxcorr={mx:.4f} 撞{hit} | {expr[:150]}')
    if '--emit' in ARGS:
        OUTP = '_autologs/search_combos.json'
        if '--out' in ARGS:
            OUTP = ARGS[ARGS.index('--out') + 1]
        json.dump(COMB, open(OUTP, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print(f'已落盘 {OUTP}（{len(COMB)} 条）')
