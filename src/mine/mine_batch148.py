# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch148 = ★★ 「降换手抬 Fitness」批 —— 今天最有可能真正完成目标的一条路
# 推导（全部基于今天实测的数据，不是猜的）：
#   ① corr 与 S 强相关（同几何下）：
#        S=3.06 → corr 0.8725；S=3.02 → corr 0.8721（/EV、/sqrt(cap) 引擎）
#        S=2.77 → corr 0.7993（w141_a）
#        S=2.73 → corr 0.7829（w145_f）
#        S=2.02 → corr 0.6999（kqoq0zed，直通入池）
#      ⇒ 想过直通线（corr<0.70），S 必须压到 ~2.1 一带。
#   ② 但门槛是 **S+F ≥ 4.0**，不是单看 S。Fitness = S × sqrt(|R| / max(T, 0.125))
#      ⇒ **换手 T 越低，F 越高**，而 T 完全不动截面排序 → 不动 corr。
#   ③ kqoq0zed 实测：S=2.02 / T=0.1427 / F=1.83 / SF=3.85 —— 差 0.15。
#      若把 T 从 0.1427 压到 0.10：F ≈ 1.83 × sqrt(0.1427/0.10) = **2.19** → SF ≈ **4.21** ✅
#   ④ 降换手的弹药（历史实证有效）：`hump(x, 0.01)`、提高 decay、`trade_when(..., -1)`（保持仓位）、ts_decay_linear
#   ⇒ 本批 = **kqoq0zed 的几何一字不改**，只加降换手包裹，目标 SF≥4.0 且 corr 守住 ~0.70
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

# kqoq0zed 原式（corr 0.6999 已入池那条），decay=6
KQ = ' + '.join([
    f'1.5*{G("fnd6_txtubadjust/cap")}',
    G('fnd6_newa1v1300_aol2/cap'),
    G('fnd6_newqv1300_dpactq/cap'),
    f'0.75*{G("-ts_delta(vwap, 5)")}',
    f'0.75*{G("volume/ts_mean(volume, 120)")}',
])

# w145_f 原式（corr 0.7829 / SF 4.01）—— 高分骨架的换腿版
HQ = ' + '.join([
    G('authorized_stock_repurchase_amount/cap'),
    G('-annual_intangible_assets_net_carrying_value/cap'),
    G('ts_delta(scl12_sentiment, 22)'),
    G('ts_av_diff(cash/cap, 45)'),
    G('ts_av_diff(cashflow_op/cap, 45)'),
    f'0.75*{G("-ts_delta(close, 10)")}',
    f'0.75*{G("volume/ts_mean(volume, 120)")}',
])

C = [
 # ① kqoq0zed 几何不动，只加 hump 降换手（hump 参数扫描）
 ('w148_a', f'hump({KQ}, 0.01)', BASE()),
 ('w148_b', f'hump({KQ}, 0.005)', BASE()),
 ('w148_c', f'hump({KQ}, 0.02)', BASE()),
 # ② kqoq0zed 几何 + 提高 decay
 ('w148_d', KQ, BASE(delay=12)),
 ('w148_e', KQ, BASE(delay=20)),
 # ③ hump + 高 decay 叠加
 ('w148_f', f'hump({KQ}, 0.01)', BASE(delay=12)),
 # ④ kqoq0zed 几何 + trade_when 保持仓位（第三参 -1）
 ('w148_g', f'trade_when(volume > ts_mean(volume, 60), {KQ}, -1)', BASE()),
 # ⑤ 高分骨架版（w145_f 几何）+ hump —— 若 corr 能从 0.7829 再降
 ('w148_h', f'hump({HQ}, 0.01)', BASE()),
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
          f"T={b.get('turnover')} tS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch148 done', flush=True)
