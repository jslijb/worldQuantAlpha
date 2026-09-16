# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch152 = 收口批：两个明确的增量方向
# 方向一：PV 腿加权（实测斜率 = 每 +0.25 → SF +0.10）
#     A_PST 锚组 PV1.0 → SF3.88（S2.00/R0.1102/T0.1201）
#     A_PST 锚组 PV1.25 → SF3.98（S2.08/R0.1157/T0.1392）
# 方向二：把 T 压进 0.125 —— F 的公式是 S×sqrt(R/max(T,0.125))，**T 一旦 ≤0.125 分母锁死，
#     相当于白送 (R/0.125)^0.5 的增益**。w151_f 的 T=0.1392 只差一点点：
#     若 T=0.125：F = 2.08×sqrt(0.1157/0.125) = 2.001 → SF = 4.08 ✅
# 另带一条完全独立的腿系（回购/无形资产 fundamental2 腿）作对照，看能否既抬 R 又错开几何。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

A_PST = ['fnd6_pstkl', 'fnd6_txs', 'fnd6_mfmq_mibtq', 'fnd6_lqpl1']

def mkanch(anchors, head=1.5, pv=1.0, pvlegs=None):
    legs = [f'{head}*{G(anchors[0] + "/cap")}'] + [G(a + '/cap') for a in anchors[1:]]
    legs += pvlegs or [f'{pv}*{G("-ts_delta(vwap, 5)")}', f'{pv}*{G("volume/ts_mean(volume, 120)")}']
    return ' + '.join(legs)

C = [
 # PV 加权继续往上推
 ('w152_a', mkanch(A_PST, pv=1.5), BASE()),
 ('w152_b', mkanch(A_PST, pv=1.4), BASE()),
 # PV 1.25 + 微调 decay，目标把 T 从 0.1392 压进 0.125
 ('w152_c', mkanch(A_PST, pv=1.25), BASE(delay=12)),
 ('w152_d', mkanch(A_PST, pv=1.25), BASE(delay=14)),
 # 换价量腿（vwap→close，缩短窗口，压 T）
 ('w152_e', mkanch(A_PST, pv=1.25, pvlegs=[f'1.25*{G("-ts_delta(close, 5)")}',
                                           f'1.25*{G("volume/ts_mean(volume, 90)")}']), BASE()),
 # 独立腿系对照：fundamental2 回购/无形资产腿 + 冷锚 + 高 PV
 ('w152_f', ' + '.join([G('authorized_stock_repurchase_amount/cap'),
                        G('-annual_intangible_assets_net_carrying_value/cap'),
                        G('fnd6_pstkl/cap'), G('fnd6_txs/cap'),
                        f'1.25*{G("-ts_delta(vwap, 5)")}', f'1.25*{G("volume/ts_mean(volume, 120)")}']), BASE()),
 # A_PST 三锚（去掉一条锚，看 corr 与质量如何动）
 ('w152_g', mkanch(['fnd6_pstkl', 'fnd6_txs', 'fnd6_mfmq_mibtq'], pv=1.25), BASE()),
 # A_PST + 第 6 条冷锚差分腿（加独有成分）
 ('w152_h', ' + '.join([f'1.5*{G("fnd6_pstkl/cap")}', G('fnd6_txs/cap'), G('fnd6_mfmq_mibtq/cap'),
                        G('fnd6_lqpl1/cap'), G('ts_av_diff(fnd6_optlifeq/cap, 45)'),
                        f'1.25*{G("-ts_delta(vwap, 5)")}', f'1.25*{G("volume/ts_mean(volume, 120)")}']), BASE()),
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
    print('batch152 done', flush=True)
