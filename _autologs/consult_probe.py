# -*- coding: utf-8 -*-
"""consult_probe.py —— 探顾问 onboarding 申请档案（resume/employment/recruitment 三项全空）"""
import json, io, requests

sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

L = []


def g(p):
    try:
        r = sess.get('https://api.worldquantbrain.com' + p)
        L.append('GET %-46s -> %-4s %s' % (p, r.status_code, r.text[:400].replace('\n', ' ')))
        return r
    except Exception as e:
        L.append('GET %-46s -> ERR %s' % (p, e))


for p in ['/users/self', '/users/self/consultant', '/users/self/onboarding',
          '/users/self/recruitment', '/users/self/resume', '/users/self/employment',
          '/users/self/progress', '/users/self/level', '/users/self/events',
          '/users/self/trainings', '/onboarding', '/consultant', '/consultants/self',
          '/users/self/referral', '/users/self/invitations']:
    g(p)

# level 与分数：排行榜自己的行
L.append('')
L.append('== 排行榜自查 ==')
for p in ['/leaderboard?limit=3', '/users/self/leaderboard?limit=3', '/competition/challenge/leaderboard?limit=3']:
    g(p)

io.open('_autologs/_consult_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
