# -*- coding: utf-8 -*-
"""离线：从 forum_posts_full.json 过滤 VF/Alpha + 1.5 年内 + 抽超链接"""
import json
import os
import re
from collections import Counter
from urllib.parse import urlparse

LGDIR = r'D:\Python\worldquant\_logs'
SRC = os.path.join(LGDIR, 'forum_posts_full.json')
LOG = os.path.join(LGDIR, 'forum_filter.log')

logf = open(LOG, 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')


all_posts = json.load(open(SRC, encoding='utf-8'))
log('总帖:', len(all_posts))

CUT15, CUT1Y = '2025-05-15', '2025-11-15'

KW_STRONG = ['vf', 'value factor', '价值因子', 'base payment', 'osmosis', 'pyramid', '金字塔',
             'atom', 'correlation', '相关性', 'combined', 'combine', 'isscore',
             'base', '分成', '收入', '美元', '刀', 'pay']
KW_WEAK = ['alpha', '阿尔法', '表达式', '模板', 'template', 'idea', '数据集', 'dataset',
           '算子', 'operator', '回测', 'simulat', 'universe', 'neutral', 'decay',
           'truncation', 'bucket', 'group_', 'ts_', 'rank', 'signal', '因子', 'sharpe',
           'fitness', 'turnover', '换手', 'submission', '提交']
KW_NOISE = ['羊毛', '白嫖', '免费', '限免', '薅', 'token', '招聘', '显卡',
            'dsh', 'agnes', '码力', 'hy4', 'step 5']

TAG = re.compile(r'<[^>]+>')


def plain(html):
    if not html:
        return ''
    s = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    s = re.sub(r'</(p|div|li|tr|h[1-6])>', '\n', s, flags=re.I)
    s = TAG.sub('', s)
    for a, b in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                 ('&quot;', '"'), ('&#39;', "'")]:
        s = s.replace(a, b)
    return re.sub(r'\n{3,}', '\n\n', s).strip()


def hits(t, kws):
    low = t.lower()
    return [k for k in kws if k in low]


recent = [x for x in all_posts if x['created_at'][:10] >= CUT15]
log('1.5 年内:', len(recent))

tagged = []
for x in recent:
    body = plain(x.get('details', ''))
    blob = (x.get('title') or '') + '\n' + body
    strong = hits(blob, KW_STRONG)
    weak = hits(blob, KW_WEAK)
    noise = hits(blob, KW_NOISE)
    if strong or len(weak) >= 2:
        vf_keys = {'vf', 'value factor', '价值因子', 'base payment', 'osmosis', 'pyramid',
                   '金字塔', 'atom', 'correlation', '相关性', 'combined', 'combine',
                   'isscore', 'base', '分成', '美元', '刀', 'pay'}
        if len(set(strong) & vf_keys) >= 2 or 'vf' in strong or 'value factor' in strong:
            rel = 'vf'
        elif noise and not (set(strong) & vf_keys):
            rel = 'noise'
        else:
            rel = 'alpha'
    else:
        rel = 'drop'
    tagged.append({'id': x['id'], 'title': x.get('title'), 'created_at': x['created_at'],
                   'votes': x.get('votes'), 'comments': x.get('comments'),
                   'author': x.get('author') or '', 'url': x.get('url'),
                   'dlen': len(body), 'rel': rel, 'strong': strong,
                   'weak_n': len(weak), 'noise': noise, 'body': body})

c = Counter(t['rel'] for t in tagged)
log('分类:', dict(c))
keep = [t for t in tagged if t['rel'] in ('vf', 'alpha')]
log('保留:', len(keep), '| 其中近1年:', sum(1 for t in keep if t['created_at'][:10] >= CUT1Y))

json.dump({'keep': keep, 'tagged': tagged},
          open(os.path.join(LGDIR, 'forum_filtered.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

log('')
log('=========== VF 类（%d 条，按时间倒序）===========' % sum(1 for t in keep if t['rel'] == 'vf'))
for t in sorted([x for x in keep if x['rel'] == 'vf'], key=lambda y: y['created_at'], reverse=True):
    log('%s | %s | v%-3s c%-3s | %s' % (t['created_at'][:10], t['id'], t['votes'],
                                        t['comments'], (t['title'] or '')[:62]))

# ---------- 超链接 ----------
log('')
log('=========== 超链接宿主分布（1.5 年内全部帖子）===========')
host_cnt = Counter()
post_links = {}
for x in recent:
    hrefs = re.findall(r'href="([^"]+)"', x.get('details') or '', flags=re.I)
    hrefs = [h for h in hrefs if not h.startswith('#')]
    if not hrefs:
        continue
    post_links[x['id']] = hrefs
    for h in hrefs:
        host_cnt[urlparse(h).netloc or 'RELATIVE'] += 1
for host, cnt in host_cnt.most_common(40):
    log('  %-48s %d' % (host, cnt))
log('  含链接的帖子数:', len(post_links), '| 链接总数:', sum(host_cnt.values()))

json.dump(post_links, open(os.path.join(LGDIR, 'forum_links_raw.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
logf.close()
