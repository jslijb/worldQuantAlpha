# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第123轮：用「alphaCount≈0」的公共数据集字段做锚 —— 撞车概率最低的破墙弹药
#
# 依据（0915 平台实测）：
#   全平台仅 14 个数据集；fundamental2（Report Footnotes，766 字段）里有大量 alphaCount = 0~5 的字段，
#   即几乎无人用过。fnd6 侧 574 个 MATRIX 字段中也有 522 个本项目从未使用。
#   本轮目标：①验证这些极冷门字段是否有效（覆盖度是主要风险）②若有效，配合共享腿降权（batch122 已验证质量不崩）
#   即可产出 corr < 0.70 的直通候选。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

# ---- fundamental2（Report Footnotes）alphaCount≈0 字段 ----
F2 = {
 'opt_shares':   'authorized_option_shares_outstanding_count',            # aC=2
 'benefit_chg':  'benefit_obligation_service_cost_change',                # aC=2
 'cust_intang':  'customer_related_intangibles_gross_value',              # aC=2
 'db_plan_cost': 'db_plan_periodic_benefit_cost',                         # aC=2
 'doubtful':     'doubtful_accounts_provision_2',                         # aC=2
 'sbp_rsu':      'allocated_sbp_expense_rsu',                             # aC=3
 'afs_amort':    'available_for_sale_securities_amortized_cost',          # aC=3
 'dtl_gw':       'deferred_tax_liability_goodwill_intangibles',           # aC=3
 'db_interest':  'defined_benefit_plan_interest_cost',                    # aC=3
 'deriv_asset':  'derivative_asset_fair_value',                           # aC=4
}
# ---- fnd6 极冷门（batch122 已在测部分，此处换另一组）----
A = '/assets'
F6 = {
 'spcepd12': 'fnd6_newqv1300_spcepd12' + A,     # aC=38
 'xoptd':    'fnd6_newa2v1300_xoptd' + A,       # aC=132
 'mibnq':    'fnd6_newqv1300_mibnq' + A,        # aC=182
 'spiq':     'fnd6_newqv1300_spiq' + A,         # aC=196
 'tfvlq':    'fnd6_newqv1300_tfvlq' + A,        # aC=200
 'txdiq':    'fnd6_newqv1300_txdiq' + A,        # aC=227
 'tstkq':    'fnd6_newqv1300_tstkq' + A,        # aC=233
 'aul3q':    'fnd6_newqv1300_aul3q' + A,        # aC=236
}

LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
CFOB = 'bucket(rank(cashflow_op/assets), range="0.1, 1, 0.1")'
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'

def G(x, grp): return f'group_rank({x}, {grp})'

def skel(anchors, grp, w=1.0):
    """独有锚（全权） + 引擎腿/PV腿（共享部分按 w 降权；batch122 实测 w=0.5 质量不崩、换手反降）"""
    parts = [G(a, grp) for a in anchors]
    shared = [G('ts_av_diff(cash/assets, 45)', grp),
              G('ts_av_diff(cashflow_op/enterprise_value, 45)', grp),
              G('-ts_delta(close, 2)', grp),
              G('volume/ts_mean(volume, 60)', grp)]
    if w != 1.0:
        shared = [f'{w}*{s}' for s in shared]
    return ' + '.join(parts + shared)

C = [
 # ---- 组1：fundamental2 极冷门脚注字段做锚（aC=2~4）----
 ('w123_a', skel([F2['opt_shares'], F2['benefit_chg'], F2['cust_intang']], LB, 0.5), BASE()),
 ('w123_b', skel([F2['db_plan_cost'], F2['doubtful'], F2['sbp_rsu']], LB, 0.5), BASE()),
 ('w123_c', skel([F2['afs_amort'], F2['dtl_gw'], F2['db_interest'], F2['deriv_asset']], LB, 0.5), BASE()),
 # ---- 组2：fnd2 + fnd6 冷门混搭 ----
 ('w123_d', skel([F2['cust_intang'], F2['sbp_rsu'], F6['spcepd12'], F6['xoptd']], LB, 0.5), BASE()),
 ('w123_e', skel([F2['opt_shares'], F2['doubtful'], F6['mibnq'], F6['spiq']], CFOB, 0.5), BASE()),
 # ---- 组3：纯 fnd6 冷门（对照组，看 fnd2 是否真比 fnd6 更有效）----
 ('w123_f', skel([F6['spcepd12'], F6['xoptd'], F6['mibnq'], F6['spiq']], LB, 0.5), BASE()),
 ('w123_g', skel([F6['tfvlq'], F6['txdiq'], F6['tstkq'], F6['aul3q']], VOLB, 0.5), BASE()),
 # ---- 组4：更激进降权（0.35）——
 ('w123_h', skel([F2['opt_shares'], F2['benefit_chg'], F2['cust_intang']], LB, 0.35), BASE()),
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
        print(f'{cid} 已有产出，跳过', flush=True); return
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
        print(f'{cid} FAIL {json.dumps(j)[:300]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} 多={b.get('longCount')} 空={b.get('shortCount')} FAIL={fa}", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch123 done', flush=True)
