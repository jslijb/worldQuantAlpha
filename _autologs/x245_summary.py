# -*- coding: utf-8 -*-
"""汇总 x245 (MARKET 换挡) 批次指标, 输出到 _x245_summary.txt"""
import os, io, json, glob

os.chdir(r'D:\Python\worldquant')
OUT = io.open('_autologs/_x245_summary.txt', 'w', encoding='utf-8')

def w(s=''):
    OUT.write(str(s) + '\n')

def g(d, *path, default=None):
    cur = d
    for p in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(p)
        if cur is None:
            return default
    return cur

rows = []
for fp in sorted(glob.glob('data/alpha_quality_analysis/mined/x245_*.json')):
    try:
        d = json.load(io.open(fp, encoding='utf-8'))
    except Exception as e:
        w('READ FAIL %s %s' % (fp, e))
        continue
    aid = d.get('id') or g(d, 'alpha', 'id')
    S = g(d, 'is', 'sharpe')
    F = g(d, 'is', 'fitness')
    TO = g(d, 'is', 'turnover')
    R = g(d, 'is', 'returns')
    tS = g(d, 'test', 'sharpe')
    checks = g(d, 'is', 'checks', default=[]) or []
    fails = [c.get('name') for c in checks if c.get('result') == 'FAIL']
    st = g(d, 'settings', default={}) or {}
    code = g(d, 'regular', 'code') or d.get('code') or ''
    rows.append(dict(file=os.path.basename(fp), aid=aid, S=S, F=F, TO=TO, R=R, tS=tS,
                     fails=fails, uni=st.get('universe'), neu=st.get('neutralization'),
                     dec=st.get('decay'), d0=st.get('delay'), code=code))

w('x245 MARKET 换挡批次汇总  (文件 %d 个)' % len(rows))
w('=' * 110)
hdr = '%-28s %-10s %6s %6s %7s %7s %6s  %-22s %s/%s/d%s'
w(hdr % ('file', 'id', 'S', 'F', 'TO', 'R', 'tS', 'FAIL', 'uni', 'neu', 'dec'))
w('-' * 110)
for r in sorted(rows, key=lambda x: -(x['F'] or -9)):
    w(hdr % (r['file'][:28], str(r['aid'])[:10],
             '%.2f' % r['S'] if r['S'] is not None else '-',
             '%.2f' % r['F'] if r['F'] is not None else '-',
             '%.4f' % r['TO'] if r['TO'] is not None else '-',
             '%.4f' % r['R'] if r['R'] is not None else '-',
             '%.2f' % r['tS'] if r['tS'] is not None else '-',
             ','.join(r['fails']) or 'none',
             r['uni'], r['neu'], r['dec']))

# 过闸判定
w('')
w('=' * 110)
gate = [r for r in rows
        if (r['S'] or 0) + (r['F'] or 0) >= 4.0 and (r['tS'] or 0) >= 1.25
        and not r['fails'] and (r['F'] or 0) >= 2.0 and (r['TO'] or 9) <= 0.20]
w('过质量闸门 (S+F>=4.0 & tS>=1.25 & 无FAIL & F>=2.0 & TO<=0.20): %d 条' % len(gate))
for r in sorted(gate, key=lambda x: -(x['F'] or 0)):
    w('  %-10s S=%.2f F=%.2f TO=%.4f tS=%.2f' % (r['aid'], r['S'], r['F'], r['TO'], r['tS']))

# 更宽的观察口径
w('')
w('放宽口径 (无FAIL & TO<=0.25 & F>=1.5) 供参考:')
loose = [r for r in rows if not r['fails'] and (r['TO'] or 9) <= 0.25 and (r['F'] or 0) >= 1.5]
for r in sorted(loose, key=lambda x: -(x['F'] or 0)):
    w('  %-10s S=%.2f F=%.2f TO=%.4f tS=%.2f' % (r['aid'], r['S'], r['F'], r['TO'], r['tS'] or -1))

w('')
w('表达式 (前 200 字符):')
for r in rows:
    w('  %-10s %s' % (r['aid'], (r['code'] or '')[:200]))

OUT.close()
print('done')
