# -*- coding: utf-8 -*-
"""smallpool_now.py —— 盘点待提交池里的非 TOP3000 弹药（换池批次产出）

用法: python _autologs/smallpool_now.py [--min-f 1.0] [--min-ts 0.0]
输出: _autologs/_smallpool_now.txt
"""
import os as _os, pathlib as _pl, sys, json, io, collections

_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

OUT = io.open('_autologs/_smallpool_now.txt', 'w', encoding='utf-8')


def say(s=''):
    OUT.write(str(s) + '\n')


def opt(name, default=None):
    a = sys.argv
    for x in a:
        if x == name: return a[a.index(x) + 1]
        if x.startswith(name + '='): return x.split('=', 1)[1]
    return default


MIN_F = float(opt('--min-f', '1.0'))
MIN_TS = float(opt('--min-ts', '0.0'))

D = json.load(io.open('data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(D, dict):
    D = D.get('results', [])

ledger = set()
try:
    for l in io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read().splitlines()[1:]:
        if l.strip():
            ledger.add(l.split(',')[0].strip().strip('"'))
except Exception:
    pass

# 已知判决结果（过墙清单）
passed = set()
try:
    txt = io.open('_autologs/_find_passers.txt', encoding='utf-8').read()
    for line in txt.splitlines():
        t = line.split()
        if t and len(t[0]) == 8 and t[0][:2] not in ('id',):
            passed.add(t[0])
except Exception:
    pass

rows = []
byu = collections.Counter()
for a in D:
    st = a.get('settings') or {}
    u = st.get('universe')
    if not u or u == 'TOP3000':
        continue
    byu[u] += 1
    ch = ((a.get('is') or {}).get('checks') or [])
    fails = [c.get('name') for c in ch if c and c.get('result') == 'FAIL']
    b = a.get('is') or {}
    te = a.get('test') or {}
    S = b.get('sharpe'); F = b.get('fitness'); TO = b.get('turnover'); tS = te.get('sharpe')
    if F is None or tS is None or TO is None or S is None:
        continue
    rows.append(dict(id=a['id'], u=u, neu=st.get('neutralization'), dec=st.get('decay'),
                     dly=st.get('delay'), S=S, F=F, TO=TO, tS=tS, nfail=len(fails),
                     fails=fails, code=((a.get('regular') or {}).get('code') or '')[:110]))

say('== 待提交池里的非 TOP3000 候选（全部 %d 条）==' % sum(byu.values()))
for k, v in byu.most_common():
    say('   %-9s %d' % (k, v))
say('')

clean = [r for r in rows if r['nfail'] == 0 and r['F'] >= MIN_F and r['tS'] >= MIN_TS]
clean.sort(key=lambda r: -r['F'])
say('== 无 FAIL 且 F>=%.2f tS>=%.2f ：%d 条 ==' % (MIN_F, MIN_TS, len(clean)))
say('%-10s %-8s %-12s %-4s %-4s %6s %6s %7s %6s %-8s %s'
    % ('id', 'universe', 'neut', 'dly', 'dec', 'S', 'F', 'TO', 'tS', '过墙?', '表达式'))
for r in clean:
    say('%-10s %-8s %-12s %-4s %-4s %6.2f %6.2f %7.4f %6.2f %-8s %s'
        % (r['id'], r['u'], str(r['neu'])[:12], r['dly'], r['dec'],
           r['S'], r['F'], r['TO'], r['tS'], ('★是' if r['id'] in passed else ''), r['code']))

say('')
say('== 带 FAIL 的非 TOP3000（仅计数）==')
bad = collections.Counter()
for r in rows:
    if r['nfail']:
        bad[r['u']] += 1
for k, v in bad.most_common():
    say('   %-9s %d' % (k, v))

OUT.close()
print('done clean=%d' % len(clean))
