# -*- coding: utf-8 -*-
"""诊断：列出 Edge 的所有 CDP target"""
import json
import os
import subprocess
import time

import requests

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
URL = 'https://support.worldquantbrain.com/hc/zh-cn/community/topics/18910956638743'

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(r'D:\Python\worldquant\_logs\edge_err.txt', 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check', URL],
    stdout=err, stderr=err, close_fds=True)

for _ in range(60):
    try:
        S.get('http://127.0.0.1:%d/json/version' % PORT, timeout=2)
        break
    except Exception:
        time.sleep(0.5)

for i in range(20):
    r = S.get('http://127.0.0.1:%d/json/list' % PORT, timeout=5)
    lst = r.json()
    print('--- try %d, %d targets' % (i, len(lst)))
    for t in lst:
        print('  type=%s  url=%s' % (t.get('type'), (t.get('url') or '')[:110]))
    pages = [t for t in lst if t.get('type') == 'page']
    if any('support.worldquantbrain.com' in (t.get('url') or '') for t in pages):
        print('>>> 找到论坛页 target')
        print(json.dumps([{'id': t['id'], 'url': t['url'], 'ws': t.get('webSocketDebuggerUrl')}
                          for t in pages], ensure_ascii=False, indent=1))
        break
    time.sleep(1.5)

p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
