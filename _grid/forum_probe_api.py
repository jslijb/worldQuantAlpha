# -*- coding: utf-8 -*-
"""探测 Zendesk 社区 API：单帖 / 批量 ids"""
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
LGDIR = r'D:\Python\worldquant\_logs'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     '%s/hc/zh-cn' % ORIGIN], stdout=err, stderr=err, close_fds=True)

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
ws = create_connection(ws_url, timeout=120, max_size=None)
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
print('ready:', st)

IDS = ['43589077012759', '41021984423063', '40520794084119']

tests = {
    'single': "%s/api/v2/community/posts/43589077012759.json" % ORIGIN,
    'bulk_ids': "%s/api/v2/community/posts.json?ids=%s" % (ORIGIN, ','.join(IDS)),
    'bulk_ids_100': "%s/api/v2/community/posts.json?per_page=100&ids=%s" % (ORIGIN, ','.join(IDS)),
    'help_center_single': "%s/api/v2/help_center/community/posts/43589077012759.json" % ORIGIN,
}

for name, u in tests.items():
    expr = """(async()=>{
      try{
        const r = await fetch('%s', {credentials:'include', headers:{'Accept':'application/json'}});
        const t = await r.text();
        return r.status + '|' + t.slice(0,220);
      }catch(e){ return 'ERR:'+e.message; }
    })()""" % u
    print('---', name)
    print(str(ev(expr))[:400])

# 顺手看看帖子所属 topic 分布
print('--- topic of one post')
print(ev("""(async()=>{
  const r = await fetch('%s/api/v2/community/posts/43589077012759.json', {credentials:'include'});
  if(!r.ok) return 'HTTP'+r.status;
  const j = await r.json();
  return JSON.stringify({topic_id:j.post.topic_id, title:j.post.title, created:j.post.created_at,
    dlen:(j.post.details||'').length, topic:(j.post.topic||{}).name});
})()""" % ORIGIN))

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
