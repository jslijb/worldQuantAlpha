# -*- coding: utf-8 -*-
"""one_corr.py —— 单条候选对 107 条池子的完整 corr 分布（提交前最后一道体检）"""
import os as _os, pathlib as _pl, sys, json, io, glob
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

AID = sys.argv[1]
L = []

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass


def pnl(aid):
    """取 PnL 时序（recordset，需先差分）"""
    loc = 'https://api.worldquantbrain.com/alphas/%s/recordsets/pnl' % aid
    for _ in range(20):
        try:
            r = sess.get(loc)
        except Exception:
            continue
        ra = r.headers.get('Retry-After')
        if ra:
            import time as _t; _t.sleep(float(ra)); continue
        break
    j = r.json()
    rec = j.get('records')
    if not rec:
        return None
    dates = [x[0] for x in rec]
    vals = [x[1] for x in rec]
    # 差分还原日收益
    d = {}
    for i in range(1, len(dates)):
        d[dates[i]] = vals[i] - vals[i - 1]
    return d


def corr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 300:
        return None
    xa = [a[k] for k in ks]; xb = [b[k] for k in ks]
    n = len(ks)
    ma = sum(xa) / n; mb = sum(xb) / n
    va = sum((v - ma) ** 2 for v in xa) ** .5
    vb = sum((v - mb) ** 2 for v in xb) ** .5
    if va == 0 or vb == 0:
        return None
    cv = sum((xa[i] - ma) * (xb[i] - mb) for i in range(n))
    return cv / (va * vb)


sub = []
seen = set()
for ln in io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig'):
    p = ln.split(',', 1)
    if p and p[0].strip() and p[0].strip() != 'id':
        i = p[0].strip().strip('"')
        if i not in seen:
            seen.add(i); sub.append(i)

print('池子 %d 条；取候选 PnL...' % len(sub), flush=True)
pa = pnl(AID)
if pa is None:
    L.append('%s 取不到 PnL' % AID)
else:
    L.append('候选 %s：PnL %d 天' % (AID, len(pa)))
    res = []
    for s in sub:
        pb = pnl(s)
        if not pb:
            continue
        c = corr(pa, pb)
        if c is not None:
            res.append((c, s))
    res.sort(reverse=True)
    L.append('可比对 %d 条' % len(res))
    L.append('最大 5 对：')
    for c, s in res[:5]:
        L.append('   %-11s %.4f' % (s, c))
    if res:
        v = [c for c, _ in res]
        L.append('max=%.4f  p90=%.4f  中位=%.4f  min=%.4f' %
                 (v[0], v[int(len(v) * .1)], v[len(v) // 2], v[-1]))
        L.append('超 0.40=%d  超 0.50=%d  超 0.66=%d  超 0.685=%d'
                 % (sum(1 for x in v if x > .40), sum(1 for x in v if x > .50),
                    sum(1 for x in v if x > .66), sum(1 for x in v if x > .685)))

io.open('_autologs/_one_corr_%s.txt' % AID, 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
