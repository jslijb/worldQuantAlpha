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
    Lm = np.vstack([load[l] for l in legs])
    Lm = Lm - Lm.mean(axis=1, keepdims=True)
    sd = Lm.std(axis=1, ddof=1, keepdims=True); sd[sd == 0] = 1
    Lz = Lm / sd
    pids = list(pool)
    Pm = np.vstack([np.array([pool[q][d] for d in dates], dtype=float) for q in pids])
    Pm = Pm - Pm.mean(axis=1, keepdims=True)
    Psd = Pm.std(axis=1, ddof=1, keepdims=True); Psd[Psd == 0] = 1
    Pz = Pm / Psd
    Mmat = Pz @ Lz.T / T          # 池 × 腿
    G = Lz @ Lz.T / T             # 腿 × 腿
    print(f'M {Mmat.shape}  G {G.shape}\n')
    idx = {l: i for i, l in enumerate(legs)}
    A = [l for l in ANCH if l in idx]; Vv = [l for l in PVS if l in idx]
    hits = []; n_eval = 0
    for na in (1, 2, 3, 4):
        for anchors in itertools.combinations(A, na):
            wa = np.zeros(len(legs))
            for j, x in enumerate(anchors):
                wa[idx[x]] = 1.5 if j == 0 else 1.0
            for nv in (1, 2, 3):
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
    print(f'评估 {n_eval} 个组合，max corr ≤ {max_corr} 的有 {len(hits)} 个')
    res = []
    for mx, w, anchors, pvs, wp, hit in hits:
        c = w @ Lz
        S = c.mean() / c.std(ddof=1) * (252 ** .5)
        if S >= min_s:
            res.append((S, mx, anchors, pvs, wp, pids[hit]))
    res.sort(key=lambda t: (-t[0], t[1]))
    print(f'其中 S ≥ {min_s} 的有 {len(res)} 个\n')
    for S, mx, anchors, pvs, wp, hit in res[:30]:
        astr = ' + '.join((f'1.5*{x}' if j == 0 else x) for j, x in enumerate(anchors))
        pstr = ' + '.join(f'{wp}*{x}' for x in pvs)
        print(f'  S={S:.3f} maxcorr={mx:.4f} 撞{hit} | {astr} + {pstr}')
