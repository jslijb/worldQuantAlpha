# -*- coding: utf-8 -*-
"""univ_report.py —— Universe 轴弹药总表

合并两个事实源：
  ① all_unsubmitted.json（3554 条）→ 非 TOP3000、无 FAIL 的候选及其指标
  ② _judge_ids_nontop.txt（76 条已判）→ 各自 corr_max / need / 判定
输出"过闸 + corr 干净"的可提交清单，按 Fitness 排序。
"""
import os as _os, pathlib as _pl, json, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

L = []

# ---- ① 平台池 ----
data = json.load(io.open('data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])

cand = {}
for a in data:
    st = a.get('settings') or {}
    b = a.get('is') or {}
    te = a.get('test') or {}
    uni = st.get('universe')
    if uni == 'TOP3000':
        continue
    fa = [c.get('name') for c in (b.get('checks') or []) if c.get('result') == 'FAIL']
    S = b.get('sharpe') or 0; F = b.get('fitness') or 0
    TO = b.get('turnover'); tS = te.get('sharpe') or 0
    cand[a['id']] = dict(id=a['id'], uni=uni, neu=st.get('neutralization'), dly=st.get('delay'),
                         dec=st.get('decay'), S=S, F=F, TO=TO, tS=tS, fa=fa,
                         mg=(b.get('margin') or 0) * 10000)

# ---- ② 判决结果 ----
import re
corr = {}
p = '_autologs/_judge_ids_nontop.txt'
if _os.path.exists(p):
    for ln in io.open(p, encoding='utf-8'):
        m = re.match(r'^([A-Za-z0-9]{8})\s+\S+\s+\S+\s+\d+\s+\d+\s+[\d.\-]+\s+[\d.\-]+\s+[\d.]+\s+[\d.\-]+\s*\|\s*([\d.]+)\s*(\S*)\s*([\d.\-]+)?\s*(.*)$', ln.rstrip())
        if m:
            corr[m.group(1)] = (float(m.group(2)), m.group(3), m.group(4), m.group(5).strip())

L.append('Universe 轴弹药总表（非 TOP3000，全部 %d 条）' % len(cand))
L.append('=' * 118)
L.append('%-10s %-9s %-11s %3s %4s %6s %6s %6s %6s %8s | %-8s %s'
         % ('id', 'universe', 'neutral', 'dly', 'dec', 'S', 'F', 'TO', 'tS', 'margin', 'corr_max', '状态'))
L.append('-' * 118)

def gate(c):
    return (not c['fa']) and c['S'] + c['F'] >= 4.0 and c['tS'] >= 1.25 and (c['TO'] or 9) <= 0.20

rows = sorted(cand.values(), key=lambda x: (-(x['F'] or 0)))
for c in rows:
    cm = corr.get(c['id'])
    cmv = ('%.4f' % cm[0]) if cm else '  -  '
    if c['fa']:
        tag = 'FAIL=' + ','.join(c['fa'])[:28]
    elif not gate(c):
        why = []
        if c['S'] + c['F'] < 4.0: why.append('SF%.2f' % (c['S'] + c['F']))
        if c['tS'] < 1.25: why.append('tS%.2f' % c['tS'])
        if (c['TO'] or 9) > 0.20: why.append('TO%.3f' % (c['TO'] or 0))
        tag = '不过闸(' + '/'.join(why) + ')'
    else:
        if cm is None:
            tag = '★过闸·未判'
        elif cm[0] <= 0.0001:
            tag = '★★ 过闸 + 已判干净'
        elif cm[0] <= 0.685:
            tag = '★ 过闸·直通边缘'
        else:
            tag = '过闸·撞墙(' + str(cm[1]) + ' 需' + str(cm[2]) + ')'
    L.append('%-10s %-9s %-11s %3s %4s %6.3f %6.3f %6.4f %6.2f %8.1f | %-8s %s'
             % (c['id'], c['uni'], c['neu'], c['dly'], c['dec'], c['S'], c['F'],
                c['TO'] or 0, c['tS'], c['mg'], cmv, tag))

# ---- 结论 ----
clean = [c for c in rows if gate(c) and corr.get(c['id']) and corr[c['id']][0] <= 0.0001]
clean.sort(key=lambda x: -(x['F'] or 0))
L.append('')
L.append('=' * 118)
L.append('★★ 过闸 + corr 已判干净（直通确定）= %d 条：' % len(clean))
for c in clean:
    L.append('   %-10s %-9s dec=%-3s S=%.2f F=%.2f TO=%.4f tS=%.2f margin=%.1fbp'
             % (c['id'], c['uni'], c['dec'], c['S'], c['F'], c['TO'] or 0, c['tS'], c['mg']))

nofail = [c for c in rows if not c['fa']]
gate_ok = [c for c in rows if gate(c)]
L.append('')
L.append('非 TOP3000 且无 FAIL = %d 条；其中过质量闸门 = %d 条；已判且 corr 干净 = %d 条'
         % (len(nofail), len(gate_ok), len(clean)))
byni = {}
for c in nofail:
    byni[c['uni']] = byni.get(c['uni'], 0) + 1
L.append('无 FAIL 各池分布：%s' % byni)

io.open('_autologs/_univ_report.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
