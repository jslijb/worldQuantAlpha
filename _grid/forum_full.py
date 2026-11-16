# -*- coding: utf-8 -*-
"""CDP 抓全量帖子（含正文 details）-> 过滤 VF/Alpha + 1.5 年内 -> 抽超链接"""
import json
import os
import re
import subprocess
import time
from urllib.parse import urlparse

import requests
from websocket import create_connection

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
ORIGIN = 'https://support.worldquantbrain.com'
TOPIC = '18910956638743'
LGDIR = r'D:\Python\worldquant\_logs'
OUT = os.path.join(LGDIR, 'forum_posts_full.json')
LOG = os.path.join(LGDIR, 'forum_full.log')

logf = open(LOG, 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     '%s/hc/zh-cn/community/topics/%s' % (ORIGIN, TOPIC)],
    stdout=err, stderr=err, close_fds=True)

ws_url = None
for _ in range(80):
    try:
        for t in S.get('http://127.0.0.1:%d/json/list' % PORT, timeout=3).json():
            if t.get('type') == 'page' and 'support.worldquantbrain.com' in (t.get('url') or ''):
                ws_url = t.get('webSocketDebuggerUrl')
                break
        if ws_url:
            break
    except Exception:
        pass
    time.sleep(0.5)
if not ws_url:
    log('未拿到 page target')
    p.terminate()
    raise SystemExit(1)
log('PAGE CDP OK')

ws = create_connection(ws_url, timeout=180, max_size=None)
n = [0]


def ev(expr, to=120000):
    n[0] += 1
    k = n[0]
    ws.send(json.dumps({'id': k, 'method': 'Runtime.evaluate',
                        'params': {'expression': expr, 'awaitPromise': True,
                                   'returnByValue': True, 'timeout': to}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == k:
            res = r.get('result', {})
            if 'exceptionDetails' in res:
                return 'EXC:' + str(res['exceptionDetails'])[:300]
            return res.get('result', {}).get('value')


t0 = time.time()
while time.time() - t0 < 90:
    st = ev("document.readyState + '|' + location.origin", to=15000)
    if isinstance(st, str) and st.startswith('complete|' + ORIGIN):
        break
    time.sleep(1.5)
log('ready:', st)

all_posts = []
page = 1
while page <= 40:
    expr = """(async()=>{
      const out=[];
      const r = await fetch('%s/api/v2/community/topics/%s/posts.json?per_page=100&page=%d',
        {credentials:'include', headers:{'Accept':'application/json'}});
      if(!r.ok) return 'HTTP'+r.status;
      const j = await r.json();
      for(const p of (j.posts||[])) out.push({id:p.id,title:p.title,created_at:p.created_at,
        updated_at:p.updated_at,votes:p.vote_sum,comments:p.comment_count,
        author:(p.author||{}).name,url:p.html_url,details:p.details||''});
      return JSON.stringify({count:j.count,next:j.next_page,n:out.length,posts:out});
    })()""" % (ORIGIN, TOPIC, page)
    raw = ev(expr)
    if not isinstance(raw, str) or raw.startswith('EXC:') or raw.startswith('HTTP'):
        log('page %d 失败: %s' % (page, str(raw)[:300]))
        break
    d = json.loads(raw)
    got = d.get('posts', [])
    log('page %d: %d 帖' % (page, len(got)))
    if not got:
        break
    all_posts.extend(got)
    if not d.get('next'):
        break
    page += 1
    time.sleep(0.3)

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass

log('抓取总数:', len(all_posts))
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, ensure_ascii=False)

# ---------- 过滤 ----------
CUT15 = '2025-05-15'
CUT1Y = '2025-11-15'

KW_STRONG = ['vf', 'value factor', '价值因子', 'base payment', 'base', 'osmosis',
             'pyramid', '金字塔', 'atom', 'correlation', '相关性', 'combined',
             'combine', 'isScore', 'is score', 'pay', '收入', '收益', '美元', '刀',
             'submission', '提交', 'sharpe', 'fitness', 'turnover', '换手']
# 弱相关（Alpha 研究法/模板/idea）也收，但打标区分
KW_WEAK = ['alpha', '阿尔法', '表达式', '模板', 'template', 'idea', '数据集', 'dataset',
           '算子', 'operator', '回测', 'simulat', 'universe', 'neutral', 'decay',
           'truncation', 'bucket', 'group_', 'ts_', 'rank', 'signal', '因子']

# 明确无关（工具/羊毛/招聘/比赛公告等）
KW_NOISE = ['羊毛', '白嫖', 'token', '免费', '招聘', '模型免费', '薅', 'dsh',
            'step 5', 'hy4', 'agnes', '码力', '限免', '关税', '显卡']

HTML_TAG = re.compile(r'<[^>]+>')


def plain(html):
    if not html:
        return ''
    s = re.sub(r'<br\s*/?>', '\n', html, flags=re.I)
    s = re.sub(r'</(p|div|li|tr|h[1-6])>', '\n', s, flags=re.I)
    s = HTML_TAG.sub('', s)
    s = (s.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<')
          .replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'"))
    return re.sub(r'\n{3,}', '\n\n', s).strip()


def hits(text, kws):
    low = text.lower()
    return [k for k in kws if k in low]


recent = [x for x in all_posts if x['created_at'][:10] >= CUT15]
log('1.5 年内:', len(recent))

tagged = []
for x in recent:
    body = plain(x.get('details', ''))
    blob = (x['title'] or '') + '\n' + body
    strong = hits(blob, KW_STRONG)
    weak = hits(blob, KW_WEAK)
    noise = hits(blob, KW_NOISE)
    # 相关性判据：命 strong>=1，或 weak>=2；同时非纯 noise
    if strong or len(weak) >= 2:
        if noise and not strong:
            rel = 'noise'
        elif len(strong) >= 2 or ('vf' in strong) or ('value factor' in strong) or ('base' in strong):
            rel = 'vf'
        else:
            rel = 'alpha'
    else:
        rel = 'drop'
    tagged.append({'id': x['id'], 'title': x['title'], 'created_at': x['created_at'],
                   'votes': x['votes'], 'comments': x['comments'],
                   'author': x['author'], 'url': x['url'],
                   'dlen': len(body), 'rel': rel,
                   'strong': strong, 'weak_n': len(weak), 'noise': noise})

from collections import Counter
c = Counter(t['rel'] for t in tagged)
log('分类:', dict(c))
log('  vf    = VF/收益相关')
log('  alpha = Alpha 研究法/模板/idea')
log('  noise = 疑似羊毛工具帖(丢弃)')
log('  drop  = 无关键词(丢弃)')

keep = [t for t in tagged if t['rel'] in ('vf', 'alpha')]
log('保留:', len(keep), '（其中近1年 %d）' % sum(1 for t in keep if t['created_at'][:10] >= CUT1Y))

with open(os.path.join(LGDIR, 'forum_filtered.json'), 'w', encoding='utf-8') as f:
    json.dump({'keep': keep, 'tagged': tagged}, f, ensure_ascii=False, indent=1)

log('--- VF 类（按时间倒序）---')
for t in sorted([x for x in keep if x['rel'] == 'vf'], key=lambda y: y['created_at'], reverse=True):
    log('%s | %s | v=%s c=%s | %s' % (t['created_at'][:10], t['id'], t['votes'],
                                      t['comments'], (t['title'] or '')[:64]))

log('--- 超链接统计 ---')
link_cnt = Counter()
titles_by_host = {}
post_links = {}
for x in all_posts:
    if x['created_at'][:10] < CUT15:
        continue
    hrefs = re.findall(r'href="([^"]+)"', x.get('details') or '', flags=re.I)
    if not hrefs:
        continue
    post_links[x['id']] = hrefs
    for h in hrefs:
        host = urlparse(h).netloc or 'RELATIVE'
        link_cnt[host] += 1
for host, cnt in link_cnt.most_common(30):
    log('  %-45s %d' % (host, cnt))

with open(os.path.join(LGDIR, 'forum_links_raw.json'), 'w', encoding='utf-8') as f:
    json.dump(post_links, f, ensure_ascii=False, indent=1)

logf.close()
