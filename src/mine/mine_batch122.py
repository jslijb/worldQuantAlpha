# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第122轮：破相关性墙 —— 共享腿降权 × 换冷门锚
#
# 背景（0915 实测）：w11x 池 99 条候选里 95% 共享同样两条腿
#   ts_av_diff(cash/assets,45) + ts_av_diff(cashflow_op/enterprise_value,45)
#   88% 再加 -ts_delta(close,2)
# 已提交池同样如此 → 47 条候选 corr 全在 0.74~0.93，豁免线 3.44~3.80 够不着，全线封死。
# 故本轮验证两个动作：
#   A 组 共享腿降权（0913 w85_a 曾实测 corr 0.754→0.6803，需复现）
#   B/C 组 换用 alphaCount 极低、从未被用过的 fnd6 冷门科目做锚 + 降权
#   I 组 对照组：原式 w=1.0，预期复现 w114_o 的 S≈3.05 / corr≈0.775
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

A = '/assets'
# w114_o 原锚
CICURR = 'fnd6_cicurr' + A
INTC   = 'fnd6_intc' + A
# 从未被用过的极冷门科目（alphaCount 9~300）
SPCEP12  = 'fnd6_newqv1300_spcep12' + A      # aC=9
SPCEEP12 = 'fnd6_newqv1300_spceepsp12' + A   # aC=17
XOPTEPSQ = 'fnd6_newqv1300_xoptepsq' + A     # aC=21
PRCEPSQ  = 'fnd6_newqv1300_prcepsq' + A      # aC=29
SPCED12  = 'fnd6_newqv1300_spcepd12' + A     # aC=38
XOPTD    = 'fnd6_newa2v1300_xoptd' + A       # aC=132
TFVLQ    = 'fnd6_newqv1300_tfvlq' + A        # aC=200
TXDIQ    = 'fnd6_newqv1300_txdiq' + A        # aC=227
STKCPAQ  = 'fnd6_newqv1300_stkcpaq' + A      # aC=278
WCAPQ    = 'fnd6_newqv1300_wcapq' + A        # aC=263
MIBRQ    = 'fnd6_newqv1300_mibnq' + A        # aC=182

LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'   # w114_o 原桶
CFOB = 'bucket(rank(cashflow_op/assets), range="0.1, 1, 0.1")'          # 换桶
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'     # 换桶

def G(x, grp): return f'group_rank({x}, {grp})'

def skel(anchors, grp, w=1.0, pv=None, eng=None):
    """独有锚（全权）+ 引擎腿 + PV 腿（共享部分按 w 降权）"""
    parts = [G(a, grp) for a in anchors]
    eng = eng or ['ts_av_diff(cash/assets, 45)', 'ts_av_diff(cashflow_op/enterprise_value, 45)']
    pvl = pv or ['-ts_delta(close, 2)', 'volume/ts_mean(volume, 60)']
    shared = [G(x, grp) for x in (eng + pvl)]
    if w != 1.0:
        shared = [f'{w}*{s}' for s in shared]
    return ' + '.join(parts + shared)

C = [
 # ---- A 组：共享腿降权梯度（锚沿用 w114_o）----
 ('w122_a', skel([CICURR, INTC], LB, 0.50), BASE()),
 ('w122_b', skel([CICURR, INTC], LB, 0.35), BASE()),
 ('w122_c', skel([CICURR, INTC], LB, 0.25), BASE()),
 # ---- B 组：换成极冷门锚 + 降权 ----
 ('w122_d', skel([SPCEP12, XOPTEPSQ, PRCEPSQ], LB, 0.50), BASE()),
 ('w122_e', skel([SPCEEP12, SPCED12, XOPTD], LB, 0.50), BASE()),
 ('w122_f', skel([TFVLQ, TXDIQ, STKCPAQ, WCAPQ], LB, 0.35), BASE()),
 # ---- C 组：换锚 + 换 PV 腿（双轮换）----
 ('w122_g', skel([SPCEP12, XOPTEPSQ, PRCEPSQ], LB, 0.50,
                 pv=['-ts_delta(close, 5)', 'ts_mean(volume,20)/ts_mean(volume,120)']), BASE()),
 ('w122_h', skel([MIBRQ, TFVLQ, TXDIQ], LB, 0.50,
                 eng=['ts_av_diff(fnd6_xrent/assets, 45)', 'ts_av_diff(cash/assets, 45)']), BASE()),
 # ---- D 组：换桶 ----
 ('w122_i', skel([SPCEP12, XOPTEPSQ, PRCEPSQ], CFOB, 0.50), BASE()),
 ('w122_j', skel([SPCEP12, XOPTEPSQ, PRCEPSQ], VOLB, 0.50), BASE()),
 # ---- 对照组：原式不降权（预期复现 w114_o S≈3.05 / corr≈0.775）----
 ('w122_k', skel([CICURR, INTC], LB, 1.0), BASE()),
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
    print('batch122 done', flush=True)
