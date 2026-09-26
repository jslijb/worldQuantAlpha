# -*- coding: utf-8 -*-
"""挑战赛实时读数 + 全部字段 dump（比赛口径校准用）"""
import json, io, time, requests

OUT = io.open(r'D:\Python\worldquant\_autologs\_chal_now.txt', 'w', encoding='utf-8')


def say(*a):
    m = ' '.join(str(x) for x in a)
    OUT.write(m + '\n')
    OUT.flush()
    try:
        print(m)
    except Exception:
        pass


s = requests.Session()
s.auth = tuple(json.load(io.open(r'D:\Python\worldquant\brain_credentials.txt', encoding='utf-8')))
for _ in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass
    time.sleep(3)

j = s.get('https://api.worldquantbrain.com/competitions/challenge', timeout=60).json()
say('====== 顶层 keys ======')
say(list(j.keys()))
say()
say('====== competition 主体（去掉长文本）======')
for k, v in j.items():
    if k in ('leaderboard', 'scoring', 'helpText', 'progress'):
        continue
    say('%-24s %s' % (k, str(v)[:200]))
say()
say('====== leaderboard ======')
for k, v in (j.get('leaderboard') or {}).items():
    say('%-24s %s' % (k, str(v)[:200]))
say()
say('====== scoring ======')
say(json.dumps(j.get('scoring'), ensure_ascii=False, indent=1)[:4000])
say()
say('====== progress ======')
say(json.dumps(j.get('progress'), ensure_ascii=False, indent=1)[:2000])
say()

c = s.get('https://api.worldquantbrain.com/users/self/alphas',
          params={'limit': 1, 'stage': 'OS'}, timeout=60).json().get('count')
say('OS count =', c)

# 找所有含分数字段的接口
say()
say('====== 其他可能的积分接口 ======')
for u in ['https://api.worldquantbrain.com/users/self',
          'https://api.worldquantbrain.com/users/self/competitions',
          'https://api.worldquantbrain.com/competitions',
          'https://api.worldquantbrain.com/users/self/points',
          'https://api.worldquantbrain.com/users/self/consultant',
          'https://api.worldquantbrain.com/users/self/level']:
    try:
        r = s.get(u, timeout=45)
        say('%-62s -> %d  %s' % (u.split('.com')[1], r.status_code, str(r.text)[:300].replace('\n', ' ')))
    except Exception as e:
        say(u, 'ERR', e)
    time.sleep(0.5)

OUT.close()
