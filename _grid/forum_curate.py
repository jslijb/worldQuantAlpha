# -*- coding: utf-8 -*-
"""离线第3步：修 ID 类型 -> 索引帖分类映射 -> 生成 VF/Alpha 1.5年内 精选清单"""
import json
import os
import re
from collections import Counter, defaultdict

LGDIR = r'D:\Python\worldquant\_logs'
all_posts = json.load(open(os.path.join(LGDIR, 'forum_posts_full.json'), encoding='utf-8'))
by_id = {str(x['id']): x for x in all_posts}          # 统一 str
LOG = os.path.join(LGDIR, 'forum_curate.log')


def log(*a):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(' '.join(str(x) for x in a) + '\n')


open(LOG, 'w').close()
CUT15, CUT1Y = '2025-05-15', '2025-11-15'

# --------- 索引帖 ---------
INDEX_IDS = []
for x in all_posts:
    t = x.get('title') or ''
    if '专题合集' in t or '工具合集' in t or '总导航' in t:
        INDEX_IDS.append(str(x['id']))
log('索引帖:', len(INDEX_IDS))

POST_URL = re.compile(r'(?:https?://support\.worldquantbrain\.com)?/hc/[a-zA-Z\-]+/community/posts/(\d+)')
curated = defaultdict(list)
for iid in INDEX_IDS:
    p = by_id.get(iid)
    if not p:
        continue
    html = p.get('details') or ''
    for href, txt in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
        m = POST_URL.search(href)
        if not m:
            continue
        pid = m.group(1)
        t2 = re.sub(r'<[^>]+>', '', txt).replace('&gt;', '>').replace('&amp;', '&').strip()
        curated[p['title']].append((pid, t2))

allids = {pid for v in curated.values() for pid, _ in v}
in_topic = [pid for pid in allids if pid in by_id]
log('索引覆盖唯一帖:', len(allids), '| 在本 topic 内:', len(in_topic))
log('  1.5年内:', sum(1 for pid in in_topic if by_id[pid]['created_at'][:10] >= CUT15))

# --------- 相关分类（VF / Alpha 研究法）----------
REL_CATS = ['Value Factor', 'Osmosis', 'Alpha 研究与组合', '相关性', 'Machine Alpha',
            '研究方法与实验设计', 'PnL、OS 与组合绩效复盘', 'Super Alpha', '论文到 Alpha',
            'Python Alpha', '价量、动量与交易行为', '基本面、财报与估值', '顾问收入与成长',
            '稳健性、过拟合与风险', '数据推荐与数据集探索', '数据与研究基础']

selected = {}   # pid -> {'cats': [...], 'title':..., 'date':...}
for cat, items in curated.items():
    if not any(k in cat for k in REL_CATS):
        continue
    for pid, t2 in items:
        p = by_id.get(pid)
        if not p:
            continue
        d = p['created_at'][:10]
        if d < CUT15:
            continue
        rec = selected.setdefault(pid, {'cats': [], 'title': p.get('title') or t2,
                                       'date': d, 'votes': p.get('votes'),
                                       'comments': p.get('comments')})
        rec['cats'].append(cat.split('】')[-1][:14])

log('')
log('===== 索引帖命中（VF/Alpha 相关分类 + 1.5年内）=====')
log('条数:', len(selected))
for pid, r in sorted(selected.items(), key=lambda kv: kv[1]['date'], reverse=True):
    log('%s | %s | v%-3s c%-3s | %-22s | %s' % (r['date'], pid, r['votes'], r['comments'],
                                                '/'.join(sorted(set(r['cats'])))[:22],
                                                (r['title'] or '')[:58]))

json.dump(selected, open(os.path.join(LGDIR, 'forum_selected.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump({k: v for k, v in curated.items()},
          open(os.path.join(LGDIR, 'forum_curated.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
log('')
log('已落盘 forum_selected.json')
