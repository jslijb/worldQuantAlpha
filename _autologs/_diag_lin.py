# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl, sys, json, csv
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d/'brain_credentials.txt').exists(): _os.chdir(_d); break
import requests
LED='data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
PC='data/alpha_quality_analysis/pnl'
s=requests.Session(); s.auth=tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code==201

def get_pnl(aid, refresh=False):
    f=_pl.Path(PC)/f'{aid}.json'
    if f.exists() and not refresh:
        j=json.load(open(f))
    else:
        j=s.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl').json()
        json.dump(j, open(f,'w'))
    rec=j.get('records') or []
    d={}
    for r in rec:
        d[str(r[0])]=float(r[1])
    return d

def diff(p):
    ks=sorted(p); out={}
    prev=None
    for k in ks:
        out[k]=p[k]-prev if prev is not None else 0.0
        prev=p[k]
    return out

def corr(a,b):
    import statistics as st
    ks=sorted(set(a)&set(b))
    if len(ks)<100: return None
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx=st.mean(x); my=st.mean(y)
    sx=(sum((v-mx)**2 for v in x))**.5; sy=(sum((v-my)**2 for v in y))**.5
    if sx==0 or sy==0: return None
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy)

LEGS={'L_dpa':'dq','L_cash':'ca','L_cfo':'cf'}
# mLmLW6E6 = w162_00: 1.5 dpa + cash + cfo + ...
spec=json.load(open('_autologs/search_combos.json'))['w162_00']
print('EXPR:', spec['expr'])
wts=spec.get('wp')
print('anchors', spec['anchors'], 'pvs', spec['pvs'], 'wp', wts)
