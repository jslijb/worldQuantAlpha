# -*- coding: utf-8 -*-
"""submit_exempt.py —— 带"豁免线"的相关性判决提交器

背景（李工 0920 纠正）：平台的 self-correlation 规则不是"corr>0.7 一律拒"，
而是两条路：
  ① corr < 0.7（本地 0.685 留缓冲）→ 直通；
  ② corr >= 0.7 时看**豁免线**：候选 S >= 1.10 × max(所有 corr>=0.7 的对手 S)
     → 平台放行（已实证：LLNXEe7L corr 0.7642 / S 2.30 vs 对手 2.02 = +13.9% → 入池）。

旧工具 auto_submit_passers.py 只实现了①，把②的候选全部当"撞墙"砍掉 —— 这就是
几周 0 提交的工具级根因。

用法：
  python src/submit/submit_exempt.py 'w218_*' --min-sf 4.0 --min-ts 1.25 --limit 10 --dry
  python src/submit/submit_exempt.py 'w2*' --tag 0920-exempt
"""
import os as _os, pathlib as _pl, sys, json, glob, time, subprocess, statistics as st

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

MINED = 'data/alpha_quality_analysis/mined'
PC = 'data/alpha_quality_analysis/pnl'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
POOL_S = 'data/alpha_quality_analysis/pool_s.json'
PY = sys.executable

ARGS = sys.argv[1:]
PAT = ARGS[0] if ARGS and not ARGS[0].startswith('-') else '*'


def opt(name, default):
    for a in ARGS:
        if a == name:
            return ARGS[ARGS.index(a) + 1]
        if a.startswith(name + '='):
            return a.split('=', 1)[1]
    return default


MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
LIMIT = int(opt('--limit', 10))
EXEMPT_RATIO = float(opt('--exempt', 1.10))
CORR_FLOOR = float(opt('--corr-floor', 0.70))   # 本地实测 ≈ 平台 −0.006~−0.017，用 0.70 略保守
DRY = '--dry' in ARGS
TAG = opt('--tag', 'exempt')

import requests
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def pnl(aid, refresh=False):
    f = _pl.Path(PC) / f'{aid}.json'
    if f.exists() and not refresh:
        return {k: float(v) for k, v in json.load(open(f, encoding='utf-8')).items()}
    j = None
    for att in range(8):
        r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        ra = r.headers.get('Retry-After')
        try:
            j = r.json()
            if j.get('records'):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        raise RuntimeError(f'pnl 端点未返回数据: {aid}')
    rec = j.get('records') or []
    d = {}
    prev = None
    for r in rec:
        cum = float(r[1])
        d[str(r[0])] = cum - (prev if prev is not None else cum)
        prev = cum
    json.dump(d, open(f, 'w', encoding='utf-8'))
    return d


def pool_ids():
    ids = []
    for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
        aid = ln.split(',')[0].strip('"')
        if aid and aid not in ids:
            ids.append(aid)
    return ids


def pool_s(ids):
    """池成员 Sharpe（平台实况，带缓存）"""
    cache = {}
    if _pl.Path(POOL_S).exists():
        try:
            cache = json.load(open(POOL_S, encoding='utf-8'))
        except Exception:
            cache = {}
    dirty = False
    for aid in ids:
        if aid in cache and cache[aid]:
            continue
        try:
            d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
            cache[aid] = (d.get('is') or {}).get('sharpe')
            dirty = True
            time.sleep(0.25)
        except Exception:
            pass
    if dirty:
        json.dump(cache, open(POOL_S, 'w', encoding='utf-8'), indent=1)
    return cache


def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300:
        return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5; sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy:
        return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)


submitted = set(pool_ids())
cands = []
for f in sorted(glob.glob(f'{MINED}/{PAT}.json')):
    try:
        d = json.load(open(f, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in submitted:
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < MIN_SF or (t.get('sharpe') or 0) < MIN_TS or fa:
        continue
    cands.append(dict(cid=d.get('_cid', _pl.Path(f).stem), aid=aid, SF=S + F,
                      tS=t.get('sharpe'), S=S, F=F))

print(f'匹配 {PAT}：达标候选 {len(cands)} 条（豁免比 {EXEMPT_RATIO}，corr 地板 {CORR_FLOOR}）', flush=True)
P = {}
miss = []
ids = pool_ids()
for aid in ids:
    try:
        P[aid] = pnl(aid)
    except Exception:
        miss.append(aid)
if miss:
    raise SystemExit(f'池子取不全（缺 {len(miss)}）→ 中止，避免误判')
PS = pool_s(ids)
print(f'池子 {len(P)} 条（S 已知 {sum(1 for v in PS.values() if v)} 条）', flush=True)

n_ok = 0
for c in sorted(cands, key=lambda x: -x['SF']):
    if n_ok >= LIMIT:
        break
    aid = c['aid']
    try:
        x = pnl(aid)
    except Exception as e:
        print(f"  {aid} PnL 取不到 {e}", flush=True)
        continue
    time.sleep(1.2)
    # 收集该候选所有 corr >= floor 的对手
    rivals = []
    for q, p in P.items():
        v = corr(x, p)
        if v is not None and v >= CORR_FLOOR:
            rivals.append((v, q, PS.get(q)))
    if not rivals:
        print(f"  ✓ {aid} {c['cid']:26s} SF={c['SF']:.2f} tS={c['tS']:.2f} corr<{CORR_FLOOR} → 直通提交", flush=True)
        need = None
    else:
        known = [r for r in rivals if r[2]]
        if not known:
            print(f"  ? {aid} {c['cid']:26s} 对手 S 未知 → 跳过", flush=True)
            continue
        vmax, qmax, smax = max(known, key=lambda t: t[2])
        need = EXEMPT_RATIO * smax
        if c['S'] < need:
            print(f"  ✗ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr={vmax:.4f} 撞{qmax}(S={smax}) 需≥{need:.2f} → 不够", flush=True)
            continue
        print(f"  ★ {aid} {c['cid']:26s} SF={c['SF']:.2f} S={c['S']:.2f} corr={vmax:.4f} 撞{qmax}(S={smax}) 需≥{need:.2f} → 豁免放行", flush=True)
    if DRY:
        continue
    r = subprocess.run([PY, 'src/submit/submit_v3.py', aid, f'{TAG}-{c["cid"]}'],
                       capture_output=True, text=True, timeout=600)
    tail = (r.stdout or '').strip().splitlines()
    print('    ' + (tail[-1] if tail else (r.stderr or '')[:200]), flush=True)
    if 'ACCEPTED' in (r.stdout or ''):
        n_ok += 1
        submitted.add(aid)
        P[aid] = x
        PS[aid] = c['S']
        json.dump(PS, open(POOL_S, 'w', encoding='utf-8'), indent=1)
    time.sleep(3)

print(f'submit_exempt 完成：本轮提交 {n_ok} 条', flush=True)
