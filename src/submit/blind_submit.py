# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 盲提交器：corr 预检服务降级时，直接走 POST /submit 让平台自查（0914 先例：预检拥塞时提交通道独立可用）
# 用法: python blind_submit.py <alpha_id> <cid>   （cid 用于从 mined json 取表达式与指标）
# 一次只提一个；PENDING/TIMEOUT 即退出，不做下一个（防互堵）
import requests, json, time, sys, csv

aid = sys.argv[1]
cid = sys.argv[2] if len(sys.argv) > 2 else ''

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def alpha_active(a):
    try: d = sess.get(f'https://api.worldquantbrain.com/alphas/{a}').json()
    except Exception: return None
    if d.get('status') == 'ACTIVE' or d.get('stage') == 'OS': return d
    return None

d0 = alpha_active(aid)
if d0:
    print(f'{aid} 已经是 ACTIVE，无需提交'); sys.exit(0)

r = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
print(f'POST /submit -> {r.status_code}', flush=True)
if r.status_code not in (200, 201):
    print('REJECT:', r.text[:200]); sys.exit(1)

loc = r.headers.get('Location') or f'https://api.worldquantbrain.com/alphas/{aid}/submit'
verdict = None
for i in range(60):  # 60 轮 x ~10s ≈ 10 分钟
    if i % 3 == 2:
        d = alpha_active(aid)
        if d:
            verdict = ('ACTIVE', d); break
    try: p = sess.get(loc)
    except Exception as e:
        print(f'poll{i} NET {e}', flush=True); time.sleep(10); continue
    ra = p.headers.get('Retry-After')
    if ra: time.sleep(min(float(ra), 20)); continue
    try: j = p.json()
    except Exception:
        time.sleep(10); continue
    st = (j.get('status') or '', j.get('stage') or '')
    print(f'poll{i} status={st[0]} stage={st[1]}', flush=True)
    if st[0] == 'ACTIVE' or st[1] == 'OS':
        verdict = ('ACTIVE', sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()); break
    if st[0] in ('FAIL', 'DEPRECATED'):
        verdict = (st[0], j); break
    time.sleep(8)

if not verdict:
    d = alpha_active(aid)
    verdict = ('ACTIVE', d) if d else ('PENDING', None)

state, info = verdict
print(f'=== {aid} verdict: {state} ===', flush=True)
if state == 'ACTIVE' and info:
    ds = info.get('dateSubmitted')
    b = info.get('is') or {}
    expr = ''
    if cid:
        try: expr = json.load(open(f'data/alpha_quality_analysis/mined/{cid}.json')).get('regular', {}).get('code', '')
        except Exception: pass
    with open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', 'a', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow([aid, expr, b.get('sharpe'), b.get('fitness'), b.get('turnover'), b.get('returns'),
                    b.get('drawdown'), '', ds, info.get('settings', {}).get('decay'),
                    info.get('settings', {}).get('neutralization'), f'0915-blind-{cid or aid}'])
    print(f'*** 台账已追加 {aid} dateSubmitted={ds}', flush=True)
elif state == 'FAIL':
    print('FAIL 详情:', json.dumps(info)[:400], flush=True)
else:
    print('PENDING —— 停止后续盲提交，防互堵；稍后用 GET /alphas/{id} 复查终态', flush=True)
