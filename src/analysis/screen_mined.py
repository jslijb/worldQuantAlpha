# -*- coding: utf-8 -*-
"""screen_mined.py —— 全库存「基础 corr」筛查（找出真正待救的候选）

为什么要它（0916 晚二轮定量结论）：
  实测稀释腿（挂一条池里没有的几何腿）的**效力只有 −0.02 左右**：
    58znv2Y1：基础 0.6928 → 挂隔夜腿 0.6706（−0.022）→ 入池
    x172 批 12 条：基础 0.72~0.82 → 挂腿后 0.686~0.825 → **12/12 全撞墙**
  → **只有基础 corr ≤0.70 的候选才救得动**，≥0.72 的挂腿也不够。
  所以生产流程第一步不是跑表达式，而是**先量出基础 corr**，把火力集中到 ≤0.70 的那一小撮。

本脚本对 `mined/*.json` 里所有「SF≥4.0 且 tS≥1.25 且无 FAIL 且未在台账」的候选，
逐条拉 PnL（走缓存）与**当前池子（台账 78 条）**算 max corr，按升序输出。

用法：
  python src/analysis/screen_mined.py --min-sf 4.0 --min-ts 1.25
产出：data/alpha_quality_analysis/screened_mined.csv
"""
import os as _os, pathlib as _pl, sys, json, glob, time, csv, statistics as st
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

MINED = 'data/alpha_quality_analysis/mined'
PC = 'data/alpha_quality_analysis/pnl'
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
OUT = 'data/alpha_quality_analysis/screened_mined.csv'


def opt(n, d):
    return float(sys.argv[sys.argv.index(n) + 1]) if n in sys.argv else d


MIN_SF = opt('--min-sf', 4.0)
MIN_TS = opt('--min-ts', 1.25)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def pnl(aid):
    f = _pl.Path(PC) / f'{aid}.json'
    if f.exists():
        try:
            return {k: float(v) for k, v in json.load(open(f, encoding='utf-8')).items()}
        except Exception:
            pass
    j = None
    for att in range(8):
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl')
        except Exception:
            time.sleep(2 * (att + 1)); continue
        ra = r.headers.get('Retry-After')
        try:
            j = r.json()
            if j.get('records'):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        raise RuntimeError('pnl 未就绪')
    d = {}
    prev = None
    for r in (j.get('records') or []):
        c = float(r[1]); d[str(r[0])] = c - (prev if prev is not None else c); prev = c
    json.dump(d, open(f, 'w', encoding='utf-8'))
    return d


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


def pool():
    ids, out = [], {}
    for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
        aid = ln.split(',')[0].strip('"')
        if aid and aid not in ids:
            ids.append(aid)
    miss = []
    for aid in ids:
        try:
            out[aid] = pnl(aid)
        except Exception:
            miss.append(aid)
    if miss:
        raise SystemExit(f'池子取不全（缺 {len(miss)}/{len(ids)}: {miss[:6]}）→ 中止')
    return out


submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])
cands = []
for f in sorted(glob.glob(f'{MINED}/*.json')):
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
    cands.append(dict(aid=aid, cid=d.get('_cid', _pl.Path(f).stem), S=S, F=F, tS=t.get('sharpe'),
                      neut=(d.get('settings') or {}).get('neutralization'),
                      expr=(d.get('regular') or {}).get('code') or ''))
print(f'达标未提交候选 {len(cands)} 条', flush=True)

P = pool()
print(f'池子 {len(P)} 条', flush=True)

rows = []
for n, c in enumerate(cands, 1):
    try:
        x = pnl(c['aid'])
    except Exception as e:
        print(f"  [{n}/{len(cands)}] {c['aid']} PnL 取不到 {e}", flush=True)
        continue
    best = (0.0, '')
    for q, p in P.items():
        v = corr(x, p)
        if v is not None and v > best[0]:
            best = (v, q)
    c['corr'] = best[0]; c['hit'] = best[1]
    rows.append(c)
    tag = '★可救' if best[0] <= 0.70 else ('  近' if best[0] <= 0.72 else '')
    print(f"  [{n}/{len(cands)}] {c['aid']:10s} SF={c['S']+c['F']:5.2f} tS={c['tS']:5.2f} corr={best[0]:.4f} 撞{best[1]:10s} {tag}", flush=True)
    time.sleep(1.2)

rows.sort(key=lambda r: r['corr'])
with open(OUT, 'w', newline='', encoding='utf-8-sig') as fh:
    w = csv.writer(fh)
    w.writerow(['id', 'cid', 'SF', 'tS', 'corr', 'hit', 'neut', 'expr'])
    for r in rows:
        w.writerow([r['aid'], r['cid'], round(r['S'] + r['F'], 3), round(r['tS'], 3), round(r['corr'], 4), r['hit'], r['neut'], r['expr']])
print(f'已写出 {OUT}（{len(rows)} 条）', flush=True)
scr = [r for r in rows if r['corr'] <= 0.70]
print(f'其中基础 corr ≤0.70（真·待救）：{len(scr)} 条', flush=True)
for r in scr:
    print(f"   {r['aid']:10s} SF={r['S']+r['F']:5.2f} tS={r['tS']:5.2f} corr={r['corr']:.4f} 撞{r['hit']} {r['cid']}", flush=True)
