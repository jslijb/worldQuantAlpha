# -*- coding: utf-8 -*-
"""核验：HC 文章更新时间 + 本账号近 3 个月独立提交日"""
import json
import os
import subprocess
import time
from datetime import datetime, timedelta

import requests
from websocket import create_connection

EDGE = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
DST = r'D:\Python\worldquant\_tmp_edge_profile'
PORT = 9333
BASE = 'https://support.worldquantbrain.com'
LGDIR = r'D:\Python\worldquant\_logs'
OUT = os.path.join(LGDIR, 'verify_facts.json')

KEY_ARTICLES = {
    '11591947651607': 'What is the Value Factor?',
    '44561175314199': 'VF 生成条件（20 个提交日）',
    '14673192879511': '提交月数是否影响 VF',
    '4672184130455': 'How can you earn more Base payment?',
    '4418494822423': 'Base payment 如何计算',
    '6161120218775': '如何提升 OS 表现从而提升 VF',
    '26716012806295': 'What are pyramids?',
    '36966491408535': 'Osmosis 分配要点',
    '37443828624279': 'PP Alpha 如何影响补偿',
    '26715994416535': 'Combined Alpha Performance',
}

S = requests.Session()
S.trust_env = False
S.proxies = {'http': None, 'https': None}

err = open(os.path.join(LGDIR, 'edge_err.txt'), 'w')
p = subprocess.Popen(
    [EDGE, '--user-data-dir=%s' % DST, '--remote-debugging-port=%d' % PORT,
     '--remote-allow-origins=*', '--no-first-run', '--no-default-browser-check',
     'https://platform.worldquantbrain.com'], stdout=err, stderr=err, close_fds=True)

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
                return 'EXC:' + str(res['exceptionDetails'])[:250]
            return res.get('result', {}).get('value')


log = []
result = {}

# 1) HC 文章元数据（用 support 域，避免跨域）
ev("location.href='%s/hc/en-us'" % BASE, to=30000)
time.sleep(2)
for aid, title in KEY_ARTICLES.items():
    raw = ev("""(async()=>{
      try{
        const r = await fetch('%s/api/v2/help_center/en-us/articles/%s.json',{credentials:'include'});
        if(!r.ok) return 'HTTP'+r.status;
        const j = await r.json();
        const a=j.article||{};
        return JSON.stringify({title:a.title,created:a.created_at,updated:a.updated_at,
                               edited:a.edited_at,author:a.author_id,draft:a.draft});
      }catch(e){return 'ERR:'+e.message;}
    })()""" % (BASE, aid))
    result[aid] = {'desc': title, 'meta': raw}
    log.append('%-16s %s -> %s' % (aid, title[:26], str(raw)[:150]))

# 2) 本账号已提交 Alpha 的提交日
ev("location.href='https://platform.worldquantbrain.com/alpha'", to=30000)
time.sleep(3)
raw = ev("""(async()=>{
  const out=[]; let off=0;
  for(let i=0;i<12;i++){
    const u='https://api.worldquantbrain.com/users/self/alphas?limit=100&offset='+off+
      '&status!=UNSUBMITTED&order=-dateSubmitted';
    const r=await fetch(u,{credentials:'include'});
    if(!r.ok) return 'HTTP'+r.status+'@'+off;
    const j=await r.json();
    const arr=j.results||j;
    if(!arr.length) break;
    for(const a of arr) out.push({id:a.id,ds:a.dateSubmitted,status:a.status,
      sharpe:(a.is||{}).sharpe,fitness:(a.is||{}).fitness,
      turnover:(a.is||{}).turnover, region:(a.settings||{}).region, delay:(a.settings||{}).delay});
    off += arr.length;
    if(arr.length<100) break;
  }
  return JSON.stringify({n:out.length, alphas:out});
})()""", to=180000)

result['self_alphas'] = raw[:400000]
try:
    d = json.loads(raw)
    al = d.get('alphas', [])
    days = sorted({(a.get('ds') or '')[:10] for a in al if a.get('ds')})
    log.append('')
    log.append('已提交 Alpha 总数: %d' % d.get('n', 0))
    log.append('有提交日期的条目数: %d' % sum(1 for a in al if a.get('ds')))
    log.append('日期范围: %s ~ %s' % (days[0] if days else '-', days[-1] if days else '-'))
    log.append('不同提交日总数: %d' % len(days))
    # 近 90 天（以最新日期为基准）
    if days:
        latest = datetime.strptime(days[-1], '%Y-%m-%d')
        cut = latest - timedelta(days=90)
        recent_days = [x for x in days if datetime.strptime(x, '%Y-%m-%d') >= cut]
        log.append('近 90 天内（截至 %s）独立提交日: %d' % (days[-1], len(recent_days)))
        log.append('  这些日期: %s' % ', '.join(recent_days))
        # 最近 10 天
        log.append('最近 6 个提交日: %s' % ', '.join(days[-6:]))
except Exception as e:
    log.append('解析 self_alphas 失败: %s' % e)

json.dump(result, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for l in log:
    print(l)

ws.close()
p.terminate()
time.sleep(1)
try:
    p.kill()
except Exception:
    pass
