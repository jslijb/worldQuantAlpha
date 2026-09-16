# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch147 = 「包裹算子」批：quantile / trade_when / zscore 叠在 /cap 高质量骨架上
# 依据链：
#   ① 未提交库质量最高两条用的都是**包裹算子**，不是换数据：
#        w100_c `wpYkX9Rx` SF 5.47  = trade_when(ts_std_dev(returns,20) > ts_std_dev(returns,60), <6腿骨架>, -1)
#        w97_c  `xAYpO9qn` SF 5.60  = quantile(<6腿骨架>, driver="gaussian")
#      → 包裹算子能加质量（5.32 → 5.47/5.60）
#   ② 包裹算子同时改变**时间序列门控/分布变换**，是比换锚更底层的几何变量（换锚已被证明无效）
#   ③ 现状：w141_a（/cap 高质量骨架，无包裹）SF 4.11 / corr 0.7993
#   → 赌：包裹算子 + /cap 能同时守住 SF≥4.0 并把 corr 打下去
# 基准构型 = w141_a 逐字复刻（全腿 1.0 权，PV 为 group_rank(-ts_delta(close,10)) 与 rank(volume/ts_mean(volume,120))）
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

BASE7 = ' + '.join([
    G('authorized_stock_buyback_amount/cap'),
    G('-annual_intangible_assets_net_carrying_value/cap'),
    G('ts_delta(scl12_sentiment, 22)'),
    G('ts_av_diff(cash/cap, 45)'),
    G('ts_av_diff(cashflow_op/cap, 45)'),
    G('-ts_delta(close, 10)'),
    'rank(volume/ts_mean(volume, 120))',
])

C = [
 # ① quantile 包裹（复刻 w97_c 手法 + /cap）
 ('w147_a', f'quantile({BASE7}, driver="gaussian")', BASE()),
 ('w147_b', f'quantile({BASE7}, driver="uniform")', BASE()),
 # ② trade_when 门控（复刻 w100_c / w100_g 手法 + /cap）
 ('w147_c', f'trade_when(ts_std_dev(returns, 20) > ts_std_dev(returns, 60), {BASE7}, -1)', BASE()),
 ('w147_d', f'trade_when(volume > ts_mean(volume, 60), {BASE7}, -1)', BASE()),
 # ③ zscore 包裹（完全不用 group_rank 的求和形态）
 ('w147_e', ' + '.join([
     f'zscore(authorized_stock_buyback_amount/cap)', f'zscore(-annual_intangible_assets_net_carrying_value/cap)',
     f'zscore(ts_delta(scl12_sentiment, 22))', f'zscore(ts_av_diff(cash/cap, 45))',
     f'zscore(ts_av_diff(cashflow_op/cap, 45))', f'zscore(-ts_delta(close, 10))', f'zscore(volume/ts_mean(volume, 120))']), BASE()),
 # ④ quantile 包裹 + 门控（两个一起上）
 ('w147_f', f'quantile(trade_when(ts_std_dev(returns, 20) > ts_std_dev(returns, 60), {BASE7}, -1), driver="gaussian")', BASE()),
 # ⑤ 换 PV 腿（保住骨架其余 5 腿，只动价量两条）
 ('w147_g', ' + '.join([
     G('authorized_stock_buyback_amount/cap'), G('-annual_intangible_assets_net_carrying_value/cap'),
     G('ts_delta(scl12_sentiment, 22)'), G('ts_av_diff(cash/cap, 45)'), G('ts_av_diff(cashflow_op/cap, 45)'),
     G('-ts_delta(vwap, 5)'), 'rank(volume/ts_mean(volume, 90))']), BASE()),
 # ⑥ 骨架加第 8 腿（均值回复腿），稀释共享成分
 ('w147_h', f'{BASE7} + {G("-(close - ts_mean(close, 5))/ts_std_dev(returns, 20)")}', BASE()),
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
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch147 done', flush=True)
