# -*- coding: utf-8 -*-
"""抓帮助中心 34 篇顾问付款/VF/金字塔官方文章 + 搜索「What is the Value Factor」"""
import json
import os
import re
import subprocess
import time

import requests
from websocket import create_connection

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
BASE = 'https://support.worldquantbrain.com'
LGDIR = r'D:\Python\worldquant\_logs'
OUTDIR = os.path.join(LGDIR, 'link_docs')
os.makedirs(OUTDIR, exist_ok=True)

arts = json.load(open(os.path.join(LGDIR, 'hc_articles.json'), encoding='utf-8'))
# 只抓 VF/付款/金字塔/Sharpe 相关，排除付款日期、本人不涉及
SKIP = ['Payment-dates', 'invoice', 'Region-Themes-as-well']
TARGETS = []
for path, title in arts.items():
    if any(s.lower() in path.lower() for s in SKIP):
        continue
    aid = re.search(r'/articles/(\d+)', path)
    if not aid:
        continue
    TARGETS.append((aid.group(1), path, title))
TARGETS.sort()
print('待抓:', len(TARGETS))

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     '%s/hc/en-us' % BASE], stdout=err, stderr=err, close_fds=True)

ws_url = None
for _ in range(80):
    try:
        for t in S.get('http://127.0.0.1:%d/json/list' % PORT, timeout=3).json():
            if t.get('type') == 'page' and 'worldquantbrain' in (t.get('url') or ''):
                ws_url = t.get('webSocketDebuggerUrl')
                break
        if ws_url:
            break
    except Exception:
        pass
    time.sleep(0.5)
ws = create_connection(ws_url, timeout=180, max_size=None)
n = [0]


def cdp(m, params=None):
    n[0] += 1
    k = n[0]
    ws.send(json.dumps({'id': k, 'method': m, 'params': params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get('id') == k:
            return r


def ev(expr, to=90000):
    r = cdp('Runtime.evaluate', {'expression': expr, 'awaitPromise': True,
                                 'returnByValue': True, 'timeout': to})
    res = r.get('result', {})
    if 'exceptionDetails' in res:
        return 'EXC:' + str(res['exceptionDetails'])[:250]
    return res.get('result', {}).get('value')


logf = open(os.path.join(LGDIR, 'hc_crawl.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


BODY_JS = r"""
(() => {
  const sec = document.querySelector('article') || document.querySelector('main') ||
              document.querySelector('.article-body') || document.body;
  const c = sec.cloneNode(true);
  ['header','nav','footer','script','style','noscript','[class*=related]',
   '[class*=Related]','[class*=vote]','[class*=comment]','[class*=breadcrumb]',
   '[class*=sidebar]','[class*=search]','svg'].forEach(s=>{
    try{ c.querySelectorAll(s).forEach(e=>e.remove()); }catch(e){}
  });
  let t = c.innerText || '';
  t = t.replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
  return t;
})()
"""

ok = 0
for aid, path, title in TARGETS:
    url = path if path.startswith('http') else BASE + path
    cdp('Page.navigate', {'url': url})
    txt = ''
    for _ in range(15):
        time.sleep(1.0)
        if ev("document.readyState", to=8000) != 'complete':
            continue
        time.sleep(0.6)
        txt = ev(BODY_JS, to=25000)
        if isinstance(txt, str) and len(txt) > 150:
            break
    if not isinstance(txt, str):
        txt = str(txt)
    fn = os.path.join(OUTDIR, 'hc_%s.txt' % aid)
    with open(fn, 'w', encoding='utf-8') as f:
        f.write('ID: %s\nTITLE: %s\nURL: %s\nLEN: %d\n\n%s' % (aid, title, url, len(txt), txt))
    if len(txt) > 150:
        ok += 1
    log('%-18s len=%-5d %s' % (aid, len(txt), title[:56]))

log('成功 %d / %d' % (ok, len(TARGETS)))

# 搜索「What is the Value Factor」
cdp("Page.navigate", {"url": BASE + "/hc/en-us/search?query=Value%20Factor"})
time.sleep(4)
raw = ev("""(() => {const o=[];document.querySelectorAll('a[href*="/articles/"]').forEach(a=>
  o.push(a.innerText.trim().slice(0,80)+' :: '+a.href.split('?')[0]));return JSON.stringify([...new Set(o)]);})()""")
log('')
log('搜索 Value Factor 结果:')
try:
    for it in json.loads(raw)[:25]:
        log('  ' + it)
except Exception:
    log(str(raw)[:500])

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
