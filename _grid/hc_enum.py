# -*- coding: utf-8 -*-
"""枚举帮助中心「顾问付款」相关章节的全部文章，并抓正文"""
import json
import os
import subprocess
import time

import requests
from websocket import create_connection

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
LGDIR = r'D:\Python\worldquant\_logs'
OUTDIR = os.path.join(LGDIR, 'link_docs')
os.makedirs(OUTDIR, exist_ok=True)

SEEDS = [
    'https://support.worldquantbrain.com/hc/en-us/articles/4672184130455',
    'https://support.worldquantbrain.com/hc/en-us/articles/6314645381655',
    'https://support.worldquantbrain.com/hc/en-us/articles/4702810979351',
    'https://support.worldquantbrain.com/hc/en-us/articles/6675128127511',
]

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     SEEDS[0]], stdout=err, stderr=err, close_fds=True)

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


logf = open(os.path.join(LGDIR, 'hc_enum.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


LINK_JS = r"""
(() => {
  const out = [];
  document.querySelectorAll('a[href*="/articles/"]').forEach(a=>{
    out.push({href:a.href, text:(a.innerText||'').trim().slice(0,90)});
  });
  return JSON.stringify(out);
})()
"""

time.sleep(3)
found = {}
for seed in SEEDS:
    cdp('Page.navigate', {'url': seed})
    for _ in range(20):
        time.sleep(1.2)
        if ev("document.readyState", to=8000) == 'complete':
            break
    time.sleep(1.5)
    raw = ev(LINK_JS)
    if isinstance(raw, str) and raw.startswith('['):
        for it in json.loads(raw):
            h = it['href'].split('?')[0]
            found.setdefault(h, it['text'])
    log('seed %s -> 累计 %d 篇' % (seed.rsplit('/', 1)[-1], len(found)))

log('')
log('===== 帮助中心文章清单 =====')
for h, t in sorted(found.items(), key=lambda kv: kv[1]):
    log('  %-72s %s' % (h.replace('https://support.worldquantbrain.com', ''), t))

json.dump(found, open(os.path.join(LGDIR, 'hc_articles.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
