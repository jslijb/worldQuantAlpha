# -*- coding: utf-8 -*-
"""axis_surgery.py —— 单轴手术：只改一个设置轴，其余设置沿用源 alpha（保证单一变量）

为什么需要它：
  近失分析（_autologs/near_miss.py）给出「离豁免线 need - S」最近的候选清单。
  这些候选的 gap 只有 0.2~0.4 个夏普，而它们 decay 常在 40~50、TO 只有 6~11%
  —— 而 decay 是「用 TO 换 S」的跷跷板（史证 d10→d1 把 S 2.45→2.77）。
  ⇒ 在 TO 预算（≤20%）内砍 decay 买 S，是唯一能直接把 gap 抹掉的动作。

用法：
  python _autologs/axis_surgery.py --ids om6PG5Pv,883GYlNo --axis decay --values 30,20,15,10 --tag s22
  python _autologs/axis_surgery.py --ids xxx --axis neutralization --values INDUSTRY,SECTOR --tag n22
  python _autologs/axis_surgery.py --ids xxx --axis universe --values TOP1000,TOP500 --tag u22

产出：data/alpha_quality_analysis/mined/{tag}_{src}_{value}.json
      _autologs/_axis_surgery.txt （汇总表，可直接与源指标对比）
"""
import os as _os, io, sys, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)
import requests
from concurrent.futures import ThreadPoolExecutor

A = sys.argv[1:]
def opt(n, d=None):
    for a in A:
        if a == n:
            return A[A.index(a) + 1]
        if a.startswith(n + '='):
            return a.split('=', 1)[1]
    return d

IDS = [x.strip() for x in (opt('--ids', '') or '').split(',') if x.strip()]
AXIS = opt('--axis', 'decay')
RAWS = [x.strip() for x in (opt('--values', '30,20,15,10') or '').split(',') if x.strip()]
TAG = opt('--tag', 's')
WORKERS = int(opt('--workers', 2))
SKIP_SAME = '--skip-same' in A          # 值为源 alpha 已有值时跳过
DRY = '--dry' in A

# 数值轴转 int
def cast(v, ref):
    if isinstance(ref, int):
        return int(v)
    if isinstance(ref, float):
        return float(v)
    return v

OUTD = ROOT / 'data/alpha_quality_analysis/mined'
API = ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'

SRC = {}
D = json.load(io.open(API, encoding='utf-8'))
if isinstance(D, dict):
    D = D.get('results', [])
for a in D:
    if a.get('id') in IDS:
        SRC[a['id']] = a
# 源可能已在池里（不在未提交池）→ 补拉平台
need_fetch = [i for i in IDS if i not in SRC]

sess = requests.Session()
sess.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
for _ in range(8):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        time.sleep(5)

for i in need_fetch:
    try:
        j = sess.get(f'https://api.worldquantbrain.com/alphas/{i}', timeout=60).json()
        SRC[i] = j
    except Exception as e:
        print('SRC-FETCH-FAIL', i, e, flush=True)

LOG = io.open(ROOT / '_autologs' / '_axis_surgery.txt', 'w', encoding='utf-8')
def w(s=''):
    LOG.write(str(s) + '\n'); LOG.flush()


def post_retry(payload, cid):
    for att in range(8):
        try:
            r = sess.post('https://api.worldquantbrain.com/simulations', json=payload, timeout=120)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201):
            return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:260], flush=True); return None
    return None


jobs = []
w('== 单轴手术：axis=%s，源 %d 条，值 %s ==' % (AXIS, len(SRC), RAWS))
for sid in IDS:
    a = SRC.get(sid)
    if not a:
        w('%s 源信息缺失，跳过' % sid); continue
    st0 = dict(a.get('settings') or {})
    b = a.get('is') or {}; te = a.get('test') or {}
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    w('[源] %-10s %-8s %-11s dly=%s dec=%-4s S=%.2f F=%.2f TO=%.4f tS=%.2f FAIL=%s'
      % (sid, st0.get('universe'), st0.get('neutralization'), st0.get('delay'), st0.get('decay'),
         b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0, te.get('sharpe') or 0, fa))
    code = (a.get('regular') or {}).get('code') or ''
    if not code:
        w('   %s 无表达式，跳过' % sid); continue
    for v in RAWS:
        val = cast(v, st0.get(AXIS))
        if SKIP_SAME and st0.get(AXIS) == val:
            continue
        st = dict(st0)
        st[AXIS] = val
        cid = '%s_%s_%s%s' % (TAG, sid, AXIS[:2], v)
        jobs.append((cid, sid, val, st, code, a.get('id')))

w('  计划模拟 %d 个（%d 条 x %d 值）' % (len(jobs), len(SRC), len(RAWS)))
w('')
if DRY:
    for cid, sid, val, st, code, _ in jobs:
        w('%-22s %s=%s' % (cid, AXIS, val))
    LOG.close(); print('dry done'); raise SystemExit

OUTD.mkdir(parents=True, exist_ok=True)


def run_one(job):
    cid, sid, val, st, code, srcid = job
    of = OUTD / f'{cid}.json'
    if of.exists():
        print(f'{cid} 已有产出，跳过', flush=True); return
    r = post_retry({'type': 'REGULAR', 'settings': st, 'regular': code}, cid)
    if r is None:
        return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try:
            p = sess.get(loc, timeout=120)
        except Exception as e:
            print(cid, 'NET-poll', e, flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 20)); continue
        break
    try:
        jj = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = jj.get('alpha')
    if not aid:
        print(f'{cid} SIM-FAIL {json.dumps(jj)[:220]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}', timeout=60).json()
    d['_cid'] = cid; d['_src'] = srcid; d['_axis'] = AXIS; d['_val'] = val
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    print('%-24s %s S=%.2f F=%.2f TO=%.4f tS=%.2f FAIL=%s'
          % (cid, aid, S, F, b.get('turnover') or 0, te.get('sharpe') or 0, fa), flush=True)
    time.sleep(0.5)


with ThreadPoolExecutor(max_workers=WORKERS) as ex:
    list(ex.map(run_one, jobs))
w('axis_surgery done：%s' % time.strftime('%H:%M:%S'))
LOG.close()
print('axis_surgery done', flush=True)
