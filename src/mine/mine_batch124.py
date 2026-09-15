# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第124轮：全新冷门锚矩阵（batch122/123 实证后定向选种）
#
# 依据：
#   - batch122 有效框架 = 冷锚全权 + 引擎/PV 腿 0.5 降权（w122_a SF5.00 / w122_d SF4.40 达标）
#   - batch123 证伪：fnd2 脚注锚（SF 全 <3.8）与无覆盖组 spceepsp12/spcepd12/xoptd（w122_d/e 指标逐位相同=锚无效）
#   - 本轮锚全部取自 fnd6_matrix.json 中从未被用过的字段（aC 196~361，含 fnd6_newqv1300_* 仅 delay=0 禁用，D1 可用）
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

A = '/assets'
# 六组全新冷门锚（均未出现在 expr_library / 台账 / w12x 池中）
S1 = ['fnd6_newqv1300_spcepq' + A,   'fnd6_newqv1300_optrfrq' + A, 'fnd6_newqv1300_tfvaq' + A]    # aC 248/196/238
S2 = ['fnd6_newa2v1300_spced' + A,   'fnd6_newa1v1300_aqpl1' + A,  'fnd6_newa2v1300_txach' + A]   # aC 213/218/238
S3 = ['fnd6_newqv1300_prcraq' + A,   'fnd6_newa2v1300_tstkn' + A,  'fnd6_newqv1300_ciderglq' + A] # aC 252/257/261
S4 = ['fnd6_optvolq' + A,            'fnd6_newqv1300_anoq' + A,    'fnd6_fatn' + A]               # aC 273/279/301
S5 = ['fnd6_newqv1300_cicurrq' + A,  'fnd6_dxd5' + A,              'fnd6_aqi' + A]                # aC 279/338/361
S6 = ['fnd6_newa2v1300_tstk' + A,    'fnd6_newqv1300_loq' + A,     'fnd6_txfed' + A]              # aC 272/317/316

LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
VOLB = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'

def G(x, grp): return f'group_rank({x}, {grp})'

def skel(anchors, grp, w=0.5):
    """冷锚全权 + 引擎/PV 腿按 w 降权（batch122 验证的过墙框架）"""
    parts = [G(a, grp) for a in anchors]
    shared = [G('ts_av_diff(cash/assets, 45)', grp),
              G('ts_av_diff(cashflow_op/enterprise_value, 45)', grp),
              G('-ts_delta(close, 2)', grp),
              G('volume/ts_mean(volume, 60)', grp)]
    shared = [f'{w}*{s}' for s in shared]
    return ' + '.join(parts + shared)

C = [
 ('w124_a', skel(S1, LB),      BASE()),
 ('w124_b', skel(S2, LB),      BASE()),
 ('w124_c', skel(S3, LB),      BASE()),
 ('w124_d', skel(S4, LB),      BASE()),
 ('w124_e', skel(S5, LB),      BASE()),
 ('w124_f', skel(S6, VOLB),    BASE()),
 ('w124_g', skel(S1, LB, 0.35), BASE()),   # 降权梯度备份（若 0.5 封死可试更低共享占比）
 ('w124_h', skel(S1, VOLB),    BASE()),     # 同锚换桶备份
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
    print('batch124 done', flush=True)
