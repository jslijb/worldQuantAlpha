# -*- coding: utf-8 -*-
"""check_fail_hist.py —— LOW_SUB_UNIVERSE_SHARPE 是不是提交拦路虎？

判据：若已入池(ACTIVE/OS)的 alpha 里有人带着这个 FAIL 进池 → 它不是拦路虎；
      若 107 条入池记录里一条都没有 → 它极可能就是拒信项。
同时统计未提交池里该 FAIL 与 universe 的关系。
"""
import os as _os, pathlib as _pl, json, io, collections
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
import requests

L = []
led = []
for ln in io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig'):
    p = ln.split(',', 1)
    if p and p[0].strip() and p[0].strip() != 'id':
        led.append(p[0].strip().strip('"'))
seen = []
for x in led:
    if x not in seen:
        seen.append(x)
L.append('台账唯一 id = %d' % len(seen))

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if sess.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass

# 1) 已入池 alpha 的 FAIL 分布
ok = 0
fail_names = collections.Counter()
uni_fail = collections.Counter()
for aid in seen:
    try:
        d = sess.get('https://api.worldquantbrain.com/alphas/' + aid).json()
    except Exception as e:
        L.append('  %s NET %s' % (aid, str(e)[:50])); continue
    if not d or not d.get('id'):
        L.append('  %s 取不到' % aid); continue
    ok += 1
    st = d.get('settings') or {}
    b = d.get('is') or {}
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    for f in fa:
        fail_names[f] += 1
        uni_fail[(f, st.get('universe'))] += 1
L.append('已入池取到 %d 条；其中带 FAIL 的记录：' % ok)
if not fail_names:
    L.append('  （无任何 FAIL —— 已入池的 alpha 全是干净闸门进的）')
for k, v in fail_names.most_common(30):
    L.append('  %-32s %d' % (k, v))
L.append('  FAIL × universe 明细：')
for (f, u), v in uni_fail.most_common(30):
    L.append('    %-32s %-10s %d' % (f, u, v))

# 2) 未提交池里 LOW_SUB_UNIVERSE_SHARPE 的分布
api = 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
data = json.load(io.open(api, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
L.append('')
L.append('未提交池 %d 条：' % len(data))
cnt = collections.Counter()
for a in data:
    st = a.get('settings') or {}
    b = a.get('is') or {}
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    key = '有FAIL' if fa else '无FAIL'
    cnt[(key, st.get('universe'))] += 1
    if 'LOW_SUB_UNIVERSE_SHARPE' in fa:
        cnt[('LOW_SUB_UNIVERSE_SHARPE', st.get('universe'))] += 1
for k, v in sorted(cnt.items(), key=lambda x: (x[0][0], str(x[0][1]))):
    L.append('  %-26s %-10s %d' % (k[0], k[1], v))

io.open('_autologs/_fail_hist.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
