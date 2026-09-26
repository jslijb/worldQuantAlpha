# -*- coding: utf-8 -*-
"""api_census.py —— 把平台全量未提交池 (all_unsubmitted.json) 按维度切开
输出 _api_census.txt
"""
import os, io, json, csv, collections

os.chdir(r'D:\Python\worldquant')
P = 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
L = []
def w(s=''):
    L.append(str(s))

data = json.load(io.open(P, encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', data.get('alphas', []))
w('平台未提交池条目: %d' % len(data))

# 提交台账 (唯一 id)
sub = set()
with io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig') as f:
    for i, row in enumerate(csv.reader(f)):
        if i == 0:
            continue
        if row and row[0].strip():
            sub.add(row[0].strip())
w('台账唯一 id: %d' % len(sub))

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
for a in data:
    st = a.get('settings') or {}
    checks = g(a, 'is', 'checks', default=[]) or []
    fails = [c.get('name') for c in checks if c and c.get('result') == 'FAIL']
    rows.append(dict(
        id=a.get('id'),
        status=a.get('status'), stage=a.get('stage'),
        S=g(a, 'is', 'sharpe'), F=g(a, 'is', 'fitness'),
        TO=g(a, 'is', 'turnover'), R=g(a, 'is', 'returns'),
        margin=g(a, 'is', 'margin'),
        tS=g(a, 'test', 'sharpe'), tF=g(a, 'test', 'fitness'),
        fails=fails,
        uni=st.get('universe'), neu=st.get('neutralization'),
        reg=st.get('region'), delay=st.get('delay'), dec=st.get('decay'),
        trunc=st.get('truncation'), inst=st.get('instrumentType'),
        pnd=g(st, 'pasteurization'), nan=st.get('nanHandling'),
        code=g(a, 'regular', 'code') or '',
        created=(a.get('dateCreated') or '')[:10],
    ))

w('')
w('== 维度分布 (全部 %d 条) ==' % len(rows))
for k in ['uni', 'neu', 'reg', 'delay', 'inst']:
    c = collections.Counter(r[k] for r in rows)
    w('  %-6s: %s' % (k, ', '.join('%s=%d' % (a, b) for a, b in c.most_common(12))))
w('  decay  : %s' % ', '.join('%s=%d' % (a, b) for a, b in
                              collections.Counter(r['dec'] for r in rows).most_common(12)))

# 平台自身判 FAIL 的
nf = [r for r in rows if not r['fails']]
w('')
w('平台未标 FAIL: %d / %d' % (len(nf), len(rows)))

# 质量闸门 (平台侧指标)
def gate(r):
    return (r['S'] or 0) + (r['F'] or 0) >= 4.0 and (r['tS'] or 0) >= 1.25 \
        and not r['fails'] and (r['F'] or 0) >= 1.8 and (r['TO'] or 9) <= 0.20
gt = [r for r in rows if gate(r)]
w('过质量闸门: %d 条' % len(gt))
w('  其中台账里已有: %d' % len([r for r in gt if r['id'] in sub]))
w('  真增量 (台账没有): %d' % len([r for r in gt if r['id'] not in sub]))

w('')
w('== 过闸候选按 universe 分 ==')
c = collections.Counter(r['uni'] for r in gt)
for a, b in c.most_common():
    w('  %-12s %d' % (a, b))
w('')
w('  == 过闸候选按 neutralization 分 ==')
for a, b in collections.Counter(r['neu'] for r in gt).most_common():
    w('  %-14s %d' % (a, b))

# ★ 关键: 过闸 且 非 TOP3000 (降池轴)
newax = [r for r in gt if r['uni'] not in ('TOP3000', None)]
w('')
w('== ★ 过闸 且 universe != TOP3000 : %d 条 ==' % len(newax))
hdr = '  %-10s %-12s %-14s %-9s %-5s %-4s %6s %6s %7s %6s %6s %s'
w(hdr % ('id', 'universe', 'neut', 'region', 'delay', 'dec', 'S', 'F', 'TO', 'tS', 'SF', '台账'))
for r in sorted(newax, key=lambda x: -(x['F'] or 0))[:60]:
    w(hdr % (str(r['id'])[:10], r['uni'], str(r['neu'])[:14], r['reg'], r['delay'], r['dec'],
             '%.2f' % r['S'], '%.2f' % r['F'], '%.3f' % r['TO'], '%.2f' % (r['tS'] or -1),
             '%.2f' % ((r['S'] or 0) + (r['F'] or 0)),
             'YES' if r['id'] in sub else 'no'))

# 所有非 TOP3000 (不论过闸)
allother = [r for r in rows if r['uni'] not in ('TOP3000', None)]
w('')
w('== 全部非 TOP3000 条目: %d 条, 按 universe ==' % len(allother))
for a, b in collections.Counter(r['uni'] for r in allother).most_common():
    w('  %-12s %d' % (a, b))

# 局部池 TOP3000 里 S 最高的 30 条 (看还有没有漏)
w('')
w('== TOP3000 过闸候选 F 前 40 (核对是否已在台账) ==')
top = [r for r in gt if r['uni'] == 'TOP3000']
w(hdr % ('id', 'universe', 'neut', 'region', 'delay', 'dec', 'S', 'F', 'TO', 'tS', 'SF', '台账'))
for r in sorted(top, key=lambda x: -(x['F'] or 0))[:40]:
    w(hdr % (str(r['id'])[:10], r['uni'], str(r['neu'])[:14], r['reg'], r['delay'], r['dec'],
             '%.2f' % r['S'], '%.2f' % r['F'], '%.3f' % r['TO'], '%.2f' % (r['tS'] or -1),
             '%.2f' % ((r['S'] or 0) + (r['F'] or 0)),
             'YES' if r['id'] in sub else 'no'))

# delay 分布 (D1 vs D0) —— Delay 子项得分
w('')
w('== 全部条目 delay 分布 ==')
for a, b in collections.Counter(r['delay'] for r in rows).most_common():
    w('  %s -> %d' % (a, b))
w('== 过闸候选 delay 分布 ==')
for a, b in collections.Counter(r['delay'] for r in gt).most_common():
    w('  %s -> %d' % (a, b))

io.open('_autologs/_api_census.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('written')
