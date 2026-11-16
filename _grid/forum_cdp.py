# -*- coding: utf-8 -*-
"""CDP( page 端点 ) 抓 support.worldquantbrain.com 顾问中文论坛帖子列表
单条命令内完成 启动 -> 抓取 -> 落盘 -> 终止
"""
import json
import os
import subprocess
import time

import requests
from websocket import create_connection

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
ORIGIN = 'https://support.worldquantbrain.com'
TOPIC = '18910956638743'
LGDIR = r'D:\Python\worldquant\_logs'
OUT = os.path.join(LGDIR, 'forum_list_raw.json')
LOG = os.path.join(LGDIR, 'forum_cdp.log')

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

# 等 CDP + page target
ws_url = None
for _ in range(80):
    try:
        lst = S.get('http://127.0.0.1:%d/json/list' % PORT, timeout=3).json()
        for t in lst:
            if t.get('type') == 'page' and 'support.worldquantbrain.com' in (t.get('url') or ''):
                ws_url = t.get('webSocketDebuggerUrl')
                break
        if ws_url:
            break
    except Exception:
        pass
    time.sleep(0.5)

if not ws_url:
    log('未拿到 page target，退出')
    p.terminate()
    raise SystemExit(1)
log('PAGE CDP OK', ws_url)

ws = create_connection(ws_url, timeout=120, max_size=None, origin='http://127.0.0.1')
n = [0]


def ev(expr, to=90000):
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


# 等页面就绪
t0 = time.time()
st = None
while time.time() - t0 < 90:
    st = ev("document.readyState + '|' + location.origin", to=15000)
    if isinstance(st, str) and st.startswith('complete|' + ORIGIN):
        break
    time.sleep(1.5)
log('ready:', st)

title = ev("document.title")
h1 = ev("(document.querySelector('h1')||{}).innerText || '-'")
log('title:', title)
log('h1:', h1)

who = ev("""(async()=>{
  try{
    const r = await fetch('/api/v2/users/me.json', {credentials:'include'});
    if(!r.ok) return 'HTTP'+r.status;
    const j = await r.json();
    return JSON.stringify({name:(j.user||{}).name, id:(j.user||{}).id});
  }catch(e){ return 'ERR:'+e.message; }
})()""")
log('me:', who)

# 翻页
all_posts = []
page = 1
while page <= 40:
    expr = """(async()=>{
      const r = await fetch('%s/api/v2/community/topics/%s/posts.json?per_page=100&page=%d',
        {credentials:'include', headers:{'Accept':'application/json'}});
      if(!r.ok) return 'HTTP'+r.status;
      const j = await r.json();
      return JSON.stringify({n:(j.posts||[]).length, count:j.count, next:j.next_page,
        posts:(j.posts||[]).map(p=>({id:p.id, title:p.title, created_at:p.created_at,
          updated_at:p.updated_at, votes:p.vote_sum, comments:p.comment_count,
          author:(p.author||{}).name, url:p.html_url, dlen:(p.details||'').length}))});
    })()""" % (ORIGIN, TOPIC, page)
    raw = ev(expr)
    if not isinstance(raw, str) or raw.startswith('EXC:') or raw.startswith('HTTP'):
        log('page %d 失败: %s' % (page, str(raw)[:300]))
        break
    d = json.loads(raw)
    got = d.get('posts', [])
    log('page %d: got=%d count=%s next=%s' % (page, d.get('n', 0), d.get('count'), d.get('next')))
    if not got:
        break
    all_posts.extend(got)
    if not d.get('next'):
        break
    page += 1
    time.sleep(0.3)

log('总帖子数:', len(all_posts))
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(all_posts, f, ensure_ascii=False, indent=1)

if all_posts:
    ds = sorted(x['created_at'] for x in all_posts)
    log('最早:', ds[0], '最新:', ds[-1])
    c1, c15 = '2025-11-15', '2025-05-15'
    a = sum(1 for x in ds if x[:10] >= c1)
    b = sum(1 for x in ds if c15 <= x[:10] < c1)
    log('★1年内 %d | ·1~1.5年 %d | >1.5年 %d' % (a, b, len(ds) - a - b))
    # 打印 1.5 年内标题清单
    log('--- 1.5 年内帖子清单 ---')
    for x in sorted(all_posts, key=lambda y: y['created_at'], reverse=True):
        if x['created_at'][:10] >= c15:
            log('%s | %s | c=%s v=%s | %s' % (x['created_at'][:16], x['id'],
                                              x.get('comments'), x.get('votes'),
                                              (x['title'] or '')[:70]))

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
