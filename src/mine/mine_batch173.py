# -*- coding: utf-8 -*-
"""mine_batch173.py —— 稀释腿换成「分析师覆盖变化」（analyst4 唯一存活轴）

来源（0916 晚二轮）：
  ① 量产动作已被证实：受阻候选 + 0.75*<池子里没有的几何腿> → 58znv2Y1（corr 0.6706 入池）、
     akbjdK26（0.6828 入池）。
  ② f171 把 analyst4 的 13 条候选轴全测了一遍，只有**分析师覆盖机构数变化**活下来：
       cov_ep = ts_av_diff(anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45)
       → SF 2.16 / tS 1.25（只挂 LOW_FITNESS，无 LOW_SHARPE）
     分歧度 disp（−0.50~0.09）、预期修正 rev（0.28~0.52）、guidance spread（0.05）全死。
  ③ 这条轴**池子里零条**，且与价量几何天然不同 —— 正是理想的第 5 条稀释腿
     （记忆里的铁律：新信号轴**只能叠加、不能顶替**价量腿，这里正好只做叠加）。

本批对受阻库存里**尚未被 172 批取用**的候选挂 0.75*cov_ep。
产出 data/alpha_quality_analysis/mined/x173_{cid}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
TOPN = int(sys.argv[sys.argv.index('--topn') + 1]) if '--topn' in sys.argv else 10
OFFSET = int(sys.argv[sys.argv.index('--offset') + 1]) if '--offset' in sys.argv else 12

COVEP = ('group_rank(ts_backfill(ts_av_diff('
         'anl4_fs_detail_estimate_1qf_v4_nd_epsr_number, 45), 120), subindustry)')

blocked = json.load(open('_autologs/_blocked_cands.json', encoding='utf-8'))
LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
submitted = set(l.split(',')[0].strip('"') for l in open(LED, encoding='utf-8-sig').read().splitlines()[1:])

cands = [(aid, v) for aid, v in blocked.items() if aid not in submitted and v.get('SF', 0) >= 4.5]
cands.sort(key=lambda kv: kv[1].get('pred') or 9)
rows = cands[OFFSET:OFFSET + TOPN]
todo = []
for aid, v in rows:
    cid = v['cid']
    src = f'{OUT}/{cid}.json'
    if not _os.path.exists(src):
        print(f'{cid} 源 json 缺失，跳过', flush=True); continue
    d = json.load(open(src, encoding='utf-8'))
    expr = (d.get('regular') or {}).get('code')
    neut = (d.get('settings') or {}).get('neutralization') or 'SUBINDUSTRY'
    if not expr:
        continue
    todo.append((f'x173_{cid}'[:60], f'{expr} + 0.75*{COVEP}', neut, cid, aid))

print(f'cov_ep 稀释变体 {len(todo)} 条（取 pred 升序第 {OFFSET+1}~{OFFSET+TOPN} 位）', flush=True)
for t in todo:
    print('   ', t[0], t[2], flush=True)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def BASE(neut):
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
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
    cid, expr, neut, src_cid, src_aid = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(neut), 'regular': expr}, cid)
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
    d['_cid'] = cid; d['_neut'] = neut; d['_src'] = src_cid; d['_src_aid'] = src_aid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '★PASS' if (S + F >= 4.0 and (te.get('sharpe') or 0) >= 1.25 and not fa) else ' fail '
    print(f'{flag} {cid:20s} {neut:11s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get("turnover")} tS={te.get("sharpe")} FAIL={fa}', flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch173 done', flush=True)
