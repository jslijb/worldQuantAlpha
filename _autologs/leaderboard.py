# -*- coding: utf-8 -*-
"""拉排行榜详情 + 找 Super Alpha 入口。"""
import json, io, requests

R = io.open('_autologs/_leaderboard.txt', 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

log('=== /competitions 全量 ===')
r = S.get('https://api.worldquantbrain.com/competitions', params={'limit': 20})
j = r.json()
log('count=%s' % j.get('count'))
for c in (j.get('results') or []):
    lb = c.get('leaderboard') or {}
    log('- id=%-24s name=%-34s status=%-10s rank=%s' % (c.get('id'), c.get('name'), c.get('status'), lb.get('rank')))

for u in ['https://api.worldquantbrain.com/competitions/challenge',
          'https://api.worldquantbrain.com/competitions/challenge/leaderboard',
          'https://api.worldquantbrain.com/competitions/challenge/leaderboard?limit=30',
          'https://api.worldquantbrain.com/competitions/challenge/score',
          'https://api.worldquantbrain.com/users/self/score']:
    r = S.get(u)
    log('')
    log('%-70s -> %s (%d)' % (u.replace('https://api.worldquantbrain.com', ''), r.status_code, len(r.text)))
    if r.status_code == 200:
        try:
            log(json.dumps(r.json(), ensure_ascii=False)[:1800])
        except Exception:
            log(r.text[:1200])

log('')
log('=== 我的 alpha 分页统计（stage=OS）===')
for stage in ('OS', 'IS'):
    r = S.get('https://api.worldquantbrain.com/users/self/alphas', params={'stage': stage, 'limit': 1})
    try:
        log('%s count=%s' % (stage, r.json().get('count')))
    except Exception:
        log('%s ERR %s' % (stage, r.status_code))
