# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# 第127轮：验证实验（2 条，定生死）
#   假设：fnd6 极冷字段（aC<30）无数据覆盖，锚腿=空信号，回测分数全部来自
#         "共享四腿 0.5 降权"骨架本身 → w125_g/w126_a~d 的 SF=4.40 是骨架分，假达标。
#   实验A（w127_a）：纯骨架（无锚，仅 0.5 共享四腿）——若 SF≈4.40/T≈0.314 即证实。
#   实验B（w127_b）：单锚 group_rank(fnd6_newq_xoptdqp/assets, LB)——若 S≈0 或长/空数异常即字段无数据。
import requests, json, time, os

OUT = 'data/alpha_quality_analysis/mined'

def BASE(delay=1, decay=4, neut='SUBINDUSTRY', trunc=0.08):
    return {'instrumentType':'EQUITY','region':'USA','universe':'TOP3000','delay':delay,'decay':decay,
     'neutralization':neut,'truncation':trunc,'pasteurization':'ON','unitHandling':'VERIFY',
     'nanHandling':'ON','language':'FASTEXPR','visualization':False,
     'startDate':'2019-01-01','endDate':'2023-12-31','testPeriod':'P1Y'}

LB = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'
def G(x): return f'group_rank({x}, {LB})'

SKELETON = ' + '.join(f'0.5*{G(x)}' for x in [
    'ts_av_diff(cash/assets, 45)',
    'ts_av_diff(cashflow_op/enterprise_value, 45)',
    '-ts_delta(close, 2)',
    'volume/ts_mean(volume, 60)'])

C = [
 ('w127_a', SKELETON, BASE()),
 ('w127_b', G('fnd6_newq_xoptdqp/assets'), BASE()),
]

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def post_retry(payload, cid):
    for att in range(8):
        try: r = sess.post('https://api.worldquantbrain.com/simulations', json=payload)
        except Exception as e:
            print(cid, 'NET', e, flush=True); time.sleep(20); continue
        if r.status_code in (200, 201): return r
        if r.status_code in (429, 504) or 'CONCURRENT' in r.text or 'rate limit' in r.text.lower():
            time.sleep(30 + att * 20); continue
        print(cid, 'REJECT', r.status_code, r.text[:300], flush=True); return None
    return None

def run_one(item):
    cid, expr, s = item
    of = f'{OUT}/{cid}.json'
    if os.path.exists(of):
        print(f'{cid}已有产出，跳过', flush=True); return
    r = post_retry({'type':'REGULAR','settings':s,'regular':expr}, cid)
    if r is None: return
    loc = r.headers.get('Location'); p = None
    for _ in range(400):
        try: p = sess.get(loc)
        except Exception as e:
            print(cid,'NET-poll',e,flush=True); time.sleep(20); continue
        ra = p.headers.get('Retry-After')
        if ra: time.sleep(float(ra)); continue
        break
    try: j = p.json()
    except Exception:
        print(cid, 'POLL-BAD', p.text[:200], flush=True); return
    aid = j.get('alpha')
    if not aid:
        print(f'{cid} FAIL {json.dumps(j)[:300]}', flush=True); return
    d = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
    d['_cid'] = cid
    json.dump(d, open(of, 'w'), ensure_ascii=False)
    b = d.get('is') or {}; te = d.get('test') or {}
    S = b.get('sharpe') or 0
    print(f"{cid} {aid} S={S:.2f} F={b.get('fitness')} SF={S+(b.get('fitness') or 0):.2f} "
          f"T={b.get('turnover')} testS={te.get('sharpe')} 多={b.get('longCount')} 空={b.get('shortCount')}", flush=True)

for item in C:
    run_one(item)
print('batch127 done', flush=True)
