# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第126轮：极冷 fnd6 锚扩产（w125_g 验证：纯 aC=9~29 三锚 SF=4.40 达标）
#
# 字段池：fnd6_matrix.json 里 aC<100 且 w123/124/125 从未用过的 22 个字段。
# 主题分组：期权系 xopt*/xoptd*/xopte*（aC 9~99）、EPS/股价系 spce*/prc*（9~21）、
#           盈利质量 pnc*（16~37）、商誉 glce*（20~47）、其他 xintopt/fcaq/tfvceq。
# 结构：锚(全权,/assets) + 共享四腿 0.5 降权（w124_e/w125 验证不崩）。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

A = '/assets'
# 极冷池（aC<100，全未用）
OPT  = ['fnd6_newq_xoptdqp'+A, 'fnd6_newqv1300_xoptdq'+A, 'fnd6_newqv1300_xoptepsq'+A]  # aC 9/10/21
EPSQ = ['fnd6_newqv1300_spceepsq'+A, 'fnd6_newqv1300_prcaq'+A, 'fnd6_newqv1300_spceq'+A] # aC 9/10/11
MIX  = ['fnd6_newqv1300_pncq'+A, 'fnd6_newqv1300_glced12'+A, 'fnd6_newqv1300_prcdq'+A]  # aC 16/20/21
MIX4 = ['fnd6_newqv1300_spcedq'+A, 'fnd6_newq_xoptepsqp'+A, 'fnd6_pncdq'+A, 'fnd6_newqv1300_glceeps12'+A]  # 21/22/24/34
LONG = ['fnd6_newqv1300_pncepsq'+A, 'fnd6_newqv1300_glcea12'+A, 'fnd6_xintopt'+A, 'fnd6_newqv1300_fcaq'+A] # 37/47/74/80
G125 = ['fnd6_newqv1300_spceepsp12'+A, 'fnd6_newqv1300_prcepsq'+A, 'fnd6_newqv1300_spcep12'+A]  # w125_g 原三锚 SF=4.40

E3 = ['fnd6_newqv1300_cicurrq'+A, 'fnd6_dxd5'+A, 'fnd6_aqi'+A]  # w124_e 已验证

LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'

def G(x, grp): return f'group_rank({x}, {grp})'

def skel(anchors, grp, w=0.5):
    parts = [G(a, grp) for a in anchors]
    shared = [G('ts_av_diff(cash/assets, 45)', grp),
              G('ts_av_diff(cashflow_op/enterprise_value, 45)', grp),
              G('-ts_delta(close, 2)', grp),
              G('volume/ts_mean(volume, 60)', grp)]
    return ' + '.join(parts + [f'{w}*{s}' for s in shared])

C = [
 # 组1：纯极冷（三个主题各一组 + 四锚组）
 ('w126_a', skel(OPT, LB), BASE()),
 ('w126_b', skel(EPSQ, LB), BASE()),
 ('w126_c', skel(MIX, LB), BASE()),
 ('w126_d', skel(MIX4, LB), BASE()),
 # 组2：w125_g 最强纯极冷组扩到 4 锚
 ('w126_g', skel(G125 + ['fnd6_newqv1300_tfvceq'+A], LB), BASE()),
 # 组3：极冷 + 已验证 E3 锚混搭（保险）
 ('w126_e', skel(OPT[:2] + [E3[0]], LB), BASE()),
 ('w126_h', skel(EPSQ[:2] + E3[1:], LB), BASE()),
 # 组4：长尾 4 锚换 VOLB 桶
 ('w126_f', skel(LONG, VOLB), BASE()),
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
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa}", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch126 done', flush=True)
