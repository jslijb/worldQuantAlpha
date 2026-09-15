# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第125轮：围绕 w124_e 成功配方扩产
#
# 依据（0915 实测）：
#   w124_e `6XrkW6R5` SF=4.28 tS=2.78 达标 —— 三锚 fnd6_newqv1300_cicurrq/fnd6_dxd5/fnd6_aqi
#   (各 /assets) + 共享四腿降权 0.5 + LB 桶。batch124 其余锚（SF 2.1~3.0）均失败，
#   说明锚本身质量差异大：cicurrq/dxd5/aqi 是被验证有效的组合。
#   batch123 极冷脚注字段全灭（最高 SF 3.75），纯冷锚路线不成立 → 本轮以"有效锚组合扩展"为主，
#   掺入 batch124 次优锚 tstk/loq（w124_f SF=3.97 差 0.03 达标）与少量极冷锚对照。
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

E3 = ['fnd6_newqv1300_cicurrq/assets', 'fnd6_dxd5/assets', 'fnd6_aqi/assets']   # w124_e 已验证
TSTK, LOQ = 'fnd6_newa2v1300_tstk/assets', 'fnd6_newqv1300_loq/assets'          # w124_f 次优
COLD = ['fnd6_newqv1300_spceepsp12/assets', 'fnd6_newqv1300_prcepsq/assets',    # aC=17/29
        'fnd6_newqv1300_spcep12/assets']                                        # aC=9

LB   = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
CFOB = 'bucket(rank(cashflow_op/assets), range="0.1, 1, 0.1")'
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
 # 组1：w124_e 三锚 + 加第4锚
 ('w125_a', skel(E3 + [TSTK], LB), BASE()),
 ('w125_b', skel(E3 + [LOQ], LB), BASE()),
 # 组2：w124_e 三锚换桶（corr 差异化：桶变了 group 内排序全变）
 ('w125_c', skel(E3, VOLB), BASE()),
 ('w125_e', skel(E3, CFOB), BASE()),
 # 组3：w124_f 补强（tstk+loq 差 0.03 达标，掺入已验证的 cicurrq）
 ('w125_d', skel([TSTK, LOQ, E3[0]], VOLB), BASE()),
 # 组4：掺极冷锚（aC=9~29，撞车概率最低）
 ('w125_f', skel(COLD[:2] + E3[:2], LB), BASE()),
 ('w125_g', skel(COLD, LB), BASE()),
 # 组5：掺历史最强腿 xrent
 ('w125_h', skel(E3 + ['fnd6_xrent/assets'], LB), BASE()),
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
    print('batch125 done', flush=True)
