# -*- coding: utf-8 -*-
"""super_probe2.py —— 探 Super Alpha 的正确接口（已解锁 100 提交线 = 每天白捡 1~60 USD）"""
import json, io, requests, time

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
sess.post('https://api.worldquantbrain.com/authentication')

L = []


def g(path):
    try:
        r = sess.get('https://api.worldquantbrain.com' + path)
        L.append('GET %-46s -> %s (%d) %s' % (path, r.status_code, len(r.content), r.text[:180]))
    except Exception as e:
        L.append('GET %-46s -> ERR %s' % (path, e))


def p(path, body):
    try:
        r = sess.post('https://api.worldquantbrain.com' + path, json=body)
        L.append('POST %-45s -> %s (%d) %s' % (path, r.status_code, len(r.content), r.text[:600]))
    except Exception as e:
        L.append('POST %-45s -> ERR %s' % (path, e))


for p_ in ['/users/self/superalphas', '/superalphas', '/users/self/superAlpha',
           '/users/self/alphas?type=SUPER&limit=3', '/users/self/alphas?stage=OS&type=SUPER&limit=3',
           '/users/self/alphas?limit=1&type=SUPER', '/consultant', '/users/self']:
    g(p_)

BASE = {'instrumentType': 'EQUITY', 'region': 'USA', 'universe': 'TOP3000', 'delay': 1,
        'decay': 0, 'neutralization': 'SUBINDUSTRY', 'truncation': 0.08, 'pasteurization': 'ON',
        'unitHandling': 'VERIFY', 'nanHandling': 'ON', 'language': 'FASTEXPR', 'visualization': False}

# 1) 空的 SUPER（看错误信息暴露必填字段）
p('/simulations', {'type': 'SUPER', 'settings': BASE})
# 2) 带 selection
p('/simulations', {'type': 'SUPER', 'settings': BASE, 'selection': {}})
# 3) 带 regular 列表
p('/simulations', {'type': 'SUPER', 'settings': BASE, 'regular': []})
# 4) docs / 说明
g('/simulations/super')
g('/tutorials')

io.open('_autologs/_super_probe2.txt', 'w', encoding='utf-8').write('\n\n'.join(L))
print('ok')
