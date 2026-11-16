# -*- coding: utf-8 -*-
"""CDP 打开帖子里的超链接，抓正文；判是否与 Alpha/VF 相关"""
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
ORIGIN = 'https://support.worldquantbrain.com'
LGDIR = r'D:\Python\worldquant\_logs'
OUTDIR = os.path.join(LGDIR, 'link_docs')
os.makedirs(OUTDIR, exist_ok=True)

P = 'https://platform.worldquantbrain.com/learn/documentation'
A = 'https://support.worldquantbrain.com/hc/en-us/articles'

DOCS = [
    # --- 官方 Learn 文档 ---
    ('learn_atom',              '%s/consultant-information/single-dataset-alphas' % P),
    ('learn_osmosis',           '%s/consultant-information/osmosis-allocation-guide-consultants' % P),
    ('learn_themes',            '%s/themes/overview-themes' % P),
    ('learn_consultant_read1',  '%s/consultant-information/getting-started-finding-consultant-alphas-read-first' % P),
    ('learn_consultant_feat',   '%s/consultant-information/consultant-features' % P),
    ('learn_consultant_tests',  '%s/consultant-information/consultant-submission-tests' % P),
    ('learn_powerpool',         '%s/consultant-information/getting-started-power-pool-alphas' % P),
    ('learn_sa_overview',       '%s/superalpha/superalpha-overview' % P),
    ('learn_sa_selection',      '%s/superalpha/selection-expression' % P),
    # --- 官方帮助中心文章（论坛里被引的 VF/收入口径）---
    ('hc_theme_base',           '%s/6314645381655' % A),
    ('hc_more_base',            '%s/4672184130455' % A),
    ('hc_quarterly',            '%s/4702810979351' % A),
    ('hc_official_qa',          '%s/6675128127511' % A),
    ('hc_theme_nochange',       '%s/6314580852119' % A),
    ('hc_subuniverse_sharpe',   '%s/6568644868375' % A),
    ('hc_weight_concentration', '%s/19248385997719' % A),
    ('hc_aftercost_sharpe',     '%s/25960264611351' % A),
    ('hc_2y_sharpe',            '%s/20251383456663' % A),
    ('hc_genius_activity',      '%s/31743652246551' % A),
]

APIS = [
    ('api_base_payment', 'https://api.worldquantbrain.com/users/self/activities/base-payment'),
    ('api_consultant', 'https://api.worldquantbrain.com/users/self/consultant'),
    ('api_consultant_summary', 'https://api.worldquantbrain.com/users/self/consultant/summary'),
]

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


def cdp(method, params=None, to=60000):
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


logf = open(os.path.join(LGDIR, 'link_crawl.log'), 'w', encoding='utf-8')


def log(*a):
    s = ' '.join(str(x) for x in a)
    print(s)
    logf.write(s + '\n')
    logf.flush()


# strip 导航噪音
CLEAN_JS = r"""
(() => {
  const kill = ['header','nav','footer','script','style','noscript',
                '[class*=cookie]','[class*=Cookie]','[class*=banner]','[class*=Breadcrumb]'];
  const c = document.body.cloneNode(true);
  kill.forEach(s => c.querySelectorAll(s).forEach(e => e.remove()));
  let t = c.innerText || '';
  t = t.replace(/[ \t]+/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
  return t;
})()
"""

results = {}
# ---------- 官方文档：导航后取 innerText ----------
for slug, url in DOCS:
    try:
        cdp('Page.navigate', {'url': url})
    except Exception as e:
        log(slug, 'navigate 失败', e)
        continue
    txt = ''
    for _ in range(30):
        time.sleep(1.2)
        st = ev("document.readyState", to=10000)
        if st == 'complete':
            time.sleep(1.2)
            txt = ev(CLEAN_JS, to=30000)
            if isinstance(txt, str) and len(txt) > 200:
                break
    if not isinstance(txt, str):
        txt = str(txt)
    cur = ev("location.href", to=10000)
    with open(os.path.join(OUTDIR, slug + '.txt'), 'w', encoding='utf-8') as f:
        f.write('URL: %s\nFINAL: %s\nLEN: %d\n\n%s' % (url, cur, len(txt), txt))
    results[slug] = {'url': url, 'final': cur, 'len': len(txt)}
    log('%-24s len=%-6d %s' % (slug, len(txt), (txt[:70].replace('\n', ' ') if txt else '')))

# ---------- API：fetch 取 JSON ----------
for slug, url in APIS:
    ev("location.href='%s/hc/zh-cn'" % ORIGIN, to=20000)
    time.sleep(1.5)
    raw = ev("""(async()=>{
      try{
        const r = await fetch('%s', {credentials:'include', headers:{'Accept':'application/json'}});
        const t = await r.text();
        return r.status + '\\n' + t.slice(0, 20000);
      }catch(e){ return 'ERR:'+e.message; }
    })()""" % url)
    with open(os.path.join(OUTDIR, slug + '.txt'), 'w', encoding='utf-8') as f:
        f.write('URL: %s\n\n%s' % (url, raw))
    log('%-24s %s' % (slug, str(raw)[:120].replace('\n', ' ')))

json.dump(results, open(os.path.join(LGDIR, 'link_crawl_index.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
logf.close()
