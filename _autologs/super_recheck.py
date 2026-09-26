# -*- coding: utf-8 -*-
"""super_recheck.py —— 107 条提交后重测 Super Alpha 权限（上次测是在 87 条时）"""
import json, io, requests

L = []


def log(s):
    L.append(str(s))


sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

# 1) 账号状态：提交数 / 层级 / 权限位
r = sess.get('https://api.worldquantbrain.com/users/self')
if r.status_code == 200:
    u = r.json()
    log('== users/self 关键字段 ==')
    for k in sorted(u.keys()):
        v = u[k]
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)[:220]
        log('  %-28s %s' % (k, v))
else:
    log('users/self -> %s' % r.status_code)

# 2) 分页 count（平台真数）
r = sess.get('https://api.worldquantbrain.com/users/self/alphas?limit=1')
if r.status_code == 200:
    log('\n== alphas count ==')
    j = r.json()
    log('  count(total)=%s' % j.get('count'))
    for st in ('IS', 'OS'):
        rr = sess.get('https://api.worldquantbrain.com/users/self/alphas?limit=1&stage=%s' % st)
        if rr.status_code == 200:
            log('  stage=%-3s count=%s' % (st, rr.json().get('count')))
    for s in ('UNSUBMITTED', 'ACTIVE'):
        rr = sess.get('https://api.worldquantbrain.com/users/self/alphas?limit=1&status=%s' % s)
        if rr.status_code == 200:
            log('  status=%-12s count=%s' % (s, rr.json().get('count')))

# 3) Super Alpha 相关端点
log('\n== super 端点探测 ==')
for p in ['/users/self/super-alphas?limit=5', '/super-alphas?limit=5',
          '/users/self/superAlphas?limit=5', '/users/self/alphas?type=SUPER&limit=3']:
    try:
        r = sess.get('https://api.worldquantbrain.com' + p)
        log('GET %-42s -> %s (%d) %s' % (p, r.status_code, len(r.content), r.text[:300].replace('\n', ' ')))
    except Exception as e:
        log('GET %-42s -> ERR %s' % (p, e))

# 4) 关键：实测 SUPER 模拟权限（与 87 条时同参数对比）
BASE = {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1,
        'decay': 0, 'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
        'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False}
log('\n== SUPER simulation 权限实测（核心）==')
for name, body in [
    ('空 SUPER', {'type': 'SUPER', 'settings': BASE}),
    ('SUPER+combo', {'type': 'SUPER', 'settings': BASE, 'combo': 'combo_a(alpha)', 'selection': '1'}),
]:
    try:
        r = sess.post('https://api.worldquantbrain.com/simulations', json=body)
        log('POST %-12s -> %s (%d) %s' % (name, r.status_code, len(r.content), r.text[:700].replace('\n', ' ')))
    except Exception as e:
        log('POST %-12s -> ERR %s' % (name, e))

io.open('_autologs/_super_recheck.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok -> _autologs/_super_recheck.txt')
