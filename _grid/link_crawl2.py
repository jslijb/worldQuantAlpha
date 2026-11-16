# -*- coding: utf-8 -*-
"""v2：先过 Cookie 同意，再抓 learn 文档；API 直接导航读 JSON"""
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
OUTDIR = os.path.join(LGDIR, 'link_docs')
os.makedirs(OUTDIR, exist_ok=True)

P = 'https://platform.worldquantbrain.com/learn/documentation'
DOCS = [
    ('learn_atom',              '%s/consultant-information/single-dataset-alphas' % P),
    ('learn_osmosis',           '%s/consultant-information/osmosis-allocation-guide-consultants' % P),
    ('learn_themes',            '%s/themes/overview-themes' % P),
    ('learn_consultant_read1',  '%s/consultant-information/getting-started-finding-consultant-alphas-read-first' % P),
    ('learn_consultant_feat',   '%s/consultant-information/consultant-features' % P),
    ('learn_consultant_tests',  '%s/consultant-information/consultant-submission-tests' % P),
    ('learn_powerpool',         '%s/consultant-information/getting-started-power-pool-alphas' % P),
    ('learn_sa_overview',       '%s/superalpha/superalpha-overview' % P),
    ('learn_sa_selection',      '%s/superalpha/selection-expression' % P),
]
APIS = [
    ('api_base_payment', 'https://api.worldquantbrain.com/users/self/activities/base-payment'),
    ('api_consultant', 'https://api.worldquantbrain.com/users/self/consultant'),
    ('api_pyramid', 'https://api.worldquantbrain.com/users/self/activities/pyramid-multiplier'),
]

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     'https://platform.worldquantbrain.com/learn'], stdout=err, stderr=err, close_fds=True)

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


def cdp(method, params=None):
    n[0] += 1
    k = n[0]
    ws.send(json.dumps({'id': k, 'method': method, 'params': params or {}}))
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


logf = open(os.path.join(LGDIR, 'link_crawl2.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


CLEAN_JS = r"""
(() => {
  const kill = ['header','nav','footer','script','style','noscript',
                '[class*=cookie]','[class*=Cookie]','[class*=consent]','[class*=Consent]',
                '[id*=onetrust]','[class*=banner]','[class*=breadcrumb]','[class*=Breadcrumb]'];
  const c = document.body.cloneNode(true);
  kill.forEach(s => { try{ c.querySelectorAll(s).forEach(e=>e.remove()); }catch(e){} });
  let t = c.innerText || '';
  t = t.replace(/[ \t]+/g,' ').replace(/\n{3,}/g,'\n\n').trim();
  return t;
})()
"""

ACCEPT_JS = r"""
(() => {
  const kws = ['接受','同意','允许全部','全部接受','Accept All','Accept all','I Accept',
               'ACCEPT ALL','Accept Cookies','同意全部','接受全部'];
  let clicked = [];
  // OneTrust 常见 id
  for (const sel of ['#onetrust-accept-btn-handler','button#onetrust-accept-btn-handler',
                     '[data-testid=accept-all]','[aria-label*=Accept]','[aria-label*=接受]']) {
    const el = document.querySelector(sel);
    if (el) { el.click(); clicked.push(sel); }
  }
  document.querySelectorAll('button,a,div[role=button]').forEach(el=>{
    const t=(el.innerText||'').trim();
    if (t && t.length < 24 && kws.some(k=>t===k||t.includes(k))) { el.click(); clicked.push(t); }
  });
  return clicked.join('|');
})()
"""

time.sleep(4)
log('cookie 点击:', ev(ACCEPT_JS))
time.sleep(2)

results = {}
for slug, url in DOCS:
    cdp('Page.navigate', {'url': url})
    txt = ''
    for attempt in range(25):
        time.sleep(1.2)
        st = ev("document.readyState", to=10000)
        if st == 'complete':
            time.sleep(1.0)
            txt = ev(CLEAN_JS, to=30000)
            if isinstance(txt, str) and len(txt) > 700 and '自定义同意偏好' not in txt[:80]:
                break
            if isinstance(txt, str) and '自定义同意偏好' in txt[:200]:
                ev(ACCEPT_JS)
                time.sleep(1.5)
                txt = ev(CLEAN_JS, to=30000)
                if isinstance(txt, str) and len(txt) > 700:
                    break
    if not isinstance(txt, str):
        txt = str(txt)
    cur = ev("location.href", to=10000)
    with open(os.path.join(OUTDIR, slug + '.txt'), 'w', encoding='utf-8') as f:
        f.write('URL: %s\nFINAL: %s\nLEN: %d\n\n%s' % (url, cur, len(txt), txt))
    results[slug] = {'url': url, 'final': cur, 'len': len(txt)}
    log('%-24s len=%-6d %s' % (slug, len(txt), txt[:80].replace('\n', ' ') if txt else ''))

# ---- API：直接导航 ----
for slug, url in APIS:
    cdp('Page.navigate', {'url': url})
    txt = ''
    for _ in range(20):
        time.sleep(1.0)
        txt = ev("document.body ? document.body.innerText : ''", to=20000)
        if isinstance(txt, str) and len(txt) > 30:
            break
    if not isinstance(txt, str):
        txt = str(txt)
    with open(os.path.join(OUTDIR, slug + '.txt'), 'w', encoding='utf-8') as f:
        f.write('URL: %s\nLEN: %d\n\n%s' % (url, len(txt), txt[:30000]))
    results[slug] = {'url': url, 'len': len(txt)}
    log('%-24s len=%-6d %s' % (slug, len(txt), txt[:120].replace('\n', ' ')))

json.dump(results, open(os.path.join(LGDIR, 'link_crawl_index2.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
