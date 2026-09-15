# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第120轮：Research Paper 16（Birru/Gokkaya/Liu/Stulz, JF 2022 分析师短期交易思路）移植验证
# 设计：w116_d 六腿骨架保留 3 锚 + 2 引擎腿，把最拥挤的 PV 腿(-ts_delta(close,2))换成「分析师评级腿」
# 改进点（对应论文作者两个问题）：①离散评级先 ts_mean/门控平滑 ②用 if_else(...,0) 取代 :nan 避免权重集中
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
TFVCE='fnd6_tfvce'+A; CICURR='fnd6_cicurr'+A; GLCE='fnd6_newqv1300_glcea12'+A

CAPR = 'bucket(rank(ts_rank(cap, 250)), range="0.1, 1, 0.1")'   # w116_d 已验证桶
SALEB= 'bucket(rank(sales/assets), range="0.1, 1, 0.1")'        # w116_e 已验证桶
LTB  = 'bucket(rank(debt_lt/assets), range="0.1, 1, 0.1")'      # 新桶

def G(x, grp): return f'group_rank({x}, {grp})'

def eng2(grp, cw=45, fw=45):
    """引擎两腿（保留）：cash45 + cfoev45。PV 腿让位给分析师腿。"""
    return [G(f'ts_av_diff(cash/assets, {cw})', grp),
            G(f'ts_av_diff(cashflow_op/enterprise_value, {fw})', grp)]

def build3(anchors, grp, extra):
    return ' + '.join([G(a, grp) for a in anchors] + eng2(grp) + [G(extra, grp)])

# ---- 分析师评级腿（论文移植；字段为 VECTOR，必须 vec_avg 聚合）----
RV_B = 'vec_avg(anl4_basicdetailrec_ratingvalue)'          # aC=574  冷门
RV_D = 'vec_avg(anl4_fs_detail_rec_v4_nd_estimate)'       # aC=24   最冷门
RV_E = 'vec_avg(anl4_eaz2lrec_ratingvalue)'               # aC=5886 主流(对照)

leg_rating_B = f'-ts_av_diff({RV_B}, 120)'
leg_rating_D = f'-ts_av_diff({RV_D}, 120)'
leg_rating_E = f'-ts_av_diff({RV_E}, 120)'
# 论文原式移植：准确性门控（回归斜率排名>0.6）→ 评级反转；用 if_else(...,0) 替代 :nan 压权重集中
leg_gated_B = (f'if_else(rank(ts_regression(rank(returns), rank({RV_B}), 120, lag=0, rettype=2))>0.6,'
               f' -ts_av_diff({RV_B}, 120), 0)')
leg_gated_D = (f'if_else(rank(ts_regression(rank(returns), rank({RV_D}), 120, lag=0, rettype=2))>0.6,'
               f' -ts_av_diff({RV_D}, 120), 0)')
# 离散→连续：先 ts_mean 平滑再取偏移（论文作者第一版思路）
leg_smooth_B = f'-ts_av_diff(ts_mean({RV_B}, 20), 120)'
# 分析师覆盖度轴（换轴不换族）
leg_totalrec = f'vec_avg(anl4_total_rec)'

C = [
 ('w120_a', build3([TSTKC, CICURR, INTC], CAPR,  leg_rating_B),  BASE()),
 ('w120_b', build3([TSTKC, CICURR, INTC], CAPR,  leg_rating_D),  BASE()),
 ('w120_c', build3([TSTKC, LIFR, INTC],   SALEB, leg_rating_B),  BASE()),
 ('w120_d', build3([TSTKC, CICURR, TFVCE],CAPR,  leg_gated_B),   BASE()),
 ('w120_e', build3([TSTKC, CICURR, TFVCE],CAPR,  leg_gated_D),   BASE()),
 ('w120_f', build3([TSTKC, CICURR, INTC], CAPR,  leg_totalrec),  BASE()),
 ('w120_g', build3([TSTKC, CICURR, INTC], LTB,   leg_rating_E),  BASE()),
 ('w120_h', build3([TSTKC, CICURR, INTC], CAPR,  leg_smooth_B),  BASE()),
 # 对照组1：论文原式照搬（不套骨架），看在我们数据下基线是多少
 ('w120_p', f'rank(ts_regression(rank(returns), rank({RV_B}), 120, lag=0, rettype=2))>0.6 '
            f'? 1 - rank(ts_av_diff({RV_B}, 120)) : 0', BASE()),
 # 对照组2：论文原式 + 我们已证的市值分桶中性化
 ('w120_q', f'group_neutralize(rank(ts_regression(rank(returns), rank({RV_B}), 120, lag=0, rettype=2))>0.6 '
            f'? 1 - rank(ts_av_diff({RV_B}, 120)) : 0, {CAPR})', BASE()),
 # 对照组3：论文式 + 市值分桶 + 全骨架（保留 PV 腿，7 腿，探算子/腿数上限）
 ('w120_r', ' + '.join([G(x, CAPR) for x in [TSTKC, CICURR, INTC]]) + ' + ' +
            ' + '.join(eng2(CAPR)) + ' + ' + G('-ts_delta(close, 2)', CAPR) + ' + ' + G(leg_gated_B, CAPR), BASE()),
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
            time.sleep(25 + att * 20); continue
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
    print('batch120 done', flush=True)
