# -*- coding: utf-8 -*-
"""第三批：VF 定义/生成条件/排行榜/Combined/Theme/Pyramid/Osmosis 官方原文"""
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

IDS = [
    ('11591947651607', 'What is the Value Factor?'),
    ('14673192879511', 'Does number of alpha submissions per month impact value factor?'),
    ('44561175314199', "What is required for a consultant's Value Factor to be generated?"),
    ('11377632861335', 'How is the consultant leaderboard calculated?'),
    ('29061097819287', 'How to get a higher quarterly payment within Genius level range'),
    ('37443828624279', 'How do Power Pool Alphas affect compensation?'),
    ('26715994416535', 'What is Combined Alpha Performance?'),
    ('6314632610199', 'How can I do well in Themes?'),
    ('26716012806295', 'What are pyramids?'),
    ('36966491408535', 'Factors to consider while assigning Osmosis points'),
    ('6314632610199b', 'dup'),
    ('4902349883927', 'Terms and definitions'),
]
IDS = [(a, b) for a, b in IDS if not a.endswith('b') and b != 'dup']

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


logf = open(os.path.join(LGDIR, 'hc_crawl3.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


WAIT_JS = r"""
(() => {
  const sels=['.article-body','article','main','.article'];
  let best=0;
  for(const s of sels){const el=document.querySelector(s); if(el) best=Math.max(best,(el.innerText||'').trim().length);}
  return best + '|' + document.readyState;
})()
"""

GET_JS = r"""
(() => {
  const sels=['.article-body','article','main','.article','body'];
  let el=null;
  for(const s of sels){const e=document.querySelector(s); if(e&&(e.innerText||'').trim().length>60){el=e;break;}}
  if(!el) el=document.body;
  const c=el.cloneNode(true);
  ['script','style','noscript','svg','[class*=related]','[class*=vote]','[class*=comment]',
   '[class*=breadcrumb]','[class*=recent]'].forEach(s=>{try{c.querySelectorAll(s).forEach(e=>e.remove());}catch(e){}});
  let t=c.innerText||'';
  return t.replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
})()
"""

for aid, title in IDS:
    url = '%s/hc/en-us/articles/%s' % (BASE, aid)
    cdp('Page.navigate', {'url': url})
    txt = ''
    for _ in range(22):
        time.sleep(1.2)
        st = ev(WAIT_JS, to=10000)
        try:
            L = int(str(st).split('|')[0])
        except Exception:
            L = 0
        if L > 120:
            txt = ev(GET_JS, to=25000)
            if isinstance(txt, str) and len(txt) > 120:
                break
    if not isinstance(txt, str):
        txt = ''
    with open(os.path.join(OUTDIR, 'hc_%s.txt' % aid), 'w', encoding='utf-8') as f:
        f.write('ID: %s\nTITLE: %s\nURL: %s\nLEN: %d\n\n%s' % (aid, title, url, len(txt), txt))
    log('%-18s len=%-5d %s' % (aid, len(txt), title[:58]))

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
