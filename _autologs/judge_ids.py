# -*- coding: utf-8 -*-
"""judge_ids.py —— 按"平台侧 alpha id"直接跑相关性判决（不依赖本地 mined 文件）

为什么需要它（0921）：
  现有 submit_exempt.py 只认 `data/alpha_quality_analysis/mined/<pat>.json`。
  但平台账号里躺着 3554 条 UNSUBMITTED，其中 487 条过质量闸门 —— 这些是
  **平台权威指标**（不是本地模拟），是本账号真正的弹药库，却从没被系统性判过。
  本脚本直接从 all_unsubmitted.json 读候选，逐个取 PnL、对 107 条已提交池算相关。

判据（与 submit_exempt.py 完全一致，双阈值不许混）：
  · CORR_FLOOR  = 0.66  —— 收哪些对手进名单
  · CORR_DIRECT = 0.685 —— 直通判定（本地 ≤0.685 → 平台 ≤0.690 < 0.70）
  · 豁免线      = 1.10 × max(所有 corr≥0.66 且 S 已知的对手的 S)

用法：
  python _autologs/judge_ids.py --gate --limit 0            # 全判
  python _autologs/judge_ids.py --gate --nontop             # 只判非 TOP3000
  python _autologs/judge_ids.py --ids XgbgNwna,qMxM5j1A
"""
import os as _os, io, sys, json, glob, time, statistics as st
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

_OUTNAME = 'txt'
for _i, _a in enumerate(sys.argv):
    if _a.startswith('--out='):
        _OUTNAME = _a.split('=', 1)[1]
if '--out' in sys.argv:
    _OUTNAME = sys.argv[sys.argv.index('--out') + 1]
OUT = io.open(ROOT / '_autologs' / ('_judge_ids_%s.txt' % _OUTNAME), 'w', encoding='utf-8')
L = []
def w(s=''):
    L.append(str(s))
    OUT.write(str(s) + '\n')
    OUT.flush()

A = sys.argv[1:]
def opt(n, d):
    for a in A:
        if a == n:
            return A[A.index(a) + 1]
        if a.startswith(n + '='):
            return a.split('=', 1)[1]
    return d

MIN_SF = float(opt('--min-sf', 4.0))
MIN_TS = float(opt('--min-ts', 1.25))
MIN_F = float(opt('--min-f', 1.8))
MAX_TO = float(opt('--max-to', 0.20))
LIMIT = int(opt('--limit', 0))
CORR_FLOOR = float(opt('--corr-floor', 0.66))
CORR_COUNT = float(opt('--corr-count', 0.66))
CORR_DIRECT = float(opt('--corr-direct', 0.685))
EXEMPT = float(opt('--exempt', 1.10))
ONLY_GATE = '--gate' in A
NONTOP = '--nontop' in A
IDS = [x.strip() for x in (opt('--ids', '') or '').split(',') if x.strip()]

PC = ROOT / 'data/alpha_quality_analysis/pnl'
LED = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
POOL_S = ROOT / 'data/alpha_quality_analysis/pool_s.json'
API = ROOT / 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'

import requests
sess = requests.Session()
sess.auth = tuple(json.load(open(ROOT / 'brain_credentials.txt')))
_ok = False
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            _ok = True; break
    except Exception as e:
        w('auth retry %d: %s' % (_a, str(e)[:60]))
    time.sleep(3 * (_a + 1))
assert _ok, '认证失败'


def pnl(aid):
    f = PC / f'{aid}.json'
    if f.exists():
        try:
            return {k: float(v) for k, v in json.load(open(f, encoding='utf-8')).items()}
        except Exception:
            pass
    j = None
    for att in range(6):
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/recordsets/pnl', timeout=60)
            ra = r.headers.get('Retry-After')
            j = r.json()
            if j.get('records'):
                break
        except Exception:
            j = None
        time.sleep(float(ra) if ra else 2 * (att + 1))
    if not j or not j.get('records'):
        raise RuntimeError('no pnl')
    d = {}; prev = None
    for r in j['records']:
        cum = float(r[1])
        d[str(r[0])] = cum - (prev if prev is not None else cum)
        prev = cum
    json.dump(d, open(f, 'w', encoding='utf-8'))
    return d


def corr(a, b):
    ks = set(a) & set(b)
    if len(ks) < 300:
        return None
    ks = sorted(ks)
    x = [a[k] for k in ks]; y = [b[k] for k in ks]
    mx = st.mean(x); my = st.mean(y)
    sx = sum((v - mx) ** 2 for v in x) ** .5
    sy = sum((v - my) ** 2 for v in y) ** .5
    if not sx or not sy:
        return None
    return sum((x[i] - mx) * (y[i] - my) for i in range(len(ks))) / (sx * sy)


def g(d, *p, default=None):
    cur = d
    for k in p:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
        if cur is None:
            return default
    return cur


# ---- 池子 ----
pool = []
for ln in open(LED, encoding='utf-8-sig').read().splitlines()[1:]:
    aid = ln.split(',')[0].strip('"')
    if aid and aid not in pool:
        pool.append(aid)
PS = json.load(open(POOL_S, encoding='utf-8')) if POOL_S.exists() else {}
P = {}
missing = []
for aid in pool:
    try:
        P[aid] = pnl(aid)
    except Exception:
        missing.append(aid)
w('池子 %d 条（取到 PnL %d，缺 %d）' % (len(pool), len(P), len(missing)))

# ---- 候选 ----
data = json.load(io.open(API, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
sub = set(pool)
cands = []
for a in data:
    st_ = a.get('settings') or {}
    checks = g(a, 'is', 'checks', default=[]) or []
    fails = [c.get('name') for c in checks if c and c.get('result') == 'FAIL']
    S = g(a, 'is', 'sharpe'); F = g(a, 'is', 'fitness')
    TO = g(a, 'is', 'turnover'); tS = g(a, 'test', 'sharpe')
    rec = dict(id=a.get('id'), S=S, F=F, TO=TO, tS=tS, fails=fails,
               uni=st_.get('universe'), neu=st_.get('neutralization'),
               delay=st_.get('delay'), dec=st_.get('decay'),
               R=g(a, 'is', 'returns'), margin=g(a, 'is', 'margin'))
    if rec['id'] in sub:
        continue
    cands.append(rec)

if IDS:
    want = set(IDS)
    cands = [c for c in cands if c['id'] in want]
elif ONLY_GATE:
    cands = [c for c in cands
             if (c['S'] or 0) + (c['F'] or 0) >= MIN_SF and (c['tS'] or 0) >= MIN_TS
             and not c['fails'] and (c['F'] or 0) >= MIN_F and (c['TO'] or 9) <= MAX_TO]
if NONTOP:
    cands = [c for c in cands if c['uni'] != 'TOP3000']

cands.sort(key=lambda x: -(x['F'] or 0))
if LIMIT:
    cands = cands[:LIMIT]
w('待判候选 %d 条（min_f %.2f / max_to %.2f / 直通线 %.3f）' % (len(cands), MIN_F, MAX_TO, CORR_DIRECT))
w('=' * 130)

hdr = '%-11s %-8s %-13s %-4s %-4s %6s %6s %7s %6s | %8s %-11s %8s %s'
w(hdr % ('id', 'universe', 'neut', 'dly', 'dec', 'S', 'F', 'TO', 'tS',
         'corr_max', '撞谁', 'need', '判定'))
w('-' * 130)

passed = []
nofail = 0
for c in cands:
    aid = c['id']
    try:
        x = pnl(aid)
    except Exception as e:
        w('  %-11s PnL 取不到: %s' % (aid, str(e)[:40]))
        continue
    rivals = []
    for q, p in P.items():
        v = corr(x, p)
        if v is not None and v >= CORR_FLOOR:
            rivals.append((v, q, PS.get(q)))
    verdict = ''; cmax = None; qmax = ''; need = None
    if not rivals:
        cmax = 0.0; verdict = '★ 直通'
    else:
        cmax, qc, sc = max(rivals, key=lambda t: t[0])
        if cmax < CORR_DIRECT:
            verdict = '★ 直通'
        else:
            known = [r for r in rivals if r[2]]
            cnt = [r for r in rivals if r[0] >= CORR_COUNT and r[2]]
            if not known:
                verdict = '? 对手S未知'
            else:
                _, qe, se = max(known, key=lambda t: t[2])
                need = EXEMPT * se
                qmax = qe
                if not cnt:
                    verdict = '★ 豁免放行(空)'
                elif (c['S'] or 0) < EXEMPT * max(cnt, key=lambda t: t[2])[2]:
                    verdict = '✗ 不够'
                    need = EXEMPT * max(cnt, key=lambda t: t[2])[2]
                    qmax = max(cnt, key=lambda t: t[2])[1]
                else:
                    verdict = '★ 豁免放行'
                    need = EXEMPT * max(cnt, key=lambda t: t[2])[2]
                    qmax = max(cnt, key=lambda t: t[2])[1]
    if not verdict.startswith('✗') and '未知' not in verdict:
        nofail += 1
    if verdict.startswith('★'):
        passed.append((c, cmax, qmax, need))
    w(hdr % (str(aid)[:11], str(c['uni'])[:8], str(c['neu'])[:13], c['delay'], c['dec'],
             '%.2f' % c['S'], '%.2f' % c['F'], '%.3f' % c['TO'], '%.2f' % (c['tS'] or -1),
             '%.4f' % cmax, str(qmax)[:11], ('%.2f' % need) if need else '-', verdict))
    time.sleep(0.15)

w('=' * 130)
w('判决完毕：判了 %d 条，通过 %d 条' % (len(cands), len(passed)))
for c, cmax, q, nd in passed:
    w('  ★ %-11s %-8s S=%.2f F=%.2f TO=%.3f tS=%.2f corr_max=%.4f' %
      (c['id'], c['uni'], c['S'], c['F'], c['TO'], c['tS'] or -1, cmax))
OUT.close()
print('done')
