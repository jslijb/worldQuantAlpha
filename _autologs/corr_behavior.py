# -*- coding: utf-8 -*-
"""corr 端点行为实验：区分「服务故障」与「需要轮询等待」
对照组设计：
  A 组 = 已提交且 selfCorrelation 有值的 alpha（池中已有缓存，应较快返回）
  B 组 = 从未算过的全新候选（需平台现算）
规则：遵守 Retry-After 间隔（>=1.5s），单探针最多轮询 100 秒。
"""
import json, os, time, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
print('auth:', s.post('https://api.worldquantbrain.com/authentication').status_code)

# A 组：最近提交、已知有 selfCorrelation 的 alpha
A = ['akLmmvPW', 'kqVp6wnO', 'npKGgKLw']
# B 组：全新未提交候选
B = ['3q9NMgk6', 'MP1rjMj9', 'KPOAOXEE']

out = []
LIMIT = 100.0


def poll(aid, tag, limit=LIMIT):
    t0 = time.time()
    n = 0
    while time.time() - t0 < limit:
        n += 1
        try:
            r = s.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
        except Exception as e:
            out.append(f"    [{tag}] {aid} try{n} EXC {type(e).__name__}: {e}")
            time.sleep(3)
            continue
        ra = r.headers.get('Retry-After')
        blen = len(r.text or '')
        recs = None
        if r.status_code == 200 and blen > 0:
            try:
                recs = len((r.json() or {}).get('records') or [])
            except Exception:
                recs = -1
        el = time.time() - t0
        if n <= 3 or recs is not None or n % 10 == 0:
            out.append(f"    [{tag}] {aid} try{n:3} t={el:6.1f}s -> {r.status_code} RA={ra} len={blen} records={recs}")
        if recs is not None and recs >= 0:
            out.append(f"    [{tag}] {aid} >>> 拿到结果，共 {recs} 条 records（耗时 {el:.1f}s，轮询 {n} 次）")
            return n, el, recs
        d = 1.6
        try:
            if ra:
                d = max(1.5, min(6.0, float(ra) + 0.4))
        except Exception:
            pass
        time.sleep(d)
    out.append(f"    [{tag}] {aid} --- {LIMIT:.0f}s 内无结果（轮询 {n} 次）")
    return n, LIMIT, None


out.append('=== A 组：已提交 alpha（池中有缓存） ===')
for a in A:
    poll(a, 'A')
    out.append('')

out.append('=== B 组：全新候选（需平台现算） ===')
for b in B:
    poll(b, 'B')
    out.append('')

open('_autologs/corr_behavior.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
