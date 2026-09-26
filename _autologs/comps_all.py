# -*- coding: utf-8 -*-
"""列出全部 11 个竞赛 + 我们参加状态（确认『打比赛』到底指哪个榜）"""
import json, io, time, requests

OUT = io.open(r'D:\Python\worldquant\_autologs\_comps_all.txt', 'w', encoding='utf-8')


def say(*a):
    m = ' '.join(str(x) for x in a)
    OUT.write(m + '\n')
    OUT.flush()


s = requests.Session()
s.auth = tuple(json.load(io.open(r'D:\Python\worldquant\brain_credentials.txt', encoding='utf-8')))
for _ in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass
    time.sleep(3)

say('====== 全部竞赛 ======')
for off in (0, 10):
    j = s.get('https://api.worldquantbrain.com/competitions',
              params={'limit': 10, 'offset': off}, timeout=60).json()
    for c in (j.get('results') or []):
        say('%-26s | %-34s | %s | %s -> %s | team=%s | status=%s' % (
            c.get('id'), c.get('name'), c.get('description'),
            c.get('startDate'), c.get('endDate'), c.get('teamBased'), c.get('status')))

say()
say('====== 我们参加的 ======')
j = s.get('https://api.worldquantbrain.com/users/self/competitions', timeout=60).json()
say('count =', j.get('count'))
for c in (j.get('results') or []):
    say(json.dumps(c, ensure_ascii=False)[:500])

say()
say('====== challenge 的 helpText ======')
j = s.get('https://api.worldquantbrain.com/competitions/challenge', timeout=60).json()
say(str(j.get('helpText'))[:3000])
say()
say('====== challenge 的 faq ======')
say(str(j.get('faq'))[:600])

OUT.close()
