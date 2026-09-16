# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch157 = 【腿库扩容批二】26 条新腿，扩大可搜索几何
#
# 动机（0916 PM）：`leg_lab.py search` 已在 26 条腿的空间里搜出
#   S≈3.3 / maxcorr≈0.65 / SF≈6.9 的组合（pwRwWoJ3 已入池，selfCorr 0.6474）。
#   但同一个"6 腿核心"只能吃一口：兄弟候选入池后互相 0.98+ 必撞。
#   → 每提交一个，可搜索区就缩小一块。**必须同步扩容腿库**。
#
# 本批两条扩容思路：
#   A. 锚腿换【分母 + 字段】：去掉 /cap（已知会把所有锚归一成市值因子），改用 /assets 与
#      池中已被证明低相关的字段（fnd6_tfvce / lnoq / txtubpospinc / intc / glcea12 …）
#   B. 锚腿换【算子 + 分组】：zscore / quantile 替代 group_rank，industry 替代 subindustry
#   C. 价量腿扩【老族窗口与算子】：ts_rank/Amihud 的 5/20/60 档、ts_decay_linear、ts_zscore、ts_corr
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G  = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'

LEGS = {
 # ---- A. 新字段（/assets 分母，避开 /cap 的市值因子） ----
 'M_tfvce': G('fnd6_tfvce/assets'),
 'M_lnoq':  G('fnd6_newqv1300_lnoq/assets'),
 'M_txp':   G('fnd6_txtubpospinc/assets'),
 'M_g12':   G('fnd6_newqv1300_glcea12/assets'),
 'M_tstk':  G('fnd6_tstkc/assets'),
 'M_intc':  G('fnd6_intc/assets'),
 'M_liab':  G('liabilities_curr/assets'),
 'M_opex':  G('operating_expense/assets'),
 'M_debt':  G('debt_st/assets'),
 'M_ni':    G('-(fnd6_newa2v1300_ni - cashflow_op)/assets'),
 'M_revt':  G('fnd6_mfma2_revt/assets'),
 'M_tot':   G('anl4_fs_detail_estimate_1qf_v4_nd_totassets_mean/assets'),
 'M_capex': G('-anl4_fs_detail_estimates_advanced_af_nd_capex_median/assets'),
 # ---- B. 换算子 / 换分组 ----
 'M_cashZ': 'zscore(ts_av_diff(cash/assets,45))',
 'M_cfoQ':  'quantile(ts_av_diff(cashflow_op/enterprise_value,45))',
 'M_xrI':   GI('fnd6_xrent/assets'),
 'M_accI':  GI('fn_accrued_liab_curr_a/assets'),
 'M_intI':  GI('-annual_intangible_assets_net_carrying_value/assets'),
 # ---- C. 价量腿扩容（老族窗口/算子） ----
 'N_tr5':   G('-ts_rank(returns, 5)'),
 'N_tr60':  G('-ts_rank(returns, 60)'),
 'N_am60':  G('-ts_mean(abs(returns)/volume, 60)'),
 'N_rvol':  G('-ts_std_dev(returns, 60)'),
 'N_rev5':  G('-ts_mean(returns, 5)'),
 'N_vcorr': G('-ts_corr(close, volume, 20)'),
 'N_dl20':  G('-ts_decay_linear(returns, 20)'),
 'N_z20':   G('-ts_zscore(returns, 20)'),
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
    print('batch157 done', flush=True)
