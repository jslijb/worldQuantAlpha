# -*- coding: utf-8 -*-
"""screen_api.py —— 用平台侧真数筛未提交池（不依赖本地 mined 目录）

输入 data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json（pull_unsubmitted.py 产出）
做四件事：
  1. 过质量闸门（S+F>=4.0 / tS>=1.25 / 无 FAIL / F>=1.8）计数
  2. 与本地台账比对（剔除已提交过的）
  3. 与本地 mined 目录比对 → 找出"平台有、本地没有"的增量候选
  4. 增量按骨架族聚类 + 按 F 排序出明细
输出 _autologs/_screen_api.txt
"""
import os, io, csv, re, json, collections, statistics as st

ROOT = 'D:/Python/worldquant/'
SRC = ROOT + 'data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json'
MINED = ROOT + 'data/alpha_quality_analysis/mined/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

NOTFIELD = set('''true false nan subindustry industry sector market country exchange
densify bucket filter trade_when hump tail kth_element last_diff_value days_from_last_change'''.split())

def sig(code):
    ops = set(re.findall(r'([a-z_][a-z0-9_]*)\s*\(', code or ''))
    ids = set(re.findall(r'\b([a-z_][a-z0-9_]*)\b', code or ''))
    return frozenset(ids - ops - NOTFIELD)

# 台账 + 本地 mined 的 id 集合
sub = set()
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip():
            sub.add(r[0].strip())

local = {}
for x in os.listdir(MINED):
    if x.endswith('.json'):
        try:
            d = json.load(io.open(MINED + x, encoding='utf-8'))
            if d.get('id'):
                local[d['id']] = x
        except Exception:
            pass

rows = json.load(io.open(SRC, encoding='utf-8'))
L = []
L.append('== 0. 平台侧未提交池 ==')
L.append('  拉取条目 %d 条' % len(rows))
L.append('  台账已提交 id %d 个；本地 mined json %d 个' % (len(sub), len(local)))
L.append('')

def met(a):
    i = a.get('is') or {}
    t = a.get('test') or {}
    return (i.get('sharpe') or 0, i.get('fitness') or 0, i.get('turnover') or 0,
            i.get('returns') or 0, t.get('sharpe'), i.get('checks') or [],
            ((a.get('regular') or {}).get('code')) or '', a.get('settings') or {}, a.get('grade'))

# 1. 过闸统计（全池，不分本地/平台）
gate, noTS, fail = [], 0, 0
for a in rows:
    S, F, TO, R, tS, ck, code, sett, gr = met(a)
    fa = [c.get('name') for c in ck if c.get('result') == 'FAIL']
    if fa:
        fail += 1
        continue
    if S + F < 4.0 or F < 1.8:
        continue
    if tS is None:
        noTS += 1
        continue
    if tS < 1.25:
        continue
    gate.append(dict(aid=a['id'], S=S, F=F, TO=TO, R=R, tS=tS, code=code,
                     uni=sett.get('universe'), neu=sett.get('neutralization'),
                     dec=sett.get('decay'), d0=sett.get('delay'), gr=gr,
                     sub=a['id'] in sub, loc=a['id'] in local,
                     dt=(a.get('dateCreated') or '')[:10]))

L.append('== 1. 过质量闸门（S+F>=4.0 / tS>=1.25 / 无 FAIL / F>=1.8）==')
L.append('  有 FAIL 的：%d 条（直接排除）' % fail)
L.append('  过 S+F/F 但缺 test sharpe 的：%d 条（单列，未计入）' % noTS)
L.append('  过闸合计：%d 条' % len(gate))
L.append('    · 其中已在台账（已提交过）：%d 条' % sum(1 for g in gate if g['sub']))
L.append('    · 其中本地 mined 已有：%d 条' % sum(1 for g in gate if g['loc']))
L.append('    · **增量（本地 mined 没有）：%d 条**' % sum(1 for g in gate if not g['loc']))
L.append('')

# 2. 增量分析
inc = [g for g in gate if not g['loc'] and not g['sub']]
if inc:
    L.append('== 2. 增量候选质量分布 ==')
    for k in ('S', 'F', 'TO', 'tS'):
        v = sorted(g[k] for g in inc)
        L.append('  %-3s 中位 %.3f 均值 %.3f p90 %.3f max %.3f'
                 % (k, v[len(v)//2], st.mean(v), v[int(len(v) * 0.9)], v[-1]))
    fam = collections.defaultdict(list)
    for g in inc:
        fam[sig(g['code'])].append(g)
    L.append('  骨架族数：%d（最大族 %d 条）' % (len(fam), max(len(v) for v in fam.values())))
    L.append('')
    L.append('== 3. 增量按 F 排序 Top 40 ==')
    for g in sorted(inc, key=lambda x: -x['F'])[:40]:
        L.append('  %-10s S=%5.2f F=%5.2f TO=%.3f tS=%4.2f %s/%s/d%s %s %s'
                 % (g['aid'], g['S'], g['F'], g['TO'], g['tS'], g['uni'], g['neu'], g['dec'],
                    g['dt'], g['gr']))
        L.append('        ' + (g['code'] or '')[:150])
    L.append('')
    L.append('== 4. 增量按族（S>=3.0 的族代表）==')
    reps = [max(v, key=lambda r: r['S']) for v in fam.values() if max(r['S'] for r in v) >= 3.0]
    reps.sort(key=lambda r: -r['S'])
    for r in reps[:40]:
        L.append('  %-10s S=%5.2f F=%5.2f TO=%.3f tS=%4.2f %s %s'
                 % (r['aid'], r['S'], r['F'], r['TO'], r['tS'], r['dt'], r['gr']))
    L.append('  共 %d 条族代表' % len(reps))
else:
    L.append('== 2/3/4. 无增量（平台过闸池是本地 mined 的子集）==')

# 5. 存量过闸（本地已有的）
L.append('')
L.append('== 5. 平台侧过闸但本地 mined 已有 ==')
L.append('  共 %d 条' % sum(1 for g in gate if g['loc']))
if gate:
    v = sorted(g['F'] for g in gate)
    L.append('  F 中位 %.3f max %.3f' % (v[len(v) // 2], v[-1]))

io.open(ROOT + '_autologs/_screen_api.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok gate=%d inc=%d' % (len(gate), len(inc)))
