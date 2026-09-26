# -*- coding: utf-8 -*-
"""super_doc.py —— 拉平台 tutorial-pages 目录，找 SuperAlpha / 解锁条件原文"""
import json, io, requests

sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

L = []
KEEP = ('super', 'unlock', 'challenge', 'score', 'level', 'payment', 'consultant', 'achieve')


def add(s):
    L.append(str(s))


# 1) 站点地图 / 页面列表
for p in ['/tutorial-pages', '/tutorial-pages/list', '/tutorial-pages/all', '/tutorials']:
    try:
        r = sess.get('https://api.worldquantbrain.com' + p)
        add('GET %-28s -> %s (%d)' % (p, r.status_code, len(r.content)))
        if r.status_code == 200:
            add('    ' + r.text[:1500].replace('\n', ' '))
    except Exception as e:
        add('GET %-28s -> ERR %s' % (p, e))
    add('')

# 2) 逐个猜 super 相关 page id
for pid in ['superalpha', 'super-alphas', 'superalpha-tutorial', 'super-alpha',
            'about-superalphas', 'challenge', 'leaderboard', 'scoring',
            'users/self/level', 'users/self/achievements', 'users/self/progress',
            'users/self/messages', 'users/self/payments']:
    try:
        r = sess.get('https://api.worldquantbrain.com/tutorial-pages/' + pid)
        tag = 'HIT' if r.status_code == 200 else '   '
        add('%s tutorial-pages/%-26s -> %s' % (tag, pid, r.status_code))
        if r.status_code == 200:
            j = r.json()
            add('    TITLE: %s' % str(j.get('title'))[:150])
            body = json.dumps(j, ensure_ascii=False)
            add('    LEN %d' % len(body))
    except Exception as e:
        add('    ERR %s' % e)

add('')
add('== 关键词命中（在已归档 learn 文档里）==')
import glob, os
for f in glob.glob('docs/study/learn/**/*.md', recursive=True):
    try:
        t = io.open(f, encoding='utf-8').read()
    except Exception:
        continue
    low = t.lower()
    for k in ('superalpha', '100 alphas', 'minimum', 'unlock'):
        if k in low:
            i = low.find(k)
            add('%-58s [%s] ...%s...' % (os.path.basename(f)[:56], k, t[max(0, i - 90):i + 160].replace('\n', ' ')))
            break

io.open('_autologs/_super_doc.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok -> _autologs/_super_doc.txt')
