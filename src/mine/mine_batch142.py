# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch142 = ★ 双杠杆叠加：高质量 7 腿骨架 + /cap 缩放 + 共享腿降权
# 依据链（本批是今天最接近成功的一条路）：
#   ① batch141 实测：把 /cap 用在高质量 7 腿骨架（原 SF 5.32）上
#      → w141_a **SF 4.11 / S 2.77 / tS 2.67，质量闸门全过**，corr 从 0.9719 降到 **0.7993**（降 0.17）
#      → 差 0.10 未过直通线
#   ② w85_a 实证过的第二个独立杠杆：共享腿降权 0.5（把 corr 从 0.754 压到 0.6803）
#   ③ 叠加假设：/cap（换分母几何）+ 共享腿降权（改 PnL 构成）→ 目标 corr < 0.70
# 骨架（w103_g 家族，decay=1, neut=SUBINDUSTRY）：
#   独有腿 L1 回购/assets  L2 -无形资产/assets  L3 ts_delta(scl12_sentiment,22)
#   共享腿 L4 ts_av_diff(cash/assets,45)  L5 ts_av_diff(cashflow_op/EV,45)  L6 -ts_delta(close,10)
#   引擎  L7 rank(volume/ts_mean(volume,120))
# 本批：分母统一换 /cap，独有腿加权、共享腿降权，另外单独替换三条共享腿做对照
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'

def build(cap=True, uniq=1.5, shared=0.5, pv=0.75, senti='scl12_sentiment',
          l4=None, l5=None, l6=None, pvleg=None, group=None):
    d = 'cap' if cap else 'sales'
    L4 = l4 or f'ts_av_diff(cash/{d}, 45)'
    L5 = l5 or f'ts_av_diff(cashflow_op/{d}, 45)'
    L6 = l6 or '-ts_delta(close, 10)'
    P7 = pvleg or 'volume/ts_mean(volume, 120)'
    R = (lambda x: f'group_rank({x}, subindustry)') if group is None else (lambda x: f'group_rank({x}, {group})')
    legs = [f'{uniq}*{R("authorized_stock_buyback_amount/"+d)}',
            f'{uniq}*{R("-annual_intangible_assets_net_carrying_value/"+d)}',
            f'{uniq}*{R("ts_delta("+senti+", 22)")}',
            f'{shared}*{R(L4)}',
            f'{shared}*{R(L5)}',
            f'{shared}*{R(L6)}',
            f'{pv}*{R(P7)}']
    return ' + '.join(legs)

C = [
 # ★ 双杠杆叠加：/cap + 共享腿降权（w85_a 手法）
 ('w142_a', build(cap=True, uniq=1.5, shared=0.5, pv=0.75), BASE()),
 ('w142_b', build(cap=True, uniq=2.0, shared=0.5, pv=1.0), BASE()),
 ('w142_c', build(cap=True, uniq=1.5, shared=0.35, pv=0.75), BASE()),
 # 换中性化（/cap + 非 SUBINDUSTRY）
 ('w142_d', build(cap=True, uniq=1.5, shared=0.5, pv=0.75), BASE(neut='NONE')),
 ('w142_e', build(cap=True, uniq=1.5, shared=0.5, pv=0.75), BASE(neut='INDUSTRY')),
 # 单条替换共享腿（定位哪条共享腿是 corr 主犯）
 ('w142_f', build(cap=True, uniq=1.5, shared=0.5, pv=0.75, l4='ts_av_diff(fnd6_pstkl/cap, 45)'), BASE()),
 ('w142_g', build(cap=True, uniq=1.5, shared=0.5, pv=0.75, l5='ts_av_diff(fnd6_txs/cap, 45)'), BASE()),
 ('w142_h', build(cap=True, uniq=1.5, shared=0.5, pv=0.75, l6='-ts_delta(close, 5)', pvleg='volume/ts_mean(volume, 60)'), BASE()),
 # 换情绪字段 + 双杠杆
 ('w142_i', build(cap=True, uniq=1.5, shared=0.5, pv=0.75, senti='snt_buzz'), BASE()),
 # 换分母 + 双杠杆
 ('w142_j', build(cap=False, uniq=1.5, shared=0.5, pv=0.75), BASE()),
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
    print('batch142 done', flush=True)
