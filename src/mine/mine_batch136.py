# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch136 = /cap 家族「顶 S 到豁免线」批
# 已知（batch131~135 实证）：
#   ① /cap 缩放把 corr 从 ~0.85 打到 0.6999（kqoq0zed 直通入池，S=2.02）
#   ② 加回质量引擎腿（cash/cap、cfoev/cap）→ SF 从 3.85 升到 4.30，但 corr 飙到 0.96（w135_a/b）→ 此路不通
#   ③ decay 越小 S 越高（w131_a decay4 S=2.25 > w131_h decay6 S=2.17）
# 本批目标：保持 /cap 几何（corr 低），把 S 顶到 ≥2.25（豁免线 = 1.10 × kqoq0zed S 2.02 = 2.22）
#   同时 SF ≥ 4.0（靠 F 补：decay 降 → S 升、F 略降，需两头都够）
# 正交变化：decay(3/4) × 头锚权重(1.5/2.0) × PV 权重(0.75/1.0) × 缩放基准(cap/sales/enterprise_value)
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'

TXA='fnd6_txtubadjust'; AOL='fnd6_newa1v1300_aol2'; DPQ='fnd6_newqv1300_dpactq'
PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'; CIT='fnd6_newqv1300_citotalq'

PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')

C = [
 # 主线：/cap 几何保持不变，只动 decay / 权重
 ('w136_a', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
 ('w136_b', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=3)),
 ('w136_c', f'2*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
 ('w136_d', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 1.0*{PVD5} + 1.0*{VOL12}', BASE(delay=4)),
 ('w136_e', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + {G(PST+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
 # 换缩放基准（/cap 之外的两条没试过的路）
 ('w136_f', f'1.5*{G(TXA+"/sales")} + {G(AOL+"/sales")} + {G(DPQ+"/sales")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
 ('w136_g', f'1.5*{G(TXA+"/enterprise_value")} + {G(AOL+"/enterprise_value")} + {G(DPQ+"/enterprise_value")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
 # /cap + 新锚组（换锚，为第 2、3 个入池位留结构差异）
 ('w136_h', f'1.5*{G(TXS+"/cap")} + {G(MIB+"/cap")} + {G(CIT+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}', BASE(delay=4)),
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
    print('batch136 done', flush=True)
