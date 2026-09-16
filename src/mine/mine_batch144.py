# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch144 = ★ 换掉 w141_a 与池内 0mR2K6lr 共享的那两条 fundamental2 腿
# 依据链（今天下午新挖出的事实）：
#   ① 池内 w103_g / 0mR2K6lr 家族的独有腿是
#        authorized_stock_buyback_amount (fundamental2, aC=8, cov=0.342)
#        annual_intangible_assets_net_carrying_value (fundamental2, aC=10, cov=0.613)
#      —— **aC=8 的字段居然有效**，推翻"aC<30 无数据"对 fundamental2 的适用（该结论只对 fnd6 极冷字段成立）
#   ② 实测 w141_a（7 腿骨架 + /cap）corr 0.7993，撞的正是 0mR2K6lr；
#      两者共享 6/7 条腿：buyback、intangible、cash45、cfoev45、close10、vol120
#      → **把 buyback 与 intangible 换成 fundamental2 同族兄弟，就断开了这条最粗的共享链**
#   ③ fundamental2 同族可换的冷字段（实测 aC / cov）：
#        authorized_stock_repurchase_amount 24 / 0.356   value_of_shares_reacquired_period 10 / 0.547
#        authorized_share_award_total        9 / 0.343   intangible_assets_net_carrying_value 18 / 0.479
#        intangible_assets_amortization_total 7 / 0.519  fn_repurchased_shares_a 182 / 0.472
#        fnd2_a_stkrpeprogramardamt         210 / 0.257  fnd6_intan 1026 / 0.5
# 保留两个前提不变：/cap 缩放（今天唯一的几何钥匙）+ 引擎腿（质量的唯一来源）+ PV 0.75
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

ENG = ['ts_av_diff(cash/cap, 45)', 'ts_av_diff(cashflow_op/cap, 45)']
PV  = ['0.75*' + G('-ts_delta(close, 10)'), '0.75*' + G('volume/ts_mean(volume, 120)')]

def mk(u1, u2, senti='ts_delta(scl12_sentiment, 22)', w1=1.5, w2=1.5, eng=ENG, pv=PV):
    legs = [f'{w1}*{G(u1 + "/cap")}', f'{w2}*{G(u2 + "/cap")}', G(senti)]
    legs += [G(e) for e in eng]
    legs += pv
    return ' + '.join(legs)

C = [
 # 换 1 号兄弟：repurchase + amortization
 ('w144_a', mk('authorized_stock_repurchase_amount', 'intangible_assets_amortization_total'), BASE()),
 # 换 2 号兄弟：value_of_shares_reacquired + intangible_assets_net_carrying_value
 ('w144_b', mk('value_of_shares_reacquired_period', 'intangible_assets_net_carrying_value'), BASE()),
 # 换 3 号兄弟：share_award + fn_repurchased_shares_a
 ('w144_c', mk('authorized_share_award_total', 'fn_repurchased_shares_a'), BASE()),
 # 换 4 号兄弟（aC 较高那两条）：stkrpeprogramardamt + fnd6_intan
 ('w144_d', mk('fnd2_a_stkrpeprogramardamt', 'fnd6_intan'), BASE()),
 # 零共享：只保留引擎腿 + PV，独有腿整组换掉且用 cold fnd6 锚
 ('w144_e', mk('authorized_stock_repurchase_amount', 'fnd6_pstkl', w1=1.5, w2=1.0), BASE()),
 # 混搭：一条 fnd2 兄弟 + 一条冷 fnd6 锚 + 情绪
 ('w144_f', mk('value_of_shares_reacquired_period', 'fnd6_txs', w1=1.5, w2=1.0), BASE()),
 # 对照：保留原 buyback/intangible 但把 sentiment 换掉 + close 窗口换（用于分离"共享腿"与"情绪腿"的贡献）
 ('w144_g', mk('authorized_stock_buyback_amount', 'annual_intangible_assets_net_carrying_value',
               senti='ts_delta(snt_buzz, 22)'), dict(BASE(), truncation=0.08)),
 # 换中性化 + 换兄弟腿
 ('w144_h', mk('authorized_stock_repurchase_amount', 'intangible_assets_amortization_total'), BASE(neut='INDUSTRY')),
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
    print('batch144 done', flush=True)
