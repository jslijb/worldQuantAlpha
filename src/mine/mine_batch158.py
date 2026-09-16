# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch158 = 【新数据轴腿库批】把 4 个从未用过的数据集接进来当"错开腿"
#
# 动机（0916 PM）：已证实配方 = **质量引擎腿 + 错开腿**。
#   错开腿原本只有老族价量腿（ts_rank(returns,20) / Amihud），但今天靠它连提 3 条后
#   该区间迅速被自己的入池 alpha 填满（兄弟候选互撞 0.98+）。
#   → 必须引入**池子里完全不存在的数据轴**。
#   平台 USA/TOP3000/delay1 共 14 个数据集，其中 4 个从未在本项目出现过：
#     option9（期权分析 74 字段 / aC 73k）、model51（系统风险 16 字段 / 42k）、
#     news18（Ravenpack 新闻 121 字段 / 56k）、pv13（关系数据 165 字段 / 161k）
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'

LEGS = {
 # ---- option9：期权流/隐含价位（经典 put-call ratio 与隐含远期）----
 'K_pcr10':   G('pcr_vol_10'),
 'K_pcrall':  G('pcr_oi_all'),
 'K_pcr30':   G('pcr_oi_30'),
 'K_fwd90':   G('forward_price_90/close - 1'),
 'K_fwd30':   G('forward_price_30/close - 1'),
 'K_be60':    G('option_breakeven_60/close - 1'),
 'K_cbe90':   G('call_breakeven_90/close - 1'),
 'K_carry':   G('forward_price_90/forward_price_30 - 1'),
 # ---- model51：系统性风险 / beta / 相关性 ----
 'K_beta60':  G('beta_last_60_days_spy'),
 'K_beta30':  G('beta_last_30_days_spy'),
 'K_unsys30': G('unsystematic_risk_last_30_days'),
 'K_sys30':   G('systematic_risk_last_30_days'),
 'K_corr90':  G('correlation_last_90_days_spy'),
 'K_unsys360':G('unsystematic_risk_last_360_days'),
 # ---- news18：MATRIX 型情绪分（VECTOR 型需 vec_avg，这里只用 MATRIX）----
 'K_esent':   G('mean_equity_sentiment_score'),
 'K_impact':  G('mean_news_impact_projection'),
 'K_novel':   G('mean_event_novelty_score'),
 'K_comp':    G('mean_composite_sentiment_score'),
 # ---- pv13：客户/竞争对手关系 ----
 'K_cust':    G('pv13_custretsig_retsig'),
 'K_page':    G('pv13_com_page_rank'),
 'K_auth':    G('pv13_com_rk_au'),
 'K_focus':   G('primary_sector_focused_company_count'),
 # ---- 对照组：换 industry 分组，看分组本身能否错开 ----
 'K_cfoI':    GI('ts_av_diff(cashflow_op/enterprise_value,45)'),
 'K_accI':    GI('fn_accrued_liab_curr_a/assets'),
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
        print(cid, 'REJECT', r.status_code, r.text[:200], flush=True); return None
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
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
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
    print('batch158 done', flush=True)
