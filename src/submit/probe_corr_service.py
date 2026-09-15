# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 自相关服务探测：缓存探针(E5vj5YdL) + 全新候选探针（防止缓存假阳性）
import requests, json, time, csv, glob, sys

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
r = sess.post('https://api.worldquantbrain.com/authentication')
print('auth:', r.status_code, flush=True)
assert r.status_code == 201

LEDGER = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
done = set()
with open(LEDGER, encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if row.get('id'): done.add(row['id'].strip())
print('ledger rows(unique ids):', len(done), flush=True)


def probe(aid, label, budget_sec=90.0):
    """判据修正（0915 实证）：
       `200 + Retry-After + 空 body` = 平台正在现算，**必须继续轮询**，不是故障。
       实测：轮询 3–4 次（4–6 秒）即返回完整 records。
       故改为按时间预算轮询，拿到 records 才算 UP；预算内始终拿不到才算 DOWN。
    """
    hits = []
    t0 = time.time()
    i = 0
    while time.time() - t0 < budget_sec:
        i += 1
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
        except Exception as e:
            hits.append(f'try{i}: EXC {type(e).__name__}')
            time.sleep(5); continue
        ra = r.headers.get('Retry-After')
        body_len = len(r.text or '')
        nrec = None
        if r.status_code == 200 and body_len > 0:
            try:
                nrec = len((r.json() or {}).get('records') or [])
            except Exception:
                nrec = -1
        if i <= 3 or nrec is not None:
            hits.append(f'try{i}: t={time.time()-t0:5.1f}s {r.status_code} '
                        f'Retry-After={ra} bodylen={body_len} records={nrec}')
        if nrec is not None and nrec > 0:
            print(f'[{label}] {aid} -> RECORDS({nrec}) 服务可用 '
                  f'（耗时 {time.time()-t0:.1f}s，轮询 {i} 次）', flush=True)
            return True, hits
        d = 1.6
        try:
            if ra:
                d = max(1.5, min(6.0, float(ra) + 0.4))
        except Exception:
            pass
        time.sleep(d)
    hits.append(f'try{i}: t={time.time()-t0:5.1f}s --- {budget_sec:.0f}s 预算耗尽仍无 records')
    print(f'[{label}] {aid} -> 无 records（{budget_sec:.0f}s 内）', flush=True)
    return False, hits


print('--- 探针1：缓存 alpha E5vj5YdL ---', flush=True)
ok1, h1 = probe('E5vj5YdL', 'CACHED')
for x in h1: print('   ', x, flush=True)

# 找全新候选（未提交、无缓存）
fresh = []
for pre in ['w112_', 'w114_', 'w115_', 'w116_', 'w118_', 'w119_']:
    for f in sorted(glob.glob(f'data/alpha_quality_analysis/mined/{pre}*.json')):
        try: d = json.load(open(f))
        except Exception: continue
        aid = d.get('id')
        if not aid or aid in done: continue
        b = d.get('is') or {}; te = d.get('test') or {}
        if (b.get('sharpe') or 0) + (b.get('fitness') or 0) < 4.0: continue
        if (te.get('sharpe') or 0) < 1.25: continue
        fresh.append((pre, aid, d.get('_cid'), b.get('sharpe'), b.get('fitness'), te.get('sharpe')))
print(f'--- 达标未提交候选: {len(fresh)} 个 ---', flush=True)
tab = {}
for pre, aid, cid, S, F, tS in fresh:
    tab.setdefault(pre, []).append((aid, cid, S, F, tS))
for pre in ['w112_','w114_','w115_','w116_','w118_','w119_']:
    print(f'   {pre}: {len(tab.get(pre, []))}', flush=True)

ok2 = None
if fresh:
    pre, aid, cid, S, F, tS = fresh[0]
    print(f'--- 探针2：全新候选 {cid} {aid} S={S} F={F} tS={tS} ---', flush=True)
    ok2, h2 = probe(aid, 'FRESH')
    for x in h2: print('   ', x, flush=True)

print('=== 判定 ===', flush=True)
print('缓存探针:', 'UP' if ok1 else 'DOWN', flush=True)
print('全新探针:', ('UP' if ok2 else 'DOWN') if ok2 is not None else 'N/A', flush=True)
print('服务真实状态:', 'RESTORED' if ok2 else 'STILL_DOWN', flush=True)

json.dump({'cached_ok': ok1, 'fresh_ok': ok2, 'backlog': {k: len(v) for k, v in tab.items()},
           'backlog_total': len(fresh), 'ledger': len(done)},
          open('_autologs/probe_0915.json', 'w'), ensure_ascii=False, indent=1)
