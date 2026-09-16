# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch145 = 修正版 A/B：**只换字段，权重全 1.0**（batch144 误给新腿加了 1.5，对比被污染）
# 基准 = w141_a（rKOKjQP8）：SF 4.11 / S 2.77 / tS 2.67 / corr 0.7993（撞 0mR2K6lr）
#   w141_a = G(回购/cap) + G(-无形资产/cap) + G(ts_delta(scl12_sentiment,22))
#            + G(ts_av_diff(cash/cap,45)) + G(ts_av_diff(cashflow_op/cap,45))
#            + 0.75*G(-ts_delta(close,10)) + 0.75*G(volume/ts_mean(volume,120))     decay=1
# 本批只动「前两条独有腿」的字段来源（它们是 w141_a 与池内 0mR2K6lr 共享最粗的两条），
# 其余五条腿一字不改 → 干净地测「换掉共享独有腿能否把 corr 从 0.7993 拉下 0.70」，
# 同时看质量掉多少（质量是前提，掉了就白搭）。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

# 五条不动腿（与 w141_a 逐字一致）
FIXED = (f'{G("ts_delta(scl12_sentiment, 22)")} + {G("ts_av_diff(cash/cap, 45)")} + '
         f'{G("ts_av_diff(cashflow_op/cap, 45)")} + 0.75*{G("-ts_delta(close, 10)")} + '
         f'0.75*{G("volume/ts_mean(volume, 120)")}')

def mk(u1, u2):   # 所有腿权重 1.0
    return f'{G(u1 + "/cap")} + {G(u2 + "/cap")} + ' + FIXED

C = [
 # 基准复刻（应重现 SF 4.11 / corr 0.7993，验流程一致性）
 ('w145_a', mk('authorized_stock_buyback_amount', '-annual_intangible_assets_net_carrying_value'), BASE()),
 # 换 1 号兄弟对
 ('w145_b', mk('authorized_stock_repurchase_amount', '-intangible_assets_amortization_total'), BASE()),
 # 换 2 号兄弟对
 ('w145_c', mk('value_of_shares_reacquired_period', '-intangible_assets_net_carrying_value'), BASE()),
 # 换 3 号兄弟对
 ('w145_d', mk('authorized_share_award_total', '-fn_repurchased_shares_a'), BASE()),
 # 换 4 号兄弟对（aC 较高）
 ('w145_e', mk('fnd2_a_stkrpeprogramardamt', '-fnd6_intan'), BASE()),
 # 只换第一条（回购→repurchase），第二条保留
 ('w145_f', mk('authorized_stock_repurchase_amount', '-annual_intangible_assets_net_carrying_value'), BASE()),
 # 只换第二条
 ('w145_g', mk('authorized_stock_buyback_amount', '-intangible_assets_net_carrying_value'), BASE()),
 # 两条都换成冷 fnd6 锚（彻底断开 fundamental2 共享链）
 ('w145_h', mk('fnd6_pstkl', '-fnd6_txs'), BASE()),
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
    print('batch145 done', flush=True)
