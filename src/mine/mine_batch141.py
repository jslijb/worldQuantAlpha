# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch141 = ★ 把 /cap 几何钥匙用在「高质量家族」上（今日最高期望值的一批）
# 依据链：
#   ① batch132 实证：/cap 缩放是唯一能把 corr 从 ~0.85 打到 0.6999 的动作（kqoq0zed 直通入池）
#      —— 但它当时用在一个**低质量**骨架（SF 天花板 3.99）上，入池那条只有 3.85
#   ② 未提交库存里质量最高的家族是 w97~w103 的 7 腿骨架（SF 5.32~5.60，S 3.45~3.55，tS 3.5+）：
#        L1 group_rank(authorized_stock_buyback_amount/assets)
#        L2 group_rank(-annual_intangible_assets_net_carrying_value/assets)
#        L3 group_rank(ts_delta(scl12_sentiment, 22))
#        L4 group_rank(ts_av_diff(cash/assets, 45))
#        L5 group_rank(ts_av_diff(cashflow_op/enterprise_value, 45))
#        L6 group_rank(-ts_delta(close, 10))
#        L7 rank(volume/ts_mean(volume, 120))          decay=1, neut=SUBINDUSTRY
#      它的实测 corr = 0.9719（撞 0mR2K6lr，同骨架）→ 质量够、几何撞
#   ③ 本批假设：**高质量骨架 + /cap 缩放 = 质量保住 + 几何错开**
#      （batch135 用低质量骨架试过 /cap+引擎 → corr 0.96，但那是 5 腿构型，与本批 7 腿构型不同）
# 梯度：全腿换缩放 → 部分换 → 换中性化 → 换分组 → 换 PV 窗口，用于定位分界点
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GB = lambda x, b: f'group_rank({x}, {b})'

# 7 腿骨架的三个缩放版本（同一骨架，只换分母）
def skel(size, extra=None):
    L = [G(f'authorized_stock_buyback_amount/{size}'),
         G(f'-annual_intangible_assets_net_carrying_value/{size}'),
         G('ts_delta(scl12_sentiment, 22)'),
         G(f'ts_av_diff(cash/{size}, 45)'),
         G(f'ts_av_diff(cashflow_op/{size}, 45)'),
         G('-ts_delta(close, 10)'),
         'rank(volume/ts_mean(volume, 120))']
    if extra: L.append(extra)
    return ' + '.join(L)

# 部分换：只有前两条腿与第 4 条换 /cap，第 5 条保留原始 EV 分母
MIX = ' + '.join([G('authorized_stock_buyback_amount/cap'),
                  G('-annual_intangible_assets_net_carrying_value/cap'),
                  G('ts_delta(scl12_sentiment, 22)'),
                  G('ts_av_diff(cash/cap, 45)'),
                  G('ts_av_diff(cashflow_op/enterprise_value, 45)'),
                  G('-ts_delta(close, 10)'),
                  'rank(volume/ts_mean(volume, 120))'])

VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'

C = [
 # ★ 主假设：全腿 /cap
 ('w141_a', skel('cap'), BASE()),
 ('w141_b', skel('cap'), BASE(neut='NONE')),
 ('w141_c', skel('cap'), BASE(neut='SECTOR')),
 ('w141_d', skel('cap'), BASE(neut='INDUSTRY')),
 # 部分换 /cap（保留 cashflow_op/enterprise_value 原分母）
 ('w141_e', MIX, BASE()),
 # 换其他分母
 ('w141_f', skel('sales'), BASE()),
 # 换情绪字段（scl12_sentiment → snt_buzz）+ 全 /cap
 ('w141_g', ' + '.join([G('authorized_stock_buyback_amount/cap'),
                        G('-annual_intangible_assets_net_carrying_value/cap'),
                        G('ts_delta(snt_buzz, 22)'),
                        G('ts_av_diff(cash/cap, 45)'),
                        G('ts_av_diff(cashflow_op/cap, 45)'),
                        G('-ts_delta(close, 10)'),
                        'rank(volume/ts_mean(volume, 120))']), BASE()),
 # 换 PV 窗口 + 全 /cap
 ('w141_h', ' + '.join([G('authorized_stock_buyback_amount/cap'),
                        G('-annual_intangible_assets_net_carrying_value/cap'),
                        G('ts_delta(scl12_sentiment, 22)'),
                        G('ts_av_diff(cash/cap, 45)'),
                        G('ts_av_diff(cashflow_op/cap, 45)'),
                        G('-ts_delta(close, 5)'),
                        'rank(volume/ts_mean(volume, 60))']), BASE()),
 # 换分组变量（市值波动桶）+ 全 /cap
 ('w141_i', ' + '.join([GB('authorized_stock_buyback_amount/cap', VOLB),
                        GB('-annual_intangible_assets_net_carrying_value/cap', VOLB),
                        GB('ts_delta(scl12_sentiment, 22)', VOLB),
                        GB('ts_av_diff(cash/cap, 45)', VOLB),
                        GB('ts_av_diff(cashflow_op/cap, 45)', VOLB),
                        GB('-ts_delta(close, 10)', VOLB),
                        GB('volume/ts_mean(volume, 120)', VOLB)]), BASE()),
 # 全 /cap + decay 6（原家族 decay=1，换 decay 会改换手与残差结构）
 ('w141_j', skel('cap'), BASE(delay=6)),
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
        print(f'{cid} SIM-FAIL {json.dumps(j)[:300]}', flush=True); return
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
    print('batch141 done', flush=True)
