# -*- coding: utf-8 -*-
"""重试渲染失败的文章 + 帮助中心搜索 API"""
import json
import os
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

RETRY = ['6161120218775', '4418494822423', '4672184130455', '6161094877079',
         '6161075815831', '6161074001047', '6275703648279', '6314580852119',
         '6314645381655', '25960264611351', '11378503211671', '11592165617303']

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


logf = open(os.path.join(LGDIR, 'hc_retry.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


WAIT_JS = r"""
(() => {
  const sels = ['.article-body','article','main','.article'];
  let best = 0;
  for (const s of sels) {
    const el = document.querySelector(s);
    if (el) best = Math.max(best, (el.innerText||'').trim().length);
  }
  return best + '|' + document.readyState;
})()
"""

GET_JS = r"""
(() => {
  const sels = ['.article-body','article','main','.article','body'];
  let el = null;
  for (const s of sels) { const e=document.querySelector(s); if(e && (e.innerText||'').trim().length>60){el=e;break;} }
  if (!el) el = document.body;
  const c = el.cloneNode(true);
  ['script','style','noscript','svg','[class*=related]','[class*=vote]',
   '[class*=comment]','[class*=breadcrumb]','[class*=recent]'].forEach(s=>{
    try{c.querySelectorAll(s).forEach(e=>e.remove());}catch(e){}
  });
  let t = c.innerText || '';
  return t.replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
})()
"""

for aid in RETRY:
    url = '%s/hc/en-us/articles/%s' % (BASE, aid)
    cdp('Page.navigate', {'url': url})
    best = 0
    txt = ''
    for i in range(22):
        time.sleep(1.2)
        st = ev(WAIT_JS, to=10000)
        try:
            L = int(str(st).split('|')[0])
        except Exception:
            L = 0
        if L > 120:
            txt = ev(GET_JS, to=25000)
            if isinstance(txt, str) and len(txt) > 120:
                best = len(txt)
                break
    if not isinstance(txt, str):
        txt = ''
    fn = os.path.join(OUTDIR, 'hc_%s.txt' % aid)
    if best > 120:
        with open(fn, 'w', encoding='utf-8') as f:
            f.write('ID: %s\nURL: %s\nLEN: %d\n\n%s' % (aid, url, len(txt), txt))
    log('%-18s len=%-5d %s' % (aid, len(txt), txt[:70].replace('\n', ' ')))

# ---- 帮助中心搜索 API ----
log('')
log('===== 搜索 API：Value Factor =====')
cdp('Page.navigate', {'url': '%s/hc/en-us' % BASE})
time.sleep(2)
for q in ['Value Factor', 'base payment', 'pyramid multiplier', 'quarterly payment']:
    raw = ev("""(async()=>{
      try{
        const r = await fetch('%s/api/v2/help_center/articles/search.json?query=%s&per_page=30',
          {credentials:'include'});
        if(!r.ok) return 'HTTP'+r.status;
        const j = await r.json();
        return JSON.stringify((j.results||[]).map(a=>({id:a.id,title:a.title,url:a.html_url})));
      }catch(e){ return 'ERR:'+e.message; }
    })()""" % (BASE, q.replace(' ', '%20')))
    log('--- %s' % q)
    try:
        for it in json.loads(raw):
            log('  %s | %s' % (it['id'], it['title'][:70]))
            log('       %s' % it['url'])
    except Exception:
        log('  ' + str(raw)[:300])

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
