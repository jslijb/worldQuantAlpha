# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch137 = 「冷锚 + ts_av_diff(·,45)」批（batch136 后的新假设）
# 依据链：
#   ① 历史实证：ts_av_diff(...,45) 是质量引擎的甜点窗口（45 活，30/60 死）
#   ② batch135 实证：把质量引擎腿（cash/cap、cfoev/cap）加回 /cap 家族 → SF 冲到 4.30 但 corr 0.96
#   ③ 推论：引擎的"回报来源"是 ts_av_diff(·,45) 这个时序差分结构，而不是 cash 本身
#   → 把 ts_av_diff(·,45) 套在**冷锚**上（不碰 cash/cfoev），既保留引擎的回报结构，又避开池内共享腿
# 同时铺三条正交路：混合缩放基准 / analyst4 评级腿（vec_avg）/ 第四锚
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=6, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'
GI = lambda x: f'group_rank({x}, industry)'
D45 = lambda x: f'ts_av_diff({x}, 45)'

TXA='fnd6_txtubadjust'; AOL='fnd6_newa1v1300_aol2'; DPQ='fnd6_newqv1300_dpactq'
PST='fnd6_pstkl'; TXS='fnd6_txs'; MIB='fnd6_mfmq_mibtq'; TXP='fnd6_txtubposinc'
INV='fnd6_newqv1300_invrmq'; NOP='fnd6_newa2v1300_nopi'; CIT='fnd6_newqv1300_citotalq'
RAT='vec_avg(anl4_fs_detail_rec_v4_nd_estimate)'

PVD5  = G('-ts_delta(vwap, 5)')
VOL12 = G('volume/ts_mean(volume, 120)')
PVD10 = G('-ts_delta(close, 10)')
VOL60 = G('volume/ts_mean(volume, 60)')

C = [
 # 主假设：冷锚 + ts_av_diff(·,45) 当引擎（/cap 尺度）
 ('w137_a', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.5*{G(D45(TXA+"/cap"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 ('w137_b', f'{G(D45(TXA+"/cap"))} + {G(D45(PST+"/cap"))} + {G(D45(TXS+"/cap"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 ('w137_c', f'1.5*{G(TXA+"/cap")} + {G(D45(MIB+"/cap"))} + {G(D45(INV+"/cap"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 ('w137_d', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + 0.5*{G(D45(NOP+"/cap"))} + 0.5*{G(D45(CIT+"/cap"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 # 混合缩放基准（同一表达式内三种分母 → 几何天然不同于纯 /cap）
 ('w137_e', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/sales")} + {G(DPQ+"/enterprise_value")} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 # analyst4 评级腿（vec_avg，账号唯一可用的评级通道）+ /cap 冷锚
 ('w137_f', f'1.5*{G(RAT)} + {G(TXA+"/cap")} + {G(AOL+"/cap")} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 ('w137_g', f'1.5*{G(RAT)} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + {G(D45(TXP+"/cap"))} + 0.75*{PVD5} + 0.75*{VOL12}',
  BASE()),
 # 四锚 + 45 差分引擎 + 换 PV 窗口
 ('w137_h', f'1.5*{G(TXA+"/cap")} + {G(AOL+"/cap")} + {G(DPQ+"/cap")} + {G(PST+"/cap")} + 0.5*{G(D45(TXA+"/cap"))} + 0.75*{PVD10} + 0.75*{VOL60}',
  BASE()),
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
        print(f'{cid} SIM-FAIL {json.dumps(j)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result')=='FAIL']
    ok = 'PASS' if (S + (b.get('fitness') or 0) >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else 'fail'
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} FAIL={fa} [{ok}]", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch137 done', flush=True)
