# -*- coding: utf-8 -*-
"""mine_batch165.py —— 字段发现批：在从未开采的数据集里找"高质量单腿"

背景（0916 晚）：所有破墙轴已逐项实证关闭（见 CLAUDE.md §6 总表）——
换字段/换区域/风险中性化/PPAC/universe/结构改造/新数据轴单独成腿/积压，
唯一还开着的是「在 USA 内发现新的高质量单腿字段」。当年 fnd6_xrent 与
cashflow_op/enterprise_value 就是这么破了第一次墙。

本批对未开采数据集（option8 波动率 / socialmedia12 情绪 / model16 评分 / news12）
的字段做「0 阶验证」的批量版：只跑**我们验证过的最强包装**
  group_rank(ts_backfill(<field>, 120), subindustry)
看单腿 S+F 与 tS。达标线：SF >= 3.0 记为「可入腿库候选」。

产出：data/alpha_quality_analysis/mined/f165_{ds}_{field}.json
"""
import os as _os, pathlib as _pl, sys, json, time
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests
from concurrent.futures import ThreadPoolExecutor

OUT = 'data/alpha_quality_analysis/mined'
DATASETS = ['option8', 'socialmedia12', 'model16', 'news12']
PER_DS = int(sys.argv[sys.argv.index('--per-ds') + 1]) if '--per-ds' in sys.argv else 12
WORKERS = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 2
MIN_COV = 0.6

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201


def fields_of(ds):
    out = []
    for off in range(0, 400, 50):
        r = sess.get('https://api.worldquantbrain.com/data-fields'
                     f'?instrumentType=EQUITY&region=USA&delay=1&universe=TOP3000'
                     f'&limit=50&offset={off}&dataset.id={ds}')
        try:
            j = r.json()
        except Exception:
            break
        res = j.get('results') or []
        if not res:
            break
        out += res
        if len(out) >= (j.get('count') or 0):
            break
        time.sleep(0.5)
    return out


todo = []
for ds in DATASETS:
    fs = [f for f in fields_of(ds) if f.get('type') == 'MATRIX' and (f.get('coverage') or 0) >= MIN_COV]
    fs.sort(key=lambda f: -(f.get('coverage') or 0))
    for f in fs[:PER_DS]:
        fid = f['id']
        expr = f'group_rank(ts_backfill({fid}, 120), subindustry)'
        todo.append((f'f165_{ds[:8]}_{fid}'[:60], expr, fid, ds, f.get('coverage'), f.get('alphaCount')))
    print(f'{ds}: MATRIX+覆盖>={MIN_COV} 取前 {min(len(fs),PER_DS)} 个', flush=True)

print(f'共 {len(todo)} 条单腿待测', flush=True)


def BASE():
    return {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1, 'decay': 10,
            'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
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
        print(cid, 'REJECT', r.status_code, r.text[:200], flush=True); return None
    return None


def run_one(item):
    cid, expr, fid, ds, cov, ac = item
    of = f'{OUT}/{cid}.json'
    if _os.path.exists(of):
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': BASE(), 'regular': expr}, cid)
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
    d['_cid'] = cid; d['_field'] = fid; d['_ds'] = ds; d['_cov'] = cov; d['_aC'] = ac
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    flag = '***强' if S + F >= 3.0 else (' 中' if S + F >= 2.2 else '  弱')
    print(f"{flag} {ds:14s} {fid:38s} {aid} S={S:.2f} F={F:.2f} SF={S+F:.2f} T={b.get('turnover')} tS={te.get('sharpe')} cov={cov} aC={ac} FAIL={fa}", flush=True)
    time.sleep(1)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, todo))
print('batch165 done', flush=True)
