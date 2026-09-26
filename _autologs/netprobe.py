# -*- coding: utf-8 -*-
"""网络连通性探测：auth 端点重试 + 备用域名对照"""
import io, os, time, datetime
import requests

ROOT = r'D:\Python\worldquant'
L = []
L.append('time=%s' % datetime.datetime.now())

# 读凭证
cred = {}
p = os.path.join(ROOT, 'brain_credentials.txt')
for ln in io.open(p, encoding='utf-8'):
    if ':' in ln or '=' in ln:
        k, v = (ln.replace(':', '=').split('=', 1) + [''])[:2]
        cred[k.strip().lower()] = v.strip()
L.append('cred keys=%s' % list(cred.keys()))
u = cred.get('email') or cred.get('username') or ''
pw = cred.get('password') or ''

L.append('--- A) auth 端点连续 6 次 ---')
for i in range(6):
    t0 = time.time()
    try:
        s = requests.Session()
        r = s.post('https://api.worldquantbrain.com/authentication',
                   auth=(u, pw), timeout=30)
        L.append('  #%d %s http=%s dt=%.1fs' % (i, r.status_code, r.status_code, time.time() - t0))
    except Exception as e:
        L.append('  #%d ERR %s %s dt=%.1fs' % (i, type(e).__name__, str(e)[:100], time.time() - t0))
    time.sleep(2)

L.append('--- B) 对照：平台首页 / 第三方 ---')
for url in ['https://api.worldquantbrain.com/',
            'https://worldquantbrain.com/',
            'https://www.baidu.com/']:
    try:
        r = requests.get(url, timeout=20)
        L.append('  %-42s http=%s' % (url, r.status_code))
    except Exception as e:
        L.append('  %-42s ERR %s %s' % (url, type(e).__name__, str(e)[:80]))

# 本机代理环境变量
L.append('--- C) 代理环境变量 ---')
for k in ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'NO_PROXY']:
    L.append('  %s=%s' % (k, os.environ.get(k, '(unset)')))

io.open(os.path.join(ROOT, '_autologs', '_netprobe.txt'), 'w', encoding='utf-8').write('\n'.join(L))
print('\n'.join(L))
