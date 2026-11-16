# -*- coding: utf-8 -*-
"""最终精选集：索引命中 ∪ 票>=30关键词命中 ∪ 置顶VF合集链接（均限 1.5 年内）"""
import json
import os
import re

LGDIR = r'D:\Python\worldquant\_logs'
CUT15, CUT1Y = '2025-05-15', '2025-11-15'

ps = {str(x['id']): x for x in json.load(open(os.path.join(LGDIR, 'forum_posts_full.json'), encoding='utf-8'))}
filt = json.load(open(os.path.join(LGDIR, 'forum_filtered.json'), encoding='utf-8'))
old = json.load(open(os.path.join(LGDIR, 'forum_selected.json'), encoding='utf-8'))
curated = json.load(open(os.path.join(LGDIR, 'forum_curated.json'), encoding='utf-8'))

rel = {str(t['id']): t['rel'] for t in filt['tagged']}
A = set(old)                                                     # 索引帖分类命中
B = {k for k, p in ps.items()
     if p['created_at'][:10] >= CUT15
     and rel.get(k) in ('vf', 'alpha')
     and int(p.get('votes') or 0) >= 30}                         # 高票关键词命中

PIN = '32032776365079'                                           # 置顶 VF 合集
POST = re.compile(r'/community/posts/(\d+)')
C = set()
cname = {}
for k, v in curated.items():
    pass
p = ps[PIN]
for href, txt in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', p['details'], re.I | re.S):
    m = POST.search(href)
    if m:
        pid = m.group(1)
        if pid in ps and ps[pid]['created_at'][:10] >= CUT15:
            C.add(pid)
            cname[pid] = re.sub(r'<[^>]+>', '', txt).strip()[:60]

S = A | B | C
print('A 索引帖分类命中 :', len(A))
print('B 高票关键词命中 :', len(B))
print('C 置顶VF合集链接 :', len(C), '（其中新增 %d）' % len(C - A))
print('并集             :', len(S))
print('  B 新增（不在A）:', len(B - A))
print('  C 新增（不在A）:', len(C - A))

# 构造最终结构
out = {}
for pid in S:
    q = ps.get(pid)
    if not q:
        continue
    cats = []
    if pid in old:
        cats = list(old[pid]['cats'])
    if pid in B and not cats:
        cats = ['关键词/高票']
    if pid in C:
        cats.append('置顶VF合集')
    out[pid] = {
        'title': q.get('title') or old.get(pid, {}).get('title') or cname.get(pid, ''),
        'date': q['created_at'][:10],
        'votes': q.get('votes'),
        'comments': q.get('comments'),
        'cats': sorted(set(cats)),
        'rel': rel.get(pid, ''),
        'src': ''.join(['A' if pid in A else '', 'B' if pid in B else '', 'C' if pid in C else '']),
    }

json.dump(out, open(os.path.join(LGDIR, 'forum_selected.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('已写 forum_selected.json:', len(out))

# 打印 C 新增的
print('')
print('置顶合集带进来的新增帖：')
for pid in sorted(C - A, key=lambda k: ps[k]['created_at'], reverse=True):
    q = ps[pid]
    print('  %s | %s | v%s | %s' % (q['created_at'][:10], pid, q.get('votes'),
                                    (q.get('title') or '')[:56]))
