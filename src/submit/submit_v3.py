# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
# submit_v3：正确取裁决的提交器（0916 实测定案）
#   机制：POST /alphas/{id}/submit -> 201；轮询 GET Location：
#     - 200 + Retry-After + 空 body = 相关计算中（实测 3~4 轮、约 4 秒）
#     - 403 + {"is":{"checks":[...]}} = 被拒判决书（含 SELF_CORRELATION 数值）
#     - alpha 变 ACTIVE/stage=OS      = 成功入池
#   旧版 blind_submit.py 只认顶层 status/stage 键，把 403 判决当空数据丢弃 -> 假 PENDING。
# 用法: python submit_v3.py <alpha_id> <cid>   （cid 取 mined json 表达式）
# 纪律：一次一个，串行；台账/裁决档案只追加。
import requests, json, time, sys, csv, datetime

aid = sys.argv[1]
cid = sys.argv[2] if len(sys.argv) > 2 else ''

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

def alpha_detail(a):
    try: return sess.get(f'https://api.worldquantbrain.com/alphas/{a}').json()
    except Exception: return None

d0 = alpha_detail(aid)
if d0 and (d0.get('status') == 'ACTIVE' or d0.get('stage') == 'OS'):
    print(f'{aid} 已经是 ACTIVE，无需提交'); sys.exit(0)

r = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
print(f'POST /submit -> {r.status_code}', flush=True)
if r.status_code not in (200, 201):
    print('REJECT:', r.text[:300]); sys.exit(1)

loc = r.headers.get('Location') or f'https://api.worldquantbrain.com/alphas/{aid}/submit'
verdict = None
t0 = time.time()
for i in range(60):  # 90 秒预算足够（实测 4 秒出判决）
    d = alpha_detail(aid)
    if d and (d.get('status') == 'ACTIVE' or d.get('stage') == 'OS'):
        verdict = ('ACCEPTED', None, d); break
    try:
        p = sess.get(loc)
    except Exception as e:
        print(f'poll{i} NET {e}', flush=True); time.sleep(5); continue
    ra = p.headers.get('Retry-After')
    if ra:
        time.sleep(min(float(ra), 10)); continue
    # 无 Retry-After：要么判决书（403+checks JSON），要么端点失效（404）
    if p.status_code == 404:
        print(f'poll{i} 404 —— 判决端点失效，稍后可重试', flush=True); time.sleep(8); continue
    try:
        j = p.json()
    except Exception:
        time.sleep(5); continue
    checks = (j.get('is') or {}).get('checks') or []
    # ⚠️ 未提交 alpha 的默认占位符就是 8 条 checks 全 PENDING —— 那不是判决书！
    # ⚠️⚠️ 更隐蔽的坑（0916 QPbP6aRQ 实测）：403 body 里 checks 带 PASS/数值、但**一条 FAIL 都没有**
    #      —— 那是「检查已跑完且都过」的回执，不是拒信。此时 alpha 会在几秒内变 ACTIVE。
    #      旧逻辑把「有 result 就算判决」→ 误判 REJECTED，台账漏记一条真入池的 alpha。
    #      正确判据：**只有出现 FAIL 才是真拒信**；无 FAIL 一律继续轮询等 ACTIVE。
    fails = [c for c in checks if c.get('result') == 'FAIL']
    if fails:
        verdict = ('REJECTED', j, None); break
    time.sleep(5)

if not verdict:
    verdict = ('TIMEOUT', None, None)

state, j, d = verdict
print(f'=== {aid} verdict: {state} ({time.time()-t0:.0f}s) ===', flush=True)

sc = None; fail_names = []; vals = {}
if j:
    for c in (j.get('is') or {}).get('checks') or []:
        vals[c.get('name')] = (c.get('result'), c.get('value'), c.get('limit'))
        if c.get('result') == 'FAIL':
            fail_names.append(c.get('name'))
        if c.get('name') == 'SELF_CORRELATION' and c.get('value') is not None:
            sc = c.get('value')          # 不论 PASS/FAIL 都取值（旧版只在 FAIL 分支里取 → 常为 None）
if state == 'ACCEPTED' and d:
    sc = (d.get('is') or {}).get('selfCorrelation') or sc
    print('selfCorr=', sc)
elif state == 'REJECTED':
    print('FAIL 项:', fail_names, 'selfCorr=', sc)
elif j:
    # 有回执但无 FAIL、又没等到 ACTIVE：状态未知，**不要当拒信记档**
    state = 'UNKNOWN'
    print('有回执但无 FAIL、未变 ACTIVE → 状态未知；重跑同命令即可确认（会走 already-ACTIVE 分支）')

# 裁决档案（只追加）
verdict_row = [datetime.datetime.now().isoformat(timespec='seconds'), aid, cid, state,
               sc, ';'.join(fail_names)]
try:
    with open('data/alpha_quality_analysis/SUBMIT_VERDICTS.csv', 'a', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow(verdict_row)
except Exception as e:
    print('verdict 档案写入失败:', e)

if state == 'ACCEPTED':
    ds = d.get('dateSubmitted'); b = d.get('is') or {}
    expr = ''
    if cid:
        try: expr = json.load(open(f'data/alpha_quality_analysis/mined/{cid}.json')).get('regular', {}).get('code', '')
        except Exception: pass
    with open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', 'a', encoding='utf-8-sig', newline='') as f:
        csv.writer(f).writerow([aid, expr, b.get('sharpe'), b.get('fitness'), b.get('turnover'), b.get('returns'),
                                b.get('drawdown'), sc if sc is not None else '', ds, d.get('settings', {}).get('decay'),
                                d.get('settings', {}).get('neutralization'), f'0916-v3-{cid or aid}'])
    print(f'*** 台账已追加 {aid} dateSubmitted={ds} selfCorr={sc}', flush=True)
elif state == 'REJECTED':
    print('被拒：', {k: v for k, v in vals.items() if v[0] == 'FAIL'})
else:
    print('未出判决（TIMEOUT/404/UNKNOWN），停止，勿并发下一条')
