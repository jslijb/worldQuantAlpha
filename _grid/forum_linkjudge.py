# -*- coding: utf-8 -*-
"""离线第4步：分析 671 篇精选帖里的超链接，分类是否与 Alpha/VF 相关"""
import json
import os
import re
from collections import Counter, defaultdict

LGDIR = r'D:\Python\worldquant\_logs'
all_posts = json.load(open(os.path.join(LGDIR, 'forum_posts_full.json'), encoding='utf-8'))
by_id = {str(x['id']): x for x in all_posts}
sel = json.load(open(os.path.join(LGDIR, 'forum_selected.json'), encoding='utf-8'))
LOG = os.path.join(LGDIR, 'forum_linkjudge.log')
open(LOG, 'w').close()


def log(*a):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(' '.join(str(x) for x in a) + '\n')


HREF = re.compile(r'href="([^"]+)"', re.I)


def norm(u):
    u = u.replace('&amp;', '&').strip()
    if u.startswith('//'):
        u = 'https:' + u
    elif u.startswith('/'):
        u = 'https://support.worldquantbrain.com' + u
    return u


def host_of(u):
    m = re.match(r'^https?://([^/?#]+)', u)
    return m.group(1) if m else 'OTHER'


POST_URL = re.compile(r'/community/posts/(\d+)')
links = defaultdict(list)   # url -> [(pid, anchor_text)]
for pid in sel:
    p = by_id.get(pid)
    if not p:
        continue
    html = p.get('details') or ''
    for href, txt in re.findall(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html, re.I | re.S):
        u = norm(href)
        if u.startswith('#'):
            continue
        t = re.sub(r'<[^>]+>', '', txt).replace('&gt;', '>').replace('&amp;', '&').strip()
        links[u].append((pid, t[:60]))

log('精选帖:', len(sel), '| 唯一链接:', len(links), '| 链接实例:', sum(len(v) for v in links.values()))

# 内部帖子链接（论坛内互引）单独统计
internal = {u: v for u, v in links.items() if POST_URL.search(u) and 'support.worldquantbrain.com' in u}
external = {u: v for u, v in links.items() if u not in internal}
log('内部互引帖链接:', len(internal), '| 外部链接:', len(external))

host_cnt = Counter(host_of(u) for u in external)
log('')
log('===== 外部链接宿主 TOP40 =====')
for h, c in host_cnt.most_common(40):
    log('  %-46s %d' % (h, c))

# 判相关：一手 Alpha/VF 语料优先
REL_HOST_PAT = [
    (r'papers\.ssrn\.com|doi\.org|arxiv\.org|ssrn\.com', '论文'),
    (r'^(api|platform|support)\.worldquantbrain\.com', '平台官方'),
    (r'worldquantbrain\.zendesk\.com', '平台论坛旧域'),
    (r'github\.com|raw\.githubusercontent\.com|gitee\.com', '代码仓'),
    (r'worldquant', 'WQ 相关'),
]
NOISE_HOST_PAT = [r'pan\.(quark|baidu)\.cn', r'linux\.do', r'bilibili', r'mp\.weixin\.qq\.com',
                  r'cloud\.tencent', r'nodejs\.org', r'python\.org', r'pypi\.org',
                  r'openrouter|deepseek|bigmodel|nvidia|agnes|iflow|z\.ai|opencode',
                  r'check-host|globalping', r'127\.0\.0\.1']

classified = defaultdict(list)
for u, refs in external.items():
    h = host_of(u)
    cat = None
    for pat, name in REL_HOST_PAT:
        if re.search(pat, u, re.I):
            cat = name
            break
    if not cat:
        if any(re.search(p, u, re.I) for p in NOISE_HOST_PAT):
            cat = '无关-工具/网盘/模型'
        else:
            cat = '待判'
    classified[cat].append((u, len(refs), refs[0][0], refs[0][1]))

log('')
log('===== 外部链接分类 =====')
for cat in sorted(classified, key=lambda k: -len(classified[k])):
    log('  %-16s %d' % (cat, len(classified[cat])))

for cat in ['论文', '平台官方', '代码仓', 'WQ 相关', '平台论坛旧域', '待判']:
    items = classified.get(cat) or []
    if not items:
        continue
    log('')
    log('===== [%s] %d 条 =====' % (cat, len(items)))
    for u, cnt, pid, anchor in sorted(items, key=lambda z: -z[1])[:60]:
        log('  x%-2d %-58s <- %s | %s' % (cnt, anchor[:58], pid, u[:110]))

json.dump({u: v for u, v in classified.items()},
          open(os.path.join(LGDIR, 'forum_extlinks.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump({u: v for u, v in internal.items()},
          open(os.path.join(LGDIR, 'forum_intlinks.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
log('')
log('已落盘 forum_extlinks.json / forum_intlinks.json')
