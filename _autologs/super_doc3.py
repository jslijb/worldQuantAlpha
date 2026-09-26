# -*- coding: utf-8 -*-
"""super_doc3.py —— 原始 dump challenge-help"""
import json, io, requests

sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

for pid in ['challenge-help']:
    r = sess.get('https://api.worldquantbrain.com/tutorial-pages/' + pid)
    io.open('_autologs/_raw_%s.json' % pid, 'w', encoding='utf-8').write(
        json.dumps(r.json(), ensure_ascii=False, indent=1))
    print(pid, r.status_code, len(r.text))
