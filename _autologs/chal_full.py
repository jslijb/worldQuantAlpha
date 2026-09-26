# -*- coding: utf-8 -*-
import io, json, time, requests

OUT = io.open(r'D:\Python\worldquant\_autologs\_chal_full.txt', 'w', encoding='utf-8')
def say(*a):
    s = ' '.join(str(x) for x in a)
    print(s); OUT.write(s + '\n'); OUT.flush()

s = requests.Session()
s.auth = tuple(json.load(io.open(r'D:\Python\worldquant\brain_credentials.txt', encoding='utf-8')))
for _ in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        pass
    time.sleep(3)

r = s.get('https://api.worldquantbrain.com/competitions/challenge', timeout=60)
io.open(r'D:\Python\worldquant\_autologs\_chal_full.json', 'w', encoding='utf-8').write(r.text)
j = r.json()
say('顶层字段:', list(j.keys()))
say('')
for k, v in j.items():
    if isinstance(v, (dict, list)):
        say('### %s ###' % k)
        say(json.dumps(v, ensure_ascii=False, indent=1)[:2500])
    else:
        say('### %s = %s' % (k, v))
    say('')

# 全部竞赛的 scoring 字段
r2 = s.get('https://api.worldquantbrain.com/competitions', params={'limit': 30}, timeout=60)
try:
    j2 = r2.json()
    rows = j2 if isinstance(j2, list) else j2.get('results', [])
    say('=== 全部竞赛 scoring 口径 ===')
    for c in rows:
        say('%-26s status=%-10s scoring=%-14s team=%s  desc=%s'
            % (c.get('id'), c.get('status'), c.get('scoring'), c.get('teamBased'), str(c.get('description'))[:60]))
except Exception as e:
    say('competitions ERR', e)

OUT.close()
