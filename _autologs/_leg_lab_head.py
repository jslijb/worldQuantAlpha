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


def cid2id(cid):
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


# ---------- 池子 ----------
pool = {}
for f in _pl.Path(PCACHE).glob('*.json'):
    if f.stem.isalnum() and len(f.stem) == 8:
        try:
            pool[f.stem] = json.load(open(f, encoding='utf-8'))
        except Exception:
            pass

LSH = {}
for row in csv.reader(open(LEDGER, newline='', encoding='utf-8')):
    if len(row) >= 4 and len(row[0]) == 8:
        try:
            LSH.setdefault(row[0], float(row[3]))
        except Exception:
            pass

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

