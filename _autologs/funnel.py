# -*- coding: utf-8 -*-
"""funnel.py —— 全部 mined 产出按提交闸门筛选，输出达标候选清单（自写 UTF-8）
闸门：S+F≥4.0 / tS≥1.25 / 无 FAIL / F≥2.0 / TO≤20%
"""
import io, json, os, csv, re

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

# 已提交 id
sub = set()
raw = io.open(LED, 'rb').read().decode('utf-8-sig')
for r in csv.reader(io.StringIO(raw)):
    if r and r[0].strip() and r[0].strip().lower() != 'id':
        sub.add(r[0].strip())

OK, WEAK, BAD, DUP = [], [], [], 0
for x in os.listdir(MINED):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MINED, x), encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid:
        continue
    if aid in sub:
        DUP += 1
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe'); F = i.get('fitness'); TO = i.get('turnover')
    tS = t.get('sharpe')
    if S is None or F is None or TO is None:
        continue
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    rec = dict(cid=d.get('_cid') or x[:-5], aid=aid, S=S, F=F, tS=tS or 0, TO=TO,
               SF=S + F, ret=i.get('returns') or 0, margin=i.get('margin') or 0,
               neut=d.get('_neut'), decay=d.get('_decay'), fa=fa)
    if fa:
        BAD.append(rec)
        continue
    if S + F >= 4.0 and (tS or 0) >= 1.25 and F >= 2.0 and TO <= 0.20:
        OK.append(rec)
    elif S + F >= 4.0 and (tS or 0) >= 1.25:
        WEAK.append(rec)

L = []
L.append('mined 总文件(含已提交)去重后: 已提交命中 %d' % DUP)
L.append('闸门通过: %d 条 | 差 F/TO: %d 条 | 带 FAIL: %d 条' % (len(OK), len(WEAK), len(BAD)))
L.append('')
L.append('== 闸门全过（按 Fitness 降序）==')
for c in sorted(OK, key=lambda z: -z['F']):
    L.append("  %-30s %s S=%.2f F=%.2f tS=%.2f TO=%5.1f%% ret=%.1f%% margin=%5.1fbp neut=%s"
             % (c['cid'], c['aid'], c['S'], c['F'], c['tS'], c['TO'] * 100,
                c['ret'] * 100, c['margin'] * 1e4, c['neut']))
L.append('')
L.append('== 差 F/TO（按 S+F 降序，前 25）==')
for c in sorted(WEAK, key=lambda z: -z['SF'])[:25]:
    L.append("  %-30s %s S=%.2f F=%.2f tS=%.2f TO=%5.1f%% F/TO卡口"
             % (c['cid'], c['aid'], c['S'], c['F'], c['tS'], c['TO'] * 100))

io.open(ROOT + '_autologs/_funnel.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
