# -*- coding: utf-8 -*-
"""ds_probe.py —— 平台数据集盘点：哪些类目有货、哪些零使用"""
import json, io, requests, collections

sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

L = []
r = sess.get('https://api.worldquantbrain.com/data-sets?limit=50')
L.append('data-sets -> %s count=%s' % (r.status_code, r.json().get('count') if r.status_code == 200 else '-'))

rows = []
off = 0
while off < 400:
    rr = sess.get('https://api.worldquantbrain.com/data-sets?limit=50&offset=%d' % off)
    if rr.status_code != 200:
        L.append('offset %d -> %s' % (off, rr.status_code))
        break
    j = rr.json()
    res = j.get('results', [])
    if not res:
        break
    rows.extend(res)
    off += 50

L.append('拉到数据集 %d 个' % len(rows))

# 按 category 归类
cat = collections.Counter()
for d in rows:
    c = (d.get('category') or {}).get('name') if isinstance(d.get('category'), dict) else d.get('category')
    cat[str(c)] += 1
L.append('\n== 数据集类目分布 ==')
for k, v in cat.most_common():
    L.append('  %-34s %d' % (k, v))

# 关键词命中：经济 / 宏观 / 科研
KEYS = ['macro', 'econom', 'inflation', 'gdp', 'interest', 'sentiment', 'news',
        'analyst', 'option', 'insider', 'short', 'patent', 'esg', 'supply']
L.append('\n== 关键词命中数据集（前 3 个字段示例）==')
for k in KEYS:
    hit = [d for d in rows if k in (d.get('id', '') + ' ' + str(d.get('name', ''))).lower()]
    if hit:
        ids = ', '.join('{}[{}f]'.format(d.get('id'), d.get('fieldCount')) for d in hit[:8])
        L.append('  %-10s %2d 个: %s' % (k, len(hit), ids))

# 全量清单（id + 字段数 + 用户数），看我们没碰的
L.append('\n== 全部数据集（按字段数排序，前 60）==')
for d in sorted(rows, key=lambda x: -(x.get('fieldCount') or 0))[:60]:
    L.append('  %-28s %5s fields  users=%-5s %s' % (
        d.get('id'), d.get('fieldCount'), d.get('userCount'),
        str(d.get('name'))[:44]))

io.open('_autologs/_ds_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
