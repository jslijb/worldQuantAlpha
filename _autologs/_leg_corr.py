# -*- coding: utf-8 -*-
"""腿 vs 已提交池的 maxcorr —— 判断"这条腿是不是新几何"""
import os as _os, pathlib as _pl, json, csv, statistics as st, sys
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d/'brain_credentials.txt').exists(): _os.chdir(_d); break
MINED='data/alpha_quality_analysis/mined'; PC='data/alpha_quality_analysis/pnl'

def corr(a,b):
    ks=sorted(set(a)&set(b))
    if len(ks)<300: return None
    x=[a[k] for k in ks]; y=[b[k] for k in ks]
    mx=st.mean(x); my=st.mean(y)
    sx=sum((v-mx)**2 for v in x)**.5; sy=sum((v-my)**2 for v in y)**.5
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy) if sx and sy else None

pool={}
for r in list(csv.reader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv',encoding='utf-8-sig')))[1:]:
    try: pool[r[0]]=json.load(open(f'{PC}/{r[0]}.json'))
    except Exception: pass
print(f'池子 {len(pool)} 条')
for cid in sys.argv[1:]:
    try:
        aid=json.load(open(f'{MINED}/{cid}.json')).get('id')
        d=json.load(open(f'{PC}/{aid}.json'))
    except Exception as e:
        print(f'{cid} 无 PnL 缓存（{e}）'); continue
    best=(0,'')
    for q,p in pool.items():
        c=corr(d,p)
        if c is not None and c>best[0]: best=(c,q)
    print(f'{cid:9s} {aid}  maxcorr={best[0]:.4f}  撞{best[1]}')
