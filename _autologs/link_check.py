# -*- coding: utf-8 -*-
"""验证：①已提交 alpha 的当前状态（判断提交链路是否受 corr 服务影响）
        ②alpha detail 里是否带 selfCorrelation 字段（找绕过 correlations/self 的信息源）
        ③探索是否有替代 corr 端点"""
import json, os, csv, time, requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
r = s.post('https://api.worldquantbrain.com/authentication')
print('auth:', r.status_code)

rows = list(csv.DictReader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')))
rows = [r for r in rows if r.get('id')]
rows.sort(key=lambda r: (r.get('dateSubmitted') or ''))
out = []

out.append('=== 最近 12 个提交的当前状态 ===')
for r in rows[-12:]:
    aid = r['id'].strip()
    try:
        d = s.get(f'https://api.worldquantbrain.com/alphas/{aid}')
        if d.status_code != 200:
            out.append(f"  {aid} -> HTTP {d.status_code}")
            continue
        j = d.json()
        st = j.get('status'); sg = j.get('stage')
        # 找所有含 corr 的键
        cb = {k: v for k, v in j.items() if 'corr' in k.lower()}
        isd = j.get('is') or {}
        isc = {k: v for k, v in isd.items() if 'corr' in k.lower()}
        out.append(f"  {aid} | status={st} stage={sg} | corr字段(顶层)={cb} | corr字段(is)={isc}")
    except Exception as e:
        out.append(f"  {aid} EXC {e}")
    time.sleep(0.5)

out.append('')
out.append('=== 探测替代 corr 端点（不消耗提交）===')
probe = rows[-1]['id'].strip()
for path in [
    f'/alphas/{probe}/correlations/self',
    f'/alphas/{probe}/correlations/prod',
    f'/alphas/{probe}/correlations',
    f'/alphas/{probe}/correlations/self/prod',
    '/correlations/self',
]:
    try:
        rr = s.get('https://api.worldquantbrain.com' + path)
        body = (rr.text or '')[:120].replace('\n', ' ')
        out.append(f"  {path} -> {rr.status_code} RA={rr.headers.get('Retry-After')} len={len(rr.text or '')} | {body}")
    except Exception as e:
        out.append(f"  {path} EXC {e}")
    time.sleep(1.2)

out.append('')
out.append('=== 未提交候选的 mined json 里是否已存 corr 信息 ===')
import glob
fs = sorted(glob.glob('data/alpha_quality_analysis/mined/w12*.json'))[:3]
for f in fs:
    d = json.load(open(f, encoding='utf-8'))
    ck = {k: v for k, v in d.items() if 'corr' in k.lower()}
    ck2 = {k: v for k, v in (d.get('is') or {}).items() if 'corr' in k.lower()}
    out.append(f"  {os.path.basename(f)} | 顶层corr={list(ck.keys())} | is.corr={list(ck2.keys())} | 全部键={list(d.keys())}")

open('_autologs/link_check.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('\n'.join(out))
