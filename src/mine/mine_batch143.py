# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch143 = ★ 去掉引擎腿、用冷锚顶位（本日第 3 条路，从数据反推出来的）
# 依据（今天实测出来的因果链）：
#   w141_a = 高质量 7 腿骨架 + /cap（有 cash/cap + cfoev/cap 两条引擎腿）→ SF 4.11 / corr 0.7993
#   kqoq0zed = /cap 冷锚三腿 + PV（**没有引擎腿**）            → SF 3.85 / corr 0.6999
#   ⇒ 引擎腿贡献 ~+0.26 SF 与 ~+0.10 corr。目标是**把 0.10 的相关性退回去，只留 0.26 里的够用部分**。
# 手段：删掉 cash/cfoev 两条引擎腿，用「冷锚静态腿 + 冷锚 45 差分腿」补回质量，
#       锚全部取自 COLD_FIELD_WHITELIST 且与 kqoq0zed 用的 TXA/AOL/DPQ 不同构。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'

BUY='authorized_stock_buyback_amount'; INT='-annual_intangible_assets_net_carrying_value'
PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'; LQP='fnd6_lqpl1'
STK='fnd6_stkcpa'; NOP='fnd6_newa2v1300_nopi'; CIT='fnd6_newqv1300_citotalq'
TXP='fnd6_txtubposinc'; INV='fnd6_newqv1300_invrmq'; RDI='fnd6_newqv1300_rdipdq'
OPT='fnd6_optlifeq'; ANO='fnd6_newa1v1300_ano'

UNIQ = [f'1.5*{G(BUY+"/cap")}', f'1.5*{G(INT+"/cap")}', G('ts_delta(scl12_sentiment, 22)')]
PV   = [f'0.75*{G("-ts_delta(close, 10)")}', f'0.75*{G("volume/ts_mean(volume, 120)")}']

def j(legs): return ' + '.join(legs)

C = [
 # ★ 主假设：独有三腿 + PV，**完全不要引擎腿**（kqoq0zed 的构型，但换了独有腿与权重）
 ('w143_a', j(UNIQ + PV), BASE()),
 # 独有三腿 + 两条冷锚静态腿（顶掉引擎腿的位置）
 ('w143_b', j(UNIQ + [f'{G(PST+"/cap")}', f'{G(TXS+"/cap")}'] + PV), BASE()),
 # 独有三腿 + 两条冷锚 45 差分腿（保留引擎的时序结构，换数据源）
 ('w143_c', j(UNIQ + [f'0.5*{G("ts_av_diff("+PST+"/cap, 45)")}', f'0.5*{G("ts_av_diff("+TXS+"/cap, 45)")}'] + PV), BASE()),
 # 只留一条引擎腿（另一半换冷锚差分）→ 定位引擎腿的边际代价
 ('w143_d', j(UNIQ + [f'0.5*{G("ts_av_diff(cash/cap, 45)")}', f'0.5*{G("ts_av_diff("+INV+"/cap, 45)")}'] + PV), BASE()),
 # 换分母（/cap 之外的几何）
 ('w143_e', j([f'1.5*{G(BUY+"/sqrt(cap)")}', f'1.5*{G(INT+"/sqrt(cap)")}', G('ts_delta(scl12_sentiment, 22)'),
               f'0.75*{G("-ts_delta(close, 10)")}', f'0.75*{G("volume/ts_mean(volume, 120)")}']), BASE()),
 ('w143_f', j([f'1.5*{G(BUY+"/ts_mean(cap, 60)")}', f'1.5*{G(INT+"/ts_mean(cap, 60)")}', G('ts_delta(scl12_sentiment, 22)'),
               f'0.75*{G("-ts_delta(close, 10)")}', f'0.75*{G("volume/ts_mean(volume, 120)")}']), BASE()),
 # 五条冷锚（不给独有腿加权）+ PV，最大化与池子的差别
 ('w143_g', j([f'{G(MIB+"/cap")}', f'{G(LQP+"/cap")}', f'{G(STK+"/cap")}', f'{G(NOP+"/cap")}',
               G('ts_delta(scl12_sentiment, 22)')] + PV), BASE()),
 # /cap + 中性化 NONE（batch141 未跑完的那一格）
 ('w143_h', j(UNIQ + PV), BASE(neut='NONE')),
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
    print('batch143 done', flush=True)
