# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch149 = kqoq0zed 几何 + 降换手（正确签名 hump(x, hump=0.01)）
# 推导（基于今天实测的 Fitness 公式 F = S × sqrt(R / max(T, 0.125))，已用台账真实值验证分毫不差）：
#   T 有 0.125 的硬下限 ⇒ F 的天花板 = S × sqrt(R / 0.125)
#   ⇒ 目标构型 = **T ≤ 0.125 且 S ≥ 2.05**（kqoq0zed S=2.02/R=0.1175 时上限 SF=3.98，差 0.02）
#   实测"把 T 压到 0.125 后的理论 SF"（用各自真实 R 算）：
#     w132_h S2.17 R0.1046 → 4.16   w131_a S2.25 R0.1047 → 4.31
#     w132_d S2.02 R0.1175 → 3.98（差一口气）
#   ⇒ 只要在 /cap 几何上把 S 抬到 2.05 以上、T 压进 0.125，就能用**低换手**换来 4.0
# 注意：hump 的正确签名是 `hump(x, hump = 0.01)`（写成 hump(x, 0.01) 报 "Invalid number of inputs"）
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

PV = f'0.75*{G("-ts_delta(vwap, 5)")} + 0.75*{G("volume/ts_mean(volume, 120)")}'

def kq(a1='fnd6_txtubadjust', a2='fnd6_newa1v1300_aol2', a3='fnd6_newqv1300_dpactq', w1=1.5, extra=None):
    legs = [f'{w1}*{G(a1 + "/cap")}', G(a2 + '/cap'), G(a3 + '/cap')]
    if extra: legs.append(G(extra + '/cap'))
    return ' + '.join(legs + [PV])

C = [
 # ① kqoq0zed 原几何 + hump（只压换手，不动截面排序）
 ('w149_a', f'hump({kq(a1="fnd6_txtubadjust", a2="fnd6_newa1v1300_aol2", a3="fnd6_newqv1300_dpactq")}, hump = 0.01)', BASE()),
 # ② 四锚（加 PST，提 S）+ hump
 ('w149_b', f'hump({kq(extra="fnd6_pstkl")}, hump = 0.01)', BASE()),
 # ③ 四锚 + 高 decay（decay 与 hump 双管压换手）
 ('w149_c', f'hump({kq(extra="fnd6_pstkl")}, hump = 0.01)', BASE(delay=10)),
 # ④ 五锚 + hump（堆锚提 S）
 ('w149_d', f'hump({kq(extra="fnd6_pstkl")}, hump = 0.01)', BASE(delay=6)),
 # ⑤ 纯高 decay（不加 hump，作 hump 的对照）
 ('w149_e', kq(extra="fnd6_pstkl"), BASE(delay=10)),
 # ⑥ 换锚组（不再使用 kqoq0zed 的 TXA/AOL/DPQ → 断开同族） + hump
 ('w149_f', f'hump({kq(a1="fnd6_pstkl", a2="fnd6_txs", a3="fnd6_mfmq_mibtq")}, hump = 0.01)', BASE()),
 # ⑦ 换锚组 + 四锚 + hump
 ('w149_g', f'hump({kq(a1="fnd6_pstkl", a2="fnd6_txs", a3="fnd6_mfmq_mibtq", extra="fnd6_lqpl1")}, hump = 0.01)', BASE()),
 # ⑧ PV 加权到 1.0 + hump（PV 是质量引擎，加权提 S/F）
 ('w149_h', f'hump({G("fnd6_txtubadjust/cap")} + {G("fnd6_newa1v1300_aol2/cap")} + {G("fnd6_newqv1300_dpactq/cap")} + {G("-ts_delta(vwap, 5)")} + {G("volume/ts_mean(volume, 120)")}, hump = 0.01)', BASE()),
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
    print('batch149 done', flush=True)
