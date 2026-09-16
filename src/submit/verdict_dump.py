# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# verdict_dump.py —— 提交一次并把完整判决书落盘 + 打印 selfCorrelated 对手明细
# 用法: python verdict_dump.py <alpha_id> [cid]
# 产出: _autologs/verdict_{alpha_id}.json
import requests, json, time, sys
aid = sys.argv[1]
cid = sys.argv[2] if len(sys.argv) > 2 else aid
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201
r = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
print('POST', r.status_code, 'Location=', r.headers.get('Location'))
loc = r.headers.get('Location') or f'https://api.worldquantbrain.com/alphas/{aid}/submit'
body = None
for i in range(40):
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    if d.get('status') == 'ACTIVE' or d.get('stage') == 'OS':
        print('ACCEPTED 入池'); body = {'accepted': True, 'is': d.get('is')}; break
    p = sess.get(loc)
    ra = p.headers.get('Retry-After')
    if ra: time.sleep(min(float(ra), 8)); continue
    if p.status_code == 404: time.sleep(6); continue
    try: j = p.json()
    except Exception: time.sleep(4); continue
    body = j; break

if body is None:
    print('无判决'); sys.exit(1)
json.dump(body, open(f'_autologs/verdict_{aid}.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
sc = (body.get('is') or {}).get('selfCorrelated') or {}
recs = sc.get('records') or []
cols = []
try:
    cols = [f.get('name') if isinstance(f, dict) else f for f in ((sc.get('schema') or {}).get('properties') or [])]
except Exception: pass
print('selfCorrelated 字段:', cols)
print('max =', sc.get('max'), ' min =', sc.get('min'), ' 对手数 =', len(recs))
if recs:
    hdr = recs[0]
    # 通用解析：找出 correlation / sharpe 所在列（按 schema，找不到就按经验位置 5/6）
    def col(name, default_idx):
        for i, c in enumerate(cols):
            if name.lower() in str(c).lower(): return i
        return default_idx
    ci = col('correlation', 5)
    si = col('sharpe', 6)
    ii = col('id', 0)
    rows = []
    for rec in recs:
        try: rows.append((rec[ii], rec[ci], rec[si]))
        except Exception: rows.append((None, None, None))
    rows.sort(key=lambda x: -(x[1] or 0))
    print(f'{"alpha_id":14s} {"corr":>8s} {"sharpe":>8s}  豁免线(1.1*S)')
    for i, c, s in rows:
        line = round(1.10 * s, 3) if (s is not None and c is not None and c >= 0.7) else None
        print(f'{str(i):14s} {c!s:>8s} {s!s:>8s}  {line}')
