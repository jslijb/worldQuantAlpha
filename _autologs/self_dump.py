# -*- coding: utf-8 -*-
"""self_dump.py —— 拉 /users/self 全文，看账号层级/权限标记"""
import json, io, requests

sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
sess.post('https://api.worldquantbrain.com/authentication')
r = sess.get('https://api.worldquantbrain.com/users/self')
d = r.json()
L = ['status=%s' % r.status_code, json.dumps(d, ensure_ascii=False, indent=1)]
io.open('_autologs/_self_dump.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
