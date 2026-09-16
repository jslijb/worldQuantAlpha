# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# corr_probe_sweep.py —— 用「提交判决」当 corr 测量仪（0916 定案：判决 4~9 秒就出）
#   输入：cid 列表（对应 mined/{cid}.json 的 alpha id）
#   行为：逐个 POST /submit，读 403 判决书里的 SELF_CORRELATION 数值；
#        过线（ACCEPTED）即写台账；被拒只记档，候选保持未提交状态，无副作用。
#   纪律：一次一个、串行；每轮结束停手汇总；不碰 correlations/self 端点。
# 用法: python corr_probe_sweep.py w103_g w57_c ...   (>0 个 cid)
#       python corr_probe_sweep.py --file list.txt
import requests, json, time, sys, csv, datetime, re

LED = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
VER = 'data/alpha_quality_analysis/SUBMIT_VERDICTS.csv'
MINED = 'data/alpha_quality_analysis/mined'

args = sys.argv[1:]
cids = []
if args and args[0] == '--file':
    cids = [l.strip() for l in open(args[1], encoding='utf-8') if l.strip()]
else:
    cids = args
if not cids:
    print('用法: corr_probe_sweep.py <cid> [cid ...]  |  --file list.txt'); sys.exit(1)

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def load(cid):
    try:
        d = json.load(open(f'{MINED}/{cid}.json', encoding='utf-8'))
    except Exception as e:
        print(cid, 'NO-JSON', e); return None
    aid = d.get('id')
    if not aid: return None
    return aid, d

def alpha(a):
    try: return sess.get(f'https://api.worldquantbrain.com/alphas/{a}').json()
    except Exception: return None

def submit_one(cid, aid):
    """返回 (state, selfCorr, detail)"""
    d0 = alpha(aid)
    if d0 and (d0.get('status') == 'ACTIVE' or d0.get('stage') == 'OS'):
        return ('ALREADY', (d0.get('is') or {}).get('selfCorrelation'), d0)
    try:
        r = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
    except Exception as e:
        return ('NETFAIL', None, str(e)[:120])
    if r.status_code in (429,):
        return ('RATELIMIT', None, r.text[:120])
    if r.status_code not in (200, 201):
        return ('POSTFAIL', None, f'{r.status_code} {r.text[:160]}')
    loc = r.headers.get('Location') or f'https://api.worldquantbrain.com/alphas/{aid}/submit'
    for i in range(60):
        d = alpha(aid)
        if d and (d.get('status') == 'ACTIVE' or d.get('stage') == 'OS'):
            return ('ACCEPTED', (d.get('is') or {}).get('selfCorrelation'), d)
        try:
            p = sess.get(loc)
        except Exception:
            time.sleep(5); continue
        ra = p.headers.get('Retry-After')
        if ra:
            time.sleep(min(float(ra), 8)); continue
        if p.status_code == 404:
            time.sleep(6); continue
        try: j = p.json()
        except Exception:
            time.sleep(4); continue
        checks = (j.get('is') or {}).get('checks') or []
        if checks:
            sc = None; fails = []
            for c in checks:
                if c.get('result') == 'FAIL':
                    fails.append(c.get('name'))
                    if c.get('name') == 'SELF_CORRELATION': sc = c.get('value')
            return ('REJECTED', sc, ','.join(fails) or 'none')
    return ('TIMEOUT', None, None)

def append_ledger(aid, cid, d):
    b = d.get('is') or {}
    expr = ''
    try: expr = json.load(open(f'{MINED}/{cid}.json', encoding='utf-8')).get('regular', {}).get('code', '')
    except Exception: pass
    with open(LED, 'a', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow([aid, expr, b.get('sharpe'), b.get('fitness'), b.get('turnover'),
                                b.get('returns'), b.get('drawdown'), '', d.get('dateSubmitted'),
                                (d.get('settings') or {}).get('decay'),
                                (d.get('settings') or {}).get('neutralization'), f'0916-sweep-{cid}'])

def append_verdict(aid, cid, state, sc, detail):
    with open(VER, 'a', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow([datetime.datetime.now().isoformat(timespec='seconds'), aid, cid,
                                state, sc, detail if isinstance(detail, str) else ''])

led = set(r['id'] for r in csv.DictReader(open(LED, encoding='utf-8-sig')))
done = []
n_acc = 0
for cid in cids:
    got = load(cid)
    if not got:
        print(f'{cid} 跳过（无 json/id）', flush=True); continue
    aid, d = got
    if aid in led:
        print(f'{cid} {aid} 已在台账，跳过', flush=True); continue
    st, sc, det = submit_one(cid, aid)
    sf = None
    try:
        b = d.get('is') or {}
        sf = round((b.get('sharpe') or 0) + (b.get('fitness') or 0), 2)
    except Exception: pass
    print(f'[{len(done)+1}/{len(cids)}] {cid} {aid} SF={sf} -> {st} corr={sc} {det if isinstance(det,str) else ""}', flush=True)
    append_verdict(aid, cid, st, sc, det)
    if st == 'ACCEPTED':
        append_ledger(aid, cid, det); n_acc += 1
        print(f'    *** 入池！台账 +1（本轮到 {n_acc} 个）', flush=True)
    done.append((cid, aid, st, sc))
    if st in ('RATELIMIT', 'POSTFAIL', 'NETFAIL'):
        print('    异常状态，停手汇总', flush=True); break
    time.sleep(2)

print('\n=== 汇总 ===')
print(f'测试 {len(done)} 条，入池 {n_acc} 条')
for cid, aid, st, sc in done:
    print(f'  {cid:12s} {aid} {st:9s} corr={sc}')
