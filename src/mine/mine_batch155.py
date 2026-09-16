# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# batch155 = 【结构诊断批】不是挖矿，是为了回答"相关性到底挂在哪条腿上"
#
# 背景（0916 15:20 新证据）：
#   1) 本地 PnL corr 已可用（src/analysis/pnl_corr.py），误差<0.01，不必再提交试探
#   2) batch154 六条互相关 0.97~0.9996 → 同锚同族 = 一个因子
#   3) batch154 六条对 kqoq0zed 0.84~0.89 → 跨锚组仍被锁
#   4) 池子不均匀：老31个 max corr 仅 0.54~0.67，拥挤是后来骨架造成的
#
# 本批要回答三件事：
#   A. 分解：锚腿 vs 价量腿，谁扛着对 kqoq0zed 的 0.87？
#   B. 线性性：PnL 是否近似等于各腿 PnL 的加权和？(成立 → 可建"腿库"离线拼装，筛选零成本)
#   C. 控制组：复刻 kqoq0zed 原式，与已提交的 kqoq0zed PnL 对不上就说明本地口径有问题
#
# 产出用法：
#   python src/analysis/pnl_corr.py x155_e x155_a x155_g ...   # 看各自撞谁
#   python src/analysis/leg_linearity.py                        # 验线性性
import requests, json, time, os
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=10, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':1,'decay':delay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

G = lambda x: f'group_rank({x}, subindustry)'

# --- w154 腿组（A_PST 锚 + close5/vol90 价量） ---
A4 = f'1.5*{G("fnd6_pstkl/cap")} + {G("fnd6_txs/cap")} + {G("fnd6_mfmq_mibtq/cap")} + {G("fnd6_lqpl1/cap")}'
PVB = f'1.5*{G("-ts_delta(close, 5)")} + 1.6*{G("volume/ts_mean(volume, 90)")}'

# --- kqoq0zed 腿组（原式已入池，用于控制组与分解） ---
KQ_ANCH = f'1.5*{G("fnd6_txtubadjust/cap")} + {G("fnd6_newa1v1300_aol2/cap")} + {G("fnd6_newqv1300_dpactq/cap")}'
KQ_PV = f'0.75*{G("-ts_delta(vwap, 5)")} + 0.75*{G("volume/ts_mean(volume, 120)")}'

C = [
 ('x155_e', f'{KQ_ANCH} + {KQ_PV}',            BASE(delay=6)),   # 控制组：复刻 kqoq0zed
 ('x155_a', A4,                                 BASE()),          # A_PST 锚腿单独
 ('x155_b', PVB,                                BASE()),          # close5/vol90 价量腿单独
 ('x155_g', KQ_ANCH,                            BASE(delay=6)),   # kqoq 锚腿单独
 ('x155_h', KQ_PV,                              BASE(delay=6)),   # kqoq 价量腿单独
 ('x155_c', G('-ts_delta(close, 5)'),           BASE()),          # 纯反转腿
 ('x155_d', G('volume/ts_mean(volume, 90)'),    BASE()),          # 纯量能腿
 ('x155_f', f'{A4} + 1.5*{G("-ts_delta(close, 20)")} + 1.6*{G("volume/ts_mean(volume, 120)")}', BASE()),  # 长周期价量
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
    ng = b.get('longCount',0) + b.get('shortCount',0)
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} R={b.get('returns')} tS={te.get('sharpe')} 持仓={ng} FAIL={fa}", flush=True)
    time.sleep(1)

if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=2) as ex:
        list(ex.map(run_one, C))
    print('batch155 done', flush=True)
