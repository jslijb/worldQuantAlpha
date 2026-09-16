# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch153 = 最后一道锁：**价量腿**
# 本轮实测出的关键事实：
#   w152_a（全新冷锚组 + PV 1.5）SF=4.00 过线，但 corr=**0.8779 撞 kqoq0zed**
#   —— 锚组已经全换（PST/TXS/MIB/LQP，kqoq0zed 用的是 TXA/AOL/DPQ），几何却仍被顶到 0.88
#   ⇒ **共享锁不在锚，在价量腿**：kqoq0zed 用的是
#        group_rank(-ts_delta(vwap, 5))  +  group_rank(volume/ts_mean(volume, 120))
#      任何候选只要沿用这两条（哪怕锚全换），corr 就落在 0.85~0.99。
#   本批把价量腿整体换族（窗口 / 算子 / 基准价 / 腿数全部变），锚组固定为 A_PST 不动，
#   这样"锚"与"PV"两个变量就分离开了。
# 保留 w152 系列已验证的参数：decay=10、PV 权重 1.25、/cap、SUBINDUSTRY、truncation 0.08
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'
R_ = lambda x: f'rank({x})'

A_PST = ['fnd6_pstkl', 'fnd6_txs', 'fnd6_mfmq_mibtq', 'fnd6_lqpl1']
ANCH = f'1.5*{G("fnd6_pstkl/cap")} + {G("fnd6_txs/cap")} + {G("fnd6_mfmq_mibtq/cap")} + {G("fnd6_lqpl1/cap")}'

C = [
 # 换窗口
 ('w153_a', f'{ANCH} + 1.25*{G("-ts_delta(close, 5)")} + 1.25*{G("volume/ts_mean(volume, 90)")}', BASE()),
 # 换基准价 + 长窗（vwap→close，窗口拉长）
 ('w153_b', f'{ANCH} + 1.25*{G("-ts_delta(vwap, 10)")} + 1.25*{G("volume/ts_mean(volume, 60)")}', BASE()),
 # 不用 group_rank，改用裸 rank（截面形态完全不同）
 ('w153_c', f'{ANCH} + 1.25*{R_("-ts_delta(vwap, 5)")} + 1.25*{R_("volume/ts_mean(volume, 120)")}', BASE()),
 # 均值回复型价量腿（不用动量）
 ('w153_d', f'{ANCH} + 1.25*{G("-(close - ts_mean(close, 20))/ts_std_dev(returns, 20)")} + 1.25*{G("volume/ts_mean(volume, 120)")}', BASE()),
 # 三条价量腿（摊薄单一 PV 腿的权重占比）
 ('w153_e', f'{ANCH} + 0.9*{G("-ts_delta(close, 5)")} + 0.9*{G("-ts_delta(close, 20)")} + 0.9*{G("volume/ts_mean(volume, 60)")}', BASE()),
 # ts_rank 形态的价量腿
 ('w153_f', f'{ANCH} + 1.25*{G("ts_rank(close, 20)")} + 1.25*{G("ts_rank(volume, 20)")}', BASE()),
 # 只用一条价量腿 + 一条冷锚差分腿（PV 占比降到 1/6）
 ('w153_g', f'{ANCH} + {G("ts_av_diff(fnd6_optlifeq/cap, 45)")} + 1.25*{G("-ts_delta(close, 5)")} + 1.25*{G("volume/ts_mean(volume, 90)")}', BASE()),
 # 价量腿用 vwap/close 相对量（不同构）
 ('w153_h', f'{ANCH} + 1.25*{G("-(vwap/close - 1)")} + 1.25*{G("volume/ts_mean(volume, 120)")}', BASE()),
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
    print('batch153 done', flush=True)
