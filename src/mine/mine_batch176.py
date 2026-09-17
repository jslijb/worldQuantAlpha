# -*- coding: utf-8 -*-
"""mine_batch176.py —— decay 扫描：最后一个从未测过的零成本参数杠杆

背景（0917 x175 判决 0/34）：
  - 池子 79 条全部 decay=10 建，PnL 时间轮廓同质；
  - 剩余近门槛候选卡在 0.689~0.702（最近差 0.004）；
  - 腿稀释矿脉已挖干（gJbkQ31Q 进池后自己成了头号撞点）。

假设：decay 拉大 → alpha 被指数平滑 → PnL 日度轮廓变化 → 与 decay=10 的池子相关性下降。
（这是三层杠杆里「参数层」的 decay 维度，本项目从未扫过。）

对 corr 0.689~0.702 的 8 条擦线候选，各跑 decay ∈ {22, 32, 44}（原 10 已测过）。
产出 data/alpha_quality_analysis/mined/x176_{cid}_d{decay}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 3

DECAYS = [22, 32, 44]
PICKS = [  # (cid, base_corr) —— x175 判决 corr 0.689~0.702
    ('x175_m161_e79PvPpE_BIT', 0.6890),
    ('x175_x172_w166_02_OVN_BIT', 0.6895),
    ('x175_w114_m_I', 0.6903),
    ('x175_x172_w166_02_OVN_B', 0.6933),
    ('x175_w166_02_BIT', 0.6978),
    ('x175_m161_0mR2K6lr_BIT', 0.6982),
    ('x175_w166_02_B', 0.7007),
    ('x175_m161_e79PvPpE_B', 0.7017),
]

todo = []
for cid, bc in PICKS:
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr:
        print(f'{cid} 无表达式，跳过', flush=True); continue
    for dec in DECAYS:
        todo.append((f'x176_{cid}_d{dec}'[:64], expr, neut, dec, cid, bc))

print(f'decay 扫描变体 {len(todo)} 条（源 {len(PICKS)} 条擦线候选 × decay {DECAYS}）', flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def BASE(neut, dec):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': dec,
            'neutralization': neut, 'truncation': 0.08, 'pasteurization': 'ON',
            'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False,
            'startDate': '2019-01-01', 'endDate': '2023-12-31', 'testPeriod': 'P1Y'}


def post_retry(payload, cid):
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None


def run_one(item):
    cid, expr, neut, dec, src_cid, bc = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut, dec), 'regular': expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try:
            p = sess.get(loc)
        except Exception as e:
            print(cid, 'NET-poll', e, flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(float(ra)); continue
        break
    try:
        jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:200]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid; d['_neut'] = neut; d['_decay'] = dec; d['_src'] = src_cid; d['_base_corr'] = bc
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:52s} {neut:11s} decay={dec:2d} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} base={bc:.4f} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch176 done', flush=True)
