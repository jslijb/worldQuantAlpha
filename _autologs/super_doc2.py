# -*- coding: utf-8 -*-
"""super_doc2.py —— 拉 challenge-help / 10-steps 原文，锁定 SuperAlpha 解锁条件"""
import json, io, requests, re

sess = requests.Session()
sess.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
sess.post('https://api.worldquantbrain.com/authentication')

L = []


def txt(node, out):
    """递归抽取 content 块里的文字"""
    if isinstance(node, dict):
        t = node.get('type')
        if t in ('TEXT', 'EQUATION', 'LABEL', 'HEADING'):
            for k in ('content', 'text', 'label'):
                if isinstance(node.get(k), str) and node[k].strip():
                    out.append(node[k].strip())
        elif t == 'TABLE':
            for row in node.get('rows', []):
                out.append(' | '.join(str(c) for c in row))
        for k, v in node.items():
            if k not in ('content', 'text'):
                txt(v, out)
    elif isinstance(node, list):
        for x in node:
            txt(x, out)


for pid in ['challenge-help', '10-steps-start-brain-platform', 'about-brain-platform']:
    try:
        r = sess.get('https://api.worldquantbrain.com/tutorial-pages/' + pid)
        L.append('=' * 70)
        L.append('PAGE %s -> %s' % (pid, r.status_code))
        if r.status_code != 200:
            L.append('   ' + r.text[:300])
            continue
        j = r.json()
        L.append('TITLE: %s' % j.get('title'))
        out = []
        txt(j.get('content'), out)
        seen = set()
        for line in out:
            line = re.sub(r'\s+', ' ', line).strip()
            if line and line not in seen:
                seen.add(line)
                L.append('  ' + line)
    except Exception as e:
        L.append('PAGE %s ERR %s' % (pid, e))

io.open('_autologs/_super_doc2.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
