# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch130 = w129_b(3.67)/w129_a(3.64) 的冲线变体：不对称权重 / decay / 桶 / truncation / PV 强度
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

def G(x): return f'group_rank({x}, subindustry)'
GB = lambda x, b: f'group_rank({x}, {b})'
GI = lambda x: f'group_rank({x}, industry)'

TXA='fnd6_txtubadjust/assets'; AOL='fnd6_newa1v1300_aol2/assets'; TXP='fnd6_txtubposinc/assets'
DPQ='fnd6_newqv1300_dpactq/assets'; ANO='fnd6_newa1v1300_ano/assets'; MIB='fnd6_mfmq_mibtq/assets'; LOL2='fnd6_lol2/assets'
PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')
LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'

C = [
 ('w132_a', f'1.5*{G(TXA)} + {G(AOL)} + {G(DPQ)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(neut='INDUSTRY')),
 ('w132_b', f'1.5*{G(TXA)} + {G(AOL)} + {G(DPQ)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(neut='MARKET')),
 ('w132_c', f'1.5*{GI(TXA)} + {GI(AOL)} + {GI(DPQ)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(neut='INDUSTRY', delay=6)),
 ('w132_d', f'1.5*G({TXA.replace("/assets","/cap")}) + G({AOL.replace("/assets","/cap")}) + G({DPQ.replace("/assets","/cap")}) + 0.75*{PVD5} + 0.75*{VOL12}'.replace('G(','group_rank(').replace(', subindustry)','/cap_placeholder)') if False else f'1.5*group_rank({TXA.replace("/assets","/cap")}, subindustry) + group_rank({AOL.replace("/assets","/cap")}, subindustry) + group_rank({DPQ.replace("/assets","/cap")}, subindustry) + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=6)),
 ('w132_e', f'1.5*{G(TXA)} + {G(AOL)} + {G(DPQ)} + 0.75*{PVD5} + 0.75*{VOL12}', dict(BASE(delay=6), universe='TOP2000')),
 ('w132_f', f'1.5*{G(TXA)} + {G(AOL)} + {G(DPQ)}', BASE(delay=6)),
 ('w132_g', f'1.5*{G(TXA)} + {G(AOL)} + {G(ANO)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(neut='INDUSTRY', delay=6)),
 ('w132_h', f'1.5*{GI(TXA)} + {GI(AOL)} + {GI(DPQ)} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=6)),
 ]

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def post_retry(payload, cid):
    for att in range(8):
        try: r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201): return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None

def run_one(item):
    cid, expr, s = item
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        print(f'{cid}已有产出，跳过', flush=True); return
    r = post_retry({'type':'REGULAR','settings':s,'regular':expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try: p = sess.get(loc)
        except Exception as e:
            print(cid,'NET-poll',e,flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra: time.sleep(float(ra)); continue
        break
    try: j = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = j.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(j)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch130 done', flush=True)
