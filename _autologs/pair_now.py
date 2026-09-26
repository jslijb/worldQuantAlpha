# -*- coding: utf-8 -*-
"""pair_now.py <id1> <id2> ... —— 候选之间两两 PnL 相关（选同日提交的第 2 条前必看）"""
import os as _os, pathlib as _pl, sys, io, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

OUT = io.open(r'D:\Python\worldquant\_autologs\_pair_now.txt', 'w', encoding='utf-8')
def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s); OUT.write(s + '\n'); OUT.flush()

IDS = [x for x in sys.argv[1:] if not x.startswith('--')]
sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass
    time.sleep(3)


def pnl(aid):
    loc = 'https://api.worldquantbrain.com/alphas/%s/recordsets/pnl' % aid
    r = None
    for _ in range(25):
        try:
            r = sess.get(loc, timeout=60)
        except Exception:
            time.sleep(3); continue
        ra = r.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 15)); continue
        break
    if r is None:
        return None
    try:
        rec = r.json().get('records')
    except Exception:
        return None
    if not rec:
        return None
    d = {}
    for i in range(1, len(rec)):
        d[rec[i][0]] = rec[i][1] - rec[i - 1][1]
    return d


def corr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 200:
        return None
    n = len(ks)
    xa = [a[k] for k in ks]; xb = [b[k] for k in ks]
    ma = sum(xa) / n; mb = sum(xb) / n
    va = sum((v - ma) ** 2 for v in xa) ** .5
    vb = sum((v - mb) ** 2 for v in xb) ** .5
    if va == 0 or vb == 0:
        return None
    return sum((xa[i] - ma) * (xb[i] - mb) for i in range(n)) / (va * vb)


P = {}
for i in IDS:
    P[i] = pnl(i)
    say('%-12s PnL %s 天' % (i, len(P[i]) if P[i] else 'FAIL'))

say('')
say('%-12s %s' % ('', ' '.join('%12s' % i for i in IDS)))
for a in IDS:
    row = []
    for b in IDS:
        if a == b:
            row.append('%12s' % '1.0000')
        elif P[a] and P[b]:
            c = corr(P[a], P[b])
            row.append('%12s' % ('%.4f' % c if c is not None else 'n/a'))
        else:
            row.append('%12s' % '--')
    say('%-12s %s' % (a, ' '.join(row)))
OUT.close()
