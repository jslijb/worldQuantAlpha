# -*- coding: utf-8 -*-
import os as _os, pathlib as _pl
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break
"""相关性守望者：r 系列 6 个 A 档等待平台相关性计算结果，就绪即按豁免规则自动提交。
预算 90 分钟；提交成功 5 个即停。
"""
import requests, json, time, sys

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201
print('login ok', flush=True)

TARGETS = ['r1_p5_d6','r3_p5_d14','r4_p5_t006','r5_p5_t010','r6_p5_sec','r7_n2_d6']
META = {}
for cid in TARGETS:
    d = json.load(open(f'data/alpha_quality_analysis/mined/{cid}.json', encoding='utf-8'))
    META[cid] = {"aid": d['id'], "S": d['is']['sharpe'], "F": d['is']['fitness'],
                 "teS": (d.get('test') or {}).get('sharpe') or 0}

submitted = 0
DEADLINE = time.time() + 90 * 60
rounds = 0
while time.time() < DEADLINE and submitted < 5:
    rounds += 1
    for cid in list(TARGETS):
        if submitted >= 5: break
        m = META[cid]
        aid = m['aid']
        try:
            r = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/correlations/self')
            if float(r.headers.get('Retry-After', 0)) > 0 or not r.text:
                continue  # 未就绪
            cj = r.json()
            cmax = cj.get('max')
            if cmax is None:
                continue
            recs = cj.get('records') or []
            hot = [rec for rec in recs if len(rec) >= 7 and isinstance(rec[5], (int, float)) and rec[5] >= 0.7]
            topS = max((rec[6] for rec in hot if isinstance(rec[6], (int, float))), default=0.0)
            if cmax >= 0.7 and not (topS > 0 and m['S'] >= 1.10 * topS):
                print(f'[{rounds}] {cid} {aid} S={m["S"]:.2f} corr={cmax:.4f} 豁免线={1.10*topS:.2f} 不可过 -> 移除', flush=True)
                TARGETS.remove(cid)
                continue
            tag = 'corr直过' if cmax < 0.7 else f'豁免通过(corr={cmax:.4f}, S={m["S"]:.2f}>={1.10*topS:.2f})'
            r2 = sess.post(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
            print(f'[{rounds}] {cid} {aid} {tag} submit->{r2.status_code}', flush=True)
            if r2.status_code == 403:
                print('  被拒:', r2.text[:150], flush=True)
                TARGETS.remove(cid)
                continue
            final = None
            for _ in range(150):
                g = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}/submit')
                ra = float(g.headers.get('Retry-After', 0))
                if ra == 0: final = g; break
                time.sleep(ra)
            if final is not None:
                print('  提交返回:', final.status_code, final.text[:120], flush=True)
            d2 = sess.get(f'https://api.worldquantbrain.com/alphas/{aid}').json()
            ok = d2.get('status') == 'ACTIVE' and d2.get('stage') == 'OS'
            print(f'  验证: status={d2.get("status")} stage={d2.get("stage")} {"OK" if ok else "未到OS"}', flush=True)
            if ok:
                submitted += 1
                print(f'>>> 提交成功 {submitted}/5: {aid} (S+F={m["S"]+m["F"]:.2f})', flush=True)
                TARGETS.remove(cid)
        except Exception as e:
            print(f'[{rounds}] {cid} EXC {str(e)[:100]}', flush=True)
    time.sleep(20)

print(f'守望结束: 今日累计提交成功 {submitted} 个(本轮), 剩余候选 {len(TARGETS)} 个', flush=True)
