# -*- coding: utf-8 -*-
"""auto_submit_passers.py —— 从 mined 目录批量捞达标候选，本地 corr 判决后自动提交

为什么要有它：手动流程（查指标 → 测 corr → 提交 → 台账）今天重复了十几次，每次
都要人盯。这个脚本把整条链路串起来，并且**每提交成功一条就重算池子**（因为池子
一变，剩余候选的 corr 全部要重判 —— 同构候选扎堆会被拒）。

用法：
  python src/submit/auto_submit_passers.py 'x162_*' --min-sf 4.0 --min-ts 1.25 --max-corr 0.685 --limit 12
  python src/submit/auto_submit_passers.py 'w164_*' --dry            # 只判决不提交

判决口径（与 CLAUDE.md 一致）：
  - 质量闸门：S+F >= min-sf 且 tS >= min-ts 且 is.checks 无 FAIL
  - 相关闸门：本地 max corr <= max-corr（默认 0.685，给平台误差 +0.006~+0.017 留缓冲）
提交后由 submit_v3.py 写台账 + 裁决档案。
"""
import os as _os, pathlib as _pl, sys, json, glob, time, subprocess, statistics as st
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

MINED = 'data/alpha_quality_analysis/mined'
PC = 'data/alpha_quality_analysis/pnl'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
PY = sys.executable

ARGS = sys.argv[1:]
PAT = ARGS[0] if ARGS and not ARGS[0].startswith('-') else '*' 
def opt(name, default):
    for a in ARGS:
        if a == name: return ARGS[ARGS.index(a) + 1]
        if a.startswith(name + '='): return a.split('=', 1)[1]
    return default

MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
MAX_CORR = float(opt('--max-corr', 0.685))
LIMIT = int(opt('--limit', 10))
DRY = '--dry' in ARGS
TAG = opt('--tag', 'auto')

import requests
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def pnl(aid, refresh=False):
    f = _pl.Path(PC) / f'{aid}.json'
    if f.exists() and not refresh:
        return {k: float(v) for k, v in json.load(open(f, encoding='utf-8')).items()}
    # ⚠️ 该端点会限流：429/空 body + Retry-After。必须退避重试，否则整批判决都会误判为"取不到"
    j = None
    for att in range(8):
        r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        ra = r.headers.get('Retry-After')
        try:
            j = r.json()
            if j.get('records'): break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        raise RuntimeError(f'pnl 端点未返回数据（限流或未就绪）: {aid}')
    rec = j.get('records') or []
    d = {}
    prev = None
    for r in rec:
        cum = float(r[1]); d[str(r[0])] = cum - (prev if prev is not None else cum); prev = cum
    json.dump({k: d[k] for k in d}, open(f, 'w', encoding='utf-8'))
    return d


def pool():
    out = {}
    ids = []
    for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
        aid = ln.split(',')[0].strip('"')
        if aid: ids.append(aid)
    miss = []
    for aid in ids:
        try: out[aid] = pnl(aid)
        except Exception: miss.append(aid)
    if miss:
        # 池子不全 → corr 会被低估 → 会误放行。宁可停，不可错判。
        raise SystemExit(f'池子取不全（缺 {len(miss)}/{len(ids)}: {miss[:6]}...）→ 中止，避免误判')
    return out


def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300: return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5; sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy: return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)


submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])
cands = []
for f in sorted(glob.glob(f'{MINED}/{PAT}.json')):
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception: continue
    aid = d.get('id')
    if not aid or aid in submitted: continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < MIN_SF or (t.get('sharpe') or 0) < MIN_TS or fa: continue
    cands.append(dict(cid=d.get('_cid', _pl.Path(f).stem), aid=aid, SF=S + F, tS=t.get('sharpe'), S=S, F=F))

print(f'匹配 {PAT}：达标候选 {len(cands)} 条，按 SF 降序处理', flush=True)
P = pool()
print(f'池子 {len(P)} 条', flush=True)

n_ok = 0
for c in sorted(cands, key=lambda x: -x['SF']):
    if n_ok >= LIMIT: break
    aid = c['aid']
    try: x = pnl(aid)
    except Exception as e:
        print(f"{aid} PnL 取不到 {e}", flush=True); continue
    time.sleep(1.5)                       # 池子遍历也走网络时留出间隔，减少限流
    best = (0.0, '')
    for q, p in P.items():
        v = corr(x, p)
        if v is not None and v > best[0]: best = (v, q)
    if best[0] > MAX_CORR:
        print(f"  ✗ {aid} {c['cid']:24s} SF={c['SF']:.2f} tS={c['tS']:.2f} corr={best[0]:.4f} 撞{best[1]} → 跳过", flush=True)
        continue
    print(f"  ✓ {aid} {c['cid']:24s} SF={c['SF']:.2f} tS={c['tS']:.2f} corr={best[0]:.4f} → 提交", flush=True)
    if DRY: continue
    r = subprocess.run([PY, 'src/submit/submit_v3.py', aid, f'{TAG}-{c["cid"]}'],
                       capture_output=True, text=True, timeout=600)
    tail = (r.stdout or '').strip().splitlines()
    print('    ' + (tail[-1] if tail else r.stderr[:200]), flush=True)
    if 'ACCEPTED' in (r.stdout or ''):
        n_ok += 1
        submitted.add(aid)
        try: P[aid] = x                      # 池子立即更新（后续候选重判）
        except Exception: pass
    time.sleep(3)

print(f'auto_submit_passers 完成：本轮提交 {n_ok} 条', flush=True)
