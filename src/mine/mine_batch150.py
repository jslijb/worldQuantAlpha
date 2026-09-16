# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch150 = 「用 truncation / PV 权重抬 R」批 —— 目标把 SF 从 3.83 推过 4.0
# 坐标（今天实测，含公式）：
#   Fitness F = S × sqrt(R / max(T, 0.125))    ← 已用台账真实值逐条验证（kqoq0zed、w132_h 分毫不差）
#   ⇒ F 有天花板 S × sqrt(R / 0.125)；T 一旦 ≤0.125，再降 T 不再加分
#   起点 w149_e：/cap 四锚 + PV0.75、decay10 → **S=1.97 / T=0.0939 / R=0.112 / F=1.86 / SF=3.83**
#     它已经在右区间（T 已进 0.125 以内），**唯一缺口是 R 要 ≥ 0.125 才能让 F 够 2.0**
#   ⇒ 抬 R 的手段（都不动 S、不动几何）：
#       ① truncation 收紧 → 持仓更集中 → R 与 σ 同比例上升 → S 不变、F ∝ sqrt(R) 上升
#       ② PV 腿加权（PV 是质量与收益引擎）
#       ③ 锚腿加权（头部锚权重）
#   目标：**S≈2.0~2.2 且 T≤0.125 且 R≥0.125 ⇒ SF≥4.0，同时几何仍是 /cap 低 corr 区**
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

def body(a1w=1.5, anchors=('fnd6_txtubadjust', 'fnd6_newa1v1300_aol2', 'fnd6_newqv1300_dpactq', 'fnd6_pstkl'),
         pv=0.75):
    legs = [f'{a1w}*{G(anchors[0] + "/cap")}']
    legs += [G(a + '/cap') for a in anchors[1:]]
    legs += [f'{pv}*{G("-ts_delta(vwap, 5)")}', f'{pv}*{G("volume/ts_mean(volume, 120)")}']
    return ' + '.join(legs)

C = [
 # ① truncation 收紧（抬 R）
 ('w150_a', body(), BASE(trunc=0.05)),
 ('w150_b', body(), BASE(trunc=0.03)),
 ('w150_c', body(), BASE(trunc=0.12)),
 # ② PV 腿加权（抬 R 与质量）
 ('w150_d', body(pv=1.0), BASE()),
 ('w150_e', body(pv=1.25), BASE()),
 # ③ 锚腿加权
 ('w150_f', body(a1w=2.0), BASE()),
 ('w150_g', body(a1w=2.0, pv=1.0), BASE()),
 # ④ 五锚（堆独有成分）
 ('w150_h', body(anchors=('fnd6_txtubadjust', 'fnd6_newa1v1300_aol2', 'fnd6_newqv1300_dpactq',
                          'fnd6_pstkl', 'fnd6_txs')), BASE()),
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
    print('batch150 done', flush=True)
