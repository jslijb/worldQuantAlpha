# -*- coding: utf-8 -*-
"""离线第2步：稳健抽链接 + 解析 19 个【专题合集】/【总导航】索引帖，建立人工分类清单"""
import json
import os
import re
from collections import Counter, defaultdict

LGDIR = r'D:\Python\worldquant\_logs'
all_posts = json.load(open(os.path.join(LGDIR, 'forum_posts_full.json'), encoding='utf-8'))
by_id = {x['id']: x for x in all_posts}
LOG = os.path.join(LGDIR, 'forum_links.log')
logf = open(LOG, 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')


CUT15 = '2025-05-15'

# ---------- 稳健抽链接 ----------
HREF = re.compile(r'href="([^"]+)"', re.I)


def host_of(u):
    m = re.match(r'^(?:https?:)?//([^/?#]+)', u)
    if m:
        return m.group(1)
    if u.startswith('/'):
        return 'RELATIVE(support)'
    return 'OTHER'


recent = [x for x in all_posts if x['created_at'][:10] >= CUT15]
host_cnt = Counter()
post_links = defaultdict(list)
for x in recent:
    hrefs = [h.replace('&amp;', '&') for h in HREF.findall(x.get('details') or '')]
    hrefs = [h for h in hrefs if not h.startswith('#')]
    if not hrefs:
        continue
    post_links[x['id']] = hrefs
    for h in hrefs:
        host_cnt[host_of(h)] += 1

log('===== 超链接宿主分布（1.5 年内 %d 帖，%d 帖含链接，共 %d 条）=====' % (
    len(recent), len(post_links), sum(host_cnt.values())))
for h, c in host_cnt.most_common(50):
    log('  %-52s %d' % (h, c))

json.dump(post_links, open(os.path.join(LGDIR, 'forum_links_raw.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# ---------- 索引帖解析 ----------
INDEX_IDS = ['43673210106007']  # 总导航
for x in all_posts:
    t = x.get('title') or ''
    if '专题合集' in t or '工具合集' in t:
        INDEX_IDS.append(x['id'])

log('')
log('===== 索引帖 %d 篇 =====' % len(INDEX_IDS))

POST_URL = re.compile(r'(?:https?://support\.worldquantbrain\.com)?/hc/[a-z\-]+/community/posts/(\d+)')
curated = defaultdict(list)  # 分类 -> [(pid, 标题)]
for iid in INDEX_IDS:
    p = by_id.get(iid)
    if not p:
        log('  缺:', iid)
        continue
    title = p.get('title') or ''
    html = p.get('details') or ''
    # 取 <a href="...">文本</a>
    anchors = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S)
    got = []
    for href, txt in anchors:
        m = POST_URL.search(href)
        if not m:
            continue
        pid = m.group(1)
        t2 = re.sub(r'<[^>]+>', '', txt).strip()
        got.append((pid, t2))
    log('  %-56s %d 个帖链接' % (title[:56], len(got)))
    for pid, t2 in got:
        curated[title].append((pid, t2))

json.dump({k: v for k, v in curated.items()},
          open(os.path.join(LGDIR, 'forum_curated.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

allids = set()
for v in curated.values():
    for pid, _ in v:
        allids.add(pid)
log('')
log('索引帖覆盖的唯一帖子数:', len(allids))
# 与全库对照：有多少在 1.5 年内、有多少更老
n_recent = sum(1 for pid in allids if pid in by_id and by_id[pid]['created_at'][:10] >= CUT15)
n_old = sum(1 for pid in allids if pid in by_id and by_id[pid]['created_at'][:10] < CUT15)
n_missing = sum(1 for pid in allids if pid not in by_id)
log('  其中 1.5 年内 %d | 更老 %d | 不在本 topic 内 %d' % (n_recent, n_old, n_missing))

log('')
log('===== 【专题合集】Value Factor 收录帖 =====')
for k, v in curated.items():
    if 'Value Factor' in k:
        for pid, t2 in v:
            pp = by_id.get(pid)
            d = pp['created_at'][:10] if pp else '?'
            log('  %s | %s | %s' % (d, pid, t2[:70]))

logf.close()
