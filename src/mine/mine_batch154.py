# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch154 = 收口最后一次：新族价量腿 + 按已验证斜率把 PV 权重提到 1.5~1.6
# 数据：
#   A_PST 锚 + close5/vol90 族价量腿 + PV1.25 + decay10 → S2.07 F1.89 **SF3.96**（w153_a）
#   A_PST 锚 + vwap5/vol120 族价量腿 + PV1.5  + decay10 → S2.13 F1.87 **SF4.00**（w152_a，但 corr 0.8779 被同族价量腿顶死）
#   斜率：PV 每 +0.25 → SF 约 +0.10
#   ⇒ 本批 = **换成新族价量腿（与 kqoq0zed 的 vwap5/vol120 不同族）+ PV 1.5~1.6**，
#      目标是 SF ≥4.0 且 corr 不再撞 kqoq0zed
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

A4 = f'1.5*{G("fnd6_pstkl/cap")} + {G("fnd6_txs/cap")} + {G("fnd6_mfmq_mibtq/cap")} + {G("fnd6_lqpl1/cap")}'
A5 = f'{A4} + {G("fnd6_optlifeq/cap")}'
PVN = lambda w: f'{w}*{G("-ts_delta(close, 5)")} + {w}*{G("volume/ts_mean(volume, 90)")}'

C = [
 ('w154_a', f'{A4} + {PVN(1.5)}', BASE()),
 ('w154_b', f'{A4} + {PVN(1.6)}', BASE()),
 ('w154_c', f'{A4} + {PVN(1.4)}', BASE()),
 ('w154_d', f'{A5} + {PVN(1.5)}', BASE()),
 ('w154_e', f'{A4} + {PVN(1.5)}', BASE(delay=12)),
 ('w154_f', f'{A4} + {PVN(1.5)}', BASE(neut='INDUSTRY')),
 ('w154_g', f'{A4} + {PVN(1.75)}', BASE()),
 ('w154_h', f'{A4} + {PVN(1.5)} + 0.5*{G("-ts_rank(close, 20)")}', BASE()),
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
    try: jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:300]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch154 done', flush=True)
