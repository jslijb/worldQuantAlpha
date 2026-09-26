# -*- coding: utf-8 -*-
"""pair_matrix.py —— 小池候选两两相关矩阵（含刚入池的 MPakMndk）

用途：选第 2 条时看它跟第 1 条的相关度 —— 第 1 条已入池，第 2 条的 selfCorr 由
"与全池（含第 1 条）的最大相关"决定，所以真正的约束是 corr(候选, MPakMndk)。
"""
import os as _os, pathlib as _pl, sys, json, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests, time

IDS = ['MPakMndk', 'omLV8Zvm', '1YXJeQoW', 'npd3p8aa', 'xA3RANep',
       'vRrdwa8G', 'pwR8wxao', 'npdO71xw', 'O0NoOjab']

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass


def pnl(aid):
    loc = 'https://api.worldquantbrain.com/alphas/%s/recordsets/pnl' % aid
    r = None
    for _ in range(30):
        try:
            r = sess.get(loc)
        except Exception:
            time.sleep(5); continue
        ra = r.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 20)); continue
        break
    try:
        j = r.json()
    except Exception:
        return None
    rec = j.get('records')
    if not rec:
        return None
    d = {}
    for i in range(1, len(rec)):
        d[rec[i][0]] = rec[i][1] - rec[i - 1][1]
    return d


def corr(a, b):
    ks = sorted(set(a) & set(b))
    if len(ks) < 300:
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
L = []
for a in IDS:
    d = pnl(a)
    L.append('%s PnL=%s' % (a, len(d) if d else 'NONE'))
    if d:
        P[a] = d

keys = [a for a in IDS if a in P]
L.append('')
hdr = '%-11s' % '' + ''.join('%-9s' % k[:8] for k in keys)
L.append(hdr)
for a in keys:
    row = '%-11s' % a
    for b in keys:
        if a == b:
            row += '%-9s' % '1.000'
        else:
            c = corr(P[a], P[b])
            row += '%-9s' % ('%.3f' % c if c is not None else '-')
    L.append(row)

io.open('_autologs/_pair_matrix.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
