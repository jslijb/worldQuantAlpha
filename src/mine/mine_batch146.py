# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch146 = 动「引擎腿的分母」——保住 45 窗口的质量结构，只换几何
# 现状（今日实测）：
#   w141_a  7 腿 + /cap + 引擎腿 ts_av_diff(cash/cap,45)+ts_av_diff(cashflow_op/cap,45)
#           → SF 4.11 / corr 0.7993（撞 0mR2K6lr，其腿为 cash/assets + cashflow_op/enterprise_value）
#   w145_b~e 换掉 buyback/intangible 两条独有腿 → 质量掉到 3.63~3.84（这对腿不可替代）
#   batch143 去掉引擎腿 → SF 掉到 3.50（引擎腿不可去）
# ⇒ 唯一还能动的：**引擎腿的分母**。45 天窗口是历史实证的甜点（30/60 死），不能改窗口，那就改分母。
#   分母一改，引擎腿的截面排序变了 → PnL 几何变 → 赌 corr 下 0.70 而质量不掉。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

UNIQ = f'{G("authorized_stock_buyback_amount/cap")} + {G("-annual_intangible_assets_net_carrying_value/cap")}'
SENT = G('ts_delta(scl12_sentiment, 22)')

def mk(e1, e2, sent=SENT, pv=None, g=G):
    pv = pv or [f'0.75*{G("-ts_delta(close, 10)")}', f'0.75*{G("volume/ts_mean(volume, 120)")}']
    return ' + '.join([UNIQ, sent, g(e1), g(e2)] + pv)

C = [
 # 引擎腿换分母：/sales
 ('w146_a', mk('ts_av_diff(cash/sales, 45)', 'ts_av_diff(cashflow_op/sales, 45)'), BASE()),
 # 引擎腿换分母：/enterprise_value（其中第二条即池内原始腿，作对照）
 ('w146_b', mk('ts_av_diff(cash/enterprise_value, 45)', 'ts_av_diff(cashflow_op/enterprise_value, 45)'), BASE()),
 # 引擎腿换分母：/sqrt(cap)
 ('w146_c', mk('ts_av_diff(cash/sqrt(cap), 45)', 'ts_av_diff(cashflow_op/sqrt(cap), 45)'), BASE()),
 # 引擎腿换分母：/assets（回到池子几何，作"反向"对照——预期 corr 升）
 ('w146_d', mk('ts_av_diff(cash/assets, 45)', 'ts_av_diff(cashflow_op/assets, 45)'), BASE()),
 # 混搭分母：一条 /cap 一条 /sales
 ('w146_e', mk('ts_av_diff(cash/cap, 45)', 'ts_av_diff(cashflow_op/sales, 45)'), BASE()),
 # 中性化 NONE（在 w141_a 构型上，此前两批都没跑到）
 ('w146_f', mk('ts_av_diff(cash/cap, 45)', 'ts_av_diff(cashflow_op/cap, 45)'), BASE(neut='NONE')),
 # 换 PV 窗口（close5 + vol60）
 ('w146_g', mk('ts_av_diff(cash/cap, 45)', 'ts_av_diff(cashflow_op/cap, 45)',
               pv=[f'0.75*{G("-ts_delta(close, 5)")}', f'0.75*{G("volume/ts_mean(volume, 60)")}']), BASE()),
 # 换情绪字段 + /sales 引擎
 ('w146_h', mk('ts_av_diff(cash/sales, 45)', 'ts_av_diff(cashflow_op/sales, 45)',
               sent=G('ts_delta(snt_buzz, 22)')), BASE()),
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
    print('batch146 done', flush=True)
