# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl, json, csv, statistics as st
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d/'brain_credentials.txt').exists(): _os.chdir(_d); break
MINED='data/alpha_quality_analysis/mined'; PC='data/alpha_quality_analysis/pnl'

def get_pnl(aid):
    return {k: float(v) for k, v in json.load(open(f'{PC}/{aid}.json', encoding='utf-8')).items()}

def corr(a, b):
    ks = sorted(set(a) & set(b))
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    if len(ks) < 100: return None
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v-mx)**2 for v in x)**.5; sy = sum((v-my)**2 for v in y)**.5
    if not sx or not sy: return None
    return sum((x[i]-mx)*(y[i]-my) for i in range(len(x)))/(sx*sy)

def shp(d):
    v = list(d.values()); return st.mean(v)/st.pstdev(v)*(252**.5)

def cid2id(c):
    return json.load(open(f'{MINED}/{c}.json')).get('id')

pool = {}
for r in list(csv.reader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))[1:]:
    try: pool[r[0]] = get_pnl(r[0])
    except Exception: pass

def maxcorr(x):
    best = (0.0, '')
    for q, p in pool.items():
        c = corr(x, p)
        if c is not None and c > best[0]: best = (c, q)
    return best

for tag, specfile, key, aid in [
        ('w164_02', '_autologs/search_w164.json', 'w164_02', 'MPaPEQGn'),
        ('w164_07', '_autologs/search_w164.json', 'w164_07', 'npdpEJ3l'),
        ('w162_00', '_autologs/search_combos.json', 'w162_00', 'mLmLW6E6'),
        ('w158_00', '_autologs/leg_lab_w158.json', 'w158_00', 'pwRwWoJ3')]:
    try:
        spec = json.load(open(specfile))[key]
    except Exception as e:
        print(tag, 'spec 缺:', e); continue
    wp = spec['wp']; w = {}
    for j, a in enumerate(spec['anchors']): w[a] = 1.5 if j == 0 else 1.0
    for x in spec['pvs']: w[x] = wp
    legp = {}
    for l, ww in w.items():
        try: legp[l] = (ww, get_pnl(cid2id(l)))
        except Exception: pass
    act = get_pnl(aid)
    ks = sorted(set(act) & set.intersection(*[set(v[1]) for v in legp.values()]))
    pred = {k: sum(v[0]*v[1][k] for v in legp.values()) for k in ks}
    act2 = {k: act[k] for k in ks}
    print(f'--- {tag} ({aid}) 腿数={len(w)} 对齐日={len(ks)} 搜索预测 corr={spec["maxcorr"]}')
    print(f'    预测S={shp(pred):.3f} 实测S={shp(act2):.3f} | 预测PnL vs 实测PnL corr={corr(pred, act2):.4f}')
    print(f'    预测PnL maxcorr={maxcorr(pred)}  实测PnL maxcorr={maxcorr(act2)}')
