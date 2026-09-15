# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第121轮：论文16移植配方的变体铺开
# 胜出配方（batch120 w120_r / MP1rjMj9：S2.53 F1.83 SF4.36 T20.89% testS2.08 无FAIL）：
#   3 锚(fnd6冷门科目) + 2 引擎腿(cash45/cfoev45) + PV腿(-ts_delta(close,2)) + 门控分析师腿
#   门控分析师腿 = if_else(rank(ts_regression(rank(returns), rank(vec_avg(评级字段)), 120, lag=0, rettype=2))>0.6, -ts_av_diff(vec_avg(评级字段),120), 0)
# 关键教训（对照 batch120 的 6 腿版本）：分析师腿不能顶替 PV 腿，只能叠加 —— PV 腿是验证期稳定性来源。
# 本轮：换锚/换桶/换字段/权重/rettype，验证配方可复制性与 rettype 语义
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

A = '/assets'
TSTKC='fnd6_tstkc'+A; LIFR='fnd6_lifr'+A; INTC='fnd6_intc'+A
CICURR='fnd6_cicurr'+A; TFVCE='fnd6_tfvce'+A; GLCE='fnd6_newqv1300_glcea12'+A
XOPTQ='fnd6_newqv1300_xoptq'+A

CAPR = 'bucket(rank(ts_rank(cap, 250)), range="0.1, 1, 0.1")'
LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
SALEB= 'bucket(rank(sales/assets), range="0.1, 1, 0.1")'
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'
CFOB = 'bucket(rank(cashflow_op/assets), range="0.1, 1, 0.1")'

def G(x, grp): return f'group_rank({x}, {grp})'

RV_B = 'vec_avg(anl4_basicdetailrec_ratingvalue)'      # aC=574
RV_D = 'vec_avg(anl4_fs_detail_rec_v4_nd_estimate)'   # aC=24  最冷门
RV_E = 'vec_avg(anl4_eaz2lrec_ratingvalue)'           # aC=5886 热

def gated(rv, rettype=2):
    return (f'if_else(rank(ts_regression(rank(returns), rank({rv}), 120, lag=0, rettype={rettype}))>0.6,'
            f' -ts_av_diff({rv}, 120), 0)')

def skel7(anchors, grp, analyst_term, w=1.0):
    """3 锚 + 2 引擎腿 + PV 腿 + 分析师腿（w120_r 已验证的 7 腿结构）"""
    parts = [G(a, grp) for a in anchors]
    parts += [G('ts_av_diff(cash/assets, 45)', grp), G('ts_av_diff(cashflow_op/enterprise_value, 45)', grp)]
    parts += [G('-ts_delta(close, 2)', grp)]
    parts += [('' if w == 1.0 else f'{w}*') + G(analyst_term, grp)]
    return ' + '.join(parts)

C = [
 # 主攻：换锚换桶，验证配方可复制性（一个配方只能吃一口，必须一次多备）
 ('w121_a', skel7([TSTKC, CICURR, TFVCE], CAPR,  gated(RV_B)), BASE()),
 ('w121_b', skel7([INTC, LIFR, CICURR],   LB,    gated(RV_B)), BASE()),
 ('w121_c', skel7([TSTKC, CICURR, INTC],  SALEB, gated(RV_B)), BASE()),
 ('w121_d', skel7([TSTKC, CICURR, INTC],  VOLB,  gated(RV_D)), BASE()),
 ('w121_e', skel7([GLCE, XOPTQ, TSTKC],   CFOB,  gated(RV_B)), BASE()),
 ('w121_f', skel7([TSTKC, CICURR, INTC],  CAPR,  gated(RV_E)), BASE()),   # 主流字段对照
 # 权重对比：分析师腿降 0.5（0913 第五斧手法）
 ('w121_g', skel7([TSTKC, CICURR, INTC],  CAPR,  gated(RV_B), 0.5), BASE()),
 # rettype 语义定位（同一结构只换 rettype）
 ('w121_h', skel7([TSTKC, CICURR, INTC],  CAPR,  gated(RV_B, 0)), BASE()),
 ('w121_i', skel7([TSTKC, CICURR, INTC],  CAPR,  gated(RV_B, 3)), BASE()),
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
        print(f'{cid} FAIL {json.dumps(j)[:250]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa}", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch121 done', flush=True)
