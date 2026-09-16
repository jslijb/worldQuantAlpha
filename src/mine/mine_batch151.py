# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch151 = ★★ 把 w150_d 的**致远参数组合**搬到**全新锚组**上（今日最后一条、也是最有希望的一条）
# 今天的完整坐标链：
#   ① w150_d（4 锚 TXA/AOL/DPQ/PST + PV 1.0 + decay 10）实测
#        S=2.05 / F=2.00 / **SF=4.05 过线** / T=0.1141 / R=0.1184 —— 质量与换手都到位
#      但 corr=0.9856（撞 kqoq0zed）→ 死因只有一个：**它跟 kqoq0zed 共用 TXA/AOL/DPQ 三条锚**
#   ② corr 与 S 的关系（同几何下）：S2.02→0.6999、S2.7~2.8→0.78~0.80、S≥3.0→0.87
#      ⇒ S≈2.0~2.1 正是 corr 能进 0.70 的唯二区间，而 w150_d 恰好在这个区间且 SF 过线
#   ③ Fitness 公式 F = S×sqrt(R/max(T,0.125)) 已逐条验证；w150_d 的 R=0.1184/T=0.1141 已达标
#   ⇒ **本批 = 完全保留 w150_d 的参数（PV 1.0、decay 10、truncation 0.08、SUBINDUSTRY），
#      只把锚组换成 kqoq0zed 从未用过的冷字段**（全部出自 COLD_FIELD_WHITELIST，hasData=Y）
#      目标：指标轮廓照旧（S≈2.0~2.1 / F≈2.0 / SF≥4.0），几何彻底错开 → corr 进 0.70
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

def mkanch(anchors, head=1.5, pv=1.0):
    legs = [f'{head}*{G(anchors[0] + "/cap")}'] + [G(a + '/cap') for a in anchors[1:]]
    legs += [f'{pv}*{G("-ts_delta(vwap, 5)")}', f'{pv}*{G("volume/ts_mean(volume, 120)")}']
    return ' + '.join(legs)

A_PST = ['fnd6_pstkl', 'fnd6_txs', 'fnd6_mfmq_mibtq', 'fnd6_lqpl1']          # 全新一组
A_TXP = ['fnd6_txtubposinc', 'fnd6_pstkl', 'fnd6_newqv1300_citotalq', 'fnd6_newa2v1300_nopi']
A_INV = ['fnd6_newqv1300_invrmq', 'fnd6_newqv1300_rdipdq', 'fnd6_stkcpa', 'fnd6_optlifeq']
A_MIX = ['fnd6_pstkl', 'fnd6_newqv1300_citotalq', 'fnd6_newqv1300_txdbaq', 'fnd6_newa1v1300_fca']

C = [
 ('w151_a', mkanch(A_PST), BASE()),
 ('w151_b', mkanch(A_TXP), BASE()),
 ('w151_c', mkanch(A_INV), BASE()),
 ('w151_d', mkanch(A_MIX), BASE()),
 # 五锚（堆独有成分，看能否把 S 稳在 2.0~2.1 的同时抬 F）
 ('w151_e', mkanch(A_PST + ['fnd6_optlifeq']), BASE()),
 # PV 加到 1.25（进一步抬 R）
 ('w151_f', mkanch(A_PST, pv=1.25), BASE()),
 # 换 decay（8 / 12）定位换手-质量的平衡
 ('w151_g', mkanch(A_PST), BASE(delay=8)),
 ('w151_h', mkanch(A_PST), BASE(delay=12)),
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
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch151 done', flush=True)
