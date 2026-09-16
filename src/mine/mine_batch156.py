# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch156 = 【腿库批】逐条跑单腿，建"腿 PnL 库"
#
# 依据（0916）：
#   1) 本地 PnL corr 已验证，误差 ±0.02（w154_b 0.8707 vs 平台 0.8769；akLp3pzW 0.8053 vs 0.8036）
#   2) batch154 六条互相关 0.97~0.9996 → PnL 几乎只由价量腿决定，锚腿贡献小
#   3) 池中高质低相关成员（E5vkQ76G SF4.11/max0.582、883OXpJl SF4.26/max0.666、
#      gJQMxZoJ SF5.07/max0.647）共用价量腿 = -ts_rank(returns,20) 与 Amihud -ts_mean(abs(returns)/volume,20)
#      → 【老族价量腿】是没被挤爆的几何
#   4) 若 PnL 对腿近似线性，则 sim(单腿) 之后可离线拼装任意组合并本地算 corr/S，筛选零成本
#
# 本批 = 26 条单腿，全部 base 设置一致（decay10/subindustry/trunc0.08/delay1），
#        拼装近似性用 w154_b（=A4+PVB）做对照验证，见 src/analysis/leg_lab.py
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

LEGS = {
 # ---- 锚 / 质量腿 ----
 'L_pst':  G('fnd6_pstkl/cap'),
 'L_txs':  G('fnd6_txs/cap'),
 'L_mib':  G('fnd6_mfmq_mibtq/cap'),
 'L_lqp':  G('fnd6_lqpl1/cap'),
 'L_txt':  G('fnd6_txtubadjust/cap'),
 'L_aol':  G('fnd6_newa1v1300_aol2/cap'),
 'L_dpa':  G('fnd6_newqv1300_dpactq/cap'),
 'L_cash': G('ts_av_diff(cash/assets,45)'),
 'L_cfo':  G('ts_av_diff(cashflow_op/enterprise_value,45)'),
 'L_ac':   G('ts_av_diff(assets_curr/assets,30)'),
 'L_acc':  G('fn_accrued_liab_curr_a/assets'),
 'L_bb':   G('authorized_stock_buyback_amount/assets'),
 'L_int':  G('-annual_intangible_assets_net_carrying_value/assets'),
 'L_xr':   G('fnd6_xrent/assets'),
 # ---- 价量腿（新族：反转型） ----
 'P_c5':   G('-ts_delta(close, 5)'),
 'P_c2':   G('-ts_delta(close, 2)'),
 'P_c20':  G('-ts_delta(close, 20)'),
 'P_vw5':  G('-ts_delta(vwap, 5)'),
 'P_v90':  G('volume/ts_mean(volume, 90)'),
 'P_v120': G('volume/ts_mean(volume, 120)'),
 'P_v60':  G('volume/ts_mean(volume, 60)'),
 # ---- 价量腿（老族：排名型 / Amihud / 隔夜） ----
 'P_tr20': G('-ts_rank(returns, 20)'),
 'P_am20': G('-ts_mean(abs(returns)/volume, 20)'),
 'P_on5':  G('-ts_mean(open/ts_delay(close,1) - 1, 5)'),
 'P_sd20': G('-ts_std_dev(returns, 20)'),
 'P_vd':   G('(close - vwap)/vwap'),
}

C = [(cid, expr, BASE()) for cid, expr in LEGS.items()]

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
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} FAIL={fa}", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch156 done', flush=True)
