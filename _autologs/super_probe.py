# -*- coding: utf-8 -*-
"""探测 Super Alpha 相关平台端点。"""
import json, io, requests

R = io.open('_autologs/_super_probe.txt', 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

CANDS = [
    'https://api.worldquantbrain.com/users/self/super-alphas?limit=10',
    'https://api.worldquantbrain.com/super-alphas?limit=10',
    'https://api.worldquantbrain.com/users/self/alphas?stage=OS&limit=5',
    'https://api.worldquantbrain.com/competitions',
    'https://api.worldquantbrain.com/users/self/competitions',
    'https://api.worldquantbrain.com/users/self/consultant',
    'https://api.worldquantbrain.com/users/self/payments',
    'https://api.worldquantbrain.com/users/self/leaderboard',
    'https://api.worldquantbrain.com/leaderboard/consultant',
]
for u in CANDS:
    try:
        r = S.get(u)
        log('%-72s -> %s (%d bytes)' % (u.replace('https://api.worldquantbrain.com', ''), r.status_code, len(r.text)))
        if r.status_code == 200:
            log('    ' + r.text[:500].replace('\n', ' '))
    except Exception as e:
        log('%-72s -> ERR %s' % (u, e))
    log('')
