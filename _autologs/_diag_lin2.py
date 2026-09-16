# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl, json, statistics as st
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d/'brain_credentials.txt').exists(): _os.chdir(_d); break
import requests
PC='data/alpha_quality_analysis/pnl'; MINED='data/alpha_quality_analysis/mined'
s=requests.Session(); s.auth=tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code==201

def get_pnl(aid):
    f=_pl.Path(PC)/f'{aid}.json'
    if f.exists(): j=json.load(open(f))
    else:
        j=s.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl').json()
        json.dump(j, open(f,'w'))
    return {str(r[0]):float(r[1]) for r in (j.get('records') or [])}

def diff(p):
    ks=sorted(p); out={}; prev=None
    for k in ks:
        out[k]=0.0 if prev is None else p[k]-prev; prev=p[k]
    return out

def corr(a,b):
    ks=sorted(set(a)&set(b))
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx=st.mean(x); my=st.mean(y)
    sx=sum((v-mx)**2 for v in x)**.5; sy=sum((v-my)**2 for v in y)**.5
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy) if sx and sy else None

def shp(d):
    v=[d[k] for k in sorted(d)]
    return st.mean(v)/st.pstdev(v)*(252**.5)

def cid2id(cid):
    try: return json.load(open(f'{MINED}/{cid}.json')).get('id')
    except Exception: return None

spec=json.load(open('_autologs/search_combos.json'))['w162_00']
wp=spec['wp']; anchor, pvs = spec['anchors'], spec['pvs']
w={}
for j,a in enumerate(anchor): w[a]= 1.5 if j==0 else 1.0
for x in pvs: w[x]=wp

legd={}
for l,ww in w.items():
    aid=cid2id(l)
    p=get_pnl(aid)
    legd[l]=(ww, diff(p), aid)

act=diff(get_pnl('mLmLW6E6'))
ks=sorted(set(act) & set.intersection(*[set(v[1]) for v in legd.values()]))
ks=[k for k in ks if k>'2019-01-01'][1:]
pred={k: sum(v[0]*v[1][k] for v in legd.values()) for k in ks}
act={k: act[k] for k in ks}
print(f'腿数 {len(w)}  对齐日 {len(ks)}')
print(f'预测 S = {shp(pred):.3f}   实测 S = {shp(act):.3f}')
print(f'预测 vs 实测 PnL corr = {corr(pred, act):.4f}')
# 池子
import csv
pool={}
for r in list(csv.reader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv',encoding='utf-8-sig')))[1:]:
    aid=r[0]
    try: pool[aid]=diff(get_pnl(aid))
    except Exception: pass
def maxcorr(x):
    best=(0,'')
    for q,p in pool.items():
        c=corr(x,p)
        if c is not None and c>best[0]: best=(c,q)
    return best
print('预测 PnL 的 maxcorr =', maxcorr(pred))
print('实测 PnL 的 maxcorr =', maxcorr(act))
# 各腿单独 vs 池子
for l,(ww,pd_,aid) in legd.items():
    print(f'  {l:8s} w={ww} S={shp(pd_):6.3f} maxcorr={maxcorr(pd_)[0]:.4f} 撞{maxcorr(pd_)[1]}')
