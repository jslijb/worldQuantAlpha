# -*- coding: utf-8 -*-
"""skeleton.py —— 714 条过闸候选按"骨架"聚类：714 条实际是几族？

背景：李工问「3500+ 待提交，提夏普+降换手是不是就能提交」。
普查结论是质量闸门过 714 条、实测过墙 0 条。但 714 条里大量是同骨架兄弟
（换 universe / 换中性化 / 增减一腿生成），它们与已提交池撞的对手是同一条，
所以"714 次尝试"不等于"714 个独立机会"。

本脚本：提取每条表达式的字段集合做骨架签名 → 输出族数、族内最大 S、族代表。
输出 _autologs/_skeleton.txt
"""
import io, os, csv, json, re, collections

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined/'
LED = ROOT + 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'

# 非信号标识符（算子/分组参数/常量），不算字段
NOTFIELD = set('''true false nan subindustry industry sector market country exchange
densify bucket filter trade_when hump tail kth_element last_diff_value days_from_last_change'''.split())

sub = set()
with io.open(LED, encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip():
            sub.add(r[0].strip())

gate = []
for x in os.listdir(MINED):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(MINED + x, encoding='utf-8'))
    except Exception:
        continue
    aid = d.get('id')
    if not aid or aid in sub:
        continue
    i = d.get('is') or {}; t = d.get('test') or {}
    S = i.get('sharpe') or 0; F = i.get('fitness') or 0
    TO = i.get('turnover') or 0; tS = t.get('sharpe') or 0
    fa = [c.get('name') for c in (i.get('checks') or []) if c.get('result') == 'FAIL']
    if S + F < 4.0 or tS < 1.25 or fa or F < 1.8:
        continue
    code = ((d.get('regular') or {}).get('code')) or ''
    st = d.get('settings') or {}
    gate.append(dict(aid=aid, cid=x[:-5], S=S, F=F, TO=TO, tS=tS, code=code,
                     uni=st.get('universe'), neu=st.get('neutralization'),
                     dec=st.get('decay'), d0=st.get('delay')))

def sig(code):
    ops = set(re.findall(r'([a-z_][a-z0-9_]*)\s*\(', code))
    ids = set(re.findall(r'\b([a-z_][a-z0-9_]*)\b', code))
    return frozenset(ids - ops - NOTFIELD)

fam = collections.defaultdict(list)
for r in gate:
    fam[sig(r['code'])].append(r)

L = []
L.append('过闸未提交候选 %d 条' % len(gate))
L.append('不同表达式（code 去重）：%d' % len(set(r['code'] for r in gate)))
L.append('骨架族数（字段集合签名）：%d' % len(fam))
L.append('')

sizes = sorted((len(v) for v in fam.values()), reverse=True)
L.append('族规模分布：max %d  中位 %d  单条族 %d 个'
         % (sizes[0], sizes[len(sizes)//2], sum(1 for s in sizes if s == 1)))
L.append('')
L.append('== 按族内最大 S 降序 Top 30 族 ==')
for fs, mem in sorted(fam.items(), key=lambda kv: -max(r['S'] for r in kv[1]))[:30]:
    top = max(mem, key=lambda r: r['S'])
    L.append('  族%-3d 条数=%-4d maxS=%.2f maxF=%.2f | 代表 %s %s S=%.2f F=%.2f TO=%.3f tS=%.2f %s/%s/d%s'
             % (len(mem), len(mem), max(r['S'] for r in mem), max(r['F'] for r in mem),
                top['aid'], top['cid'][:26], top['S'], top['F'], top['TO'], top['tS'],
                top['uni'], top['neu'], top['dec']))
    L.append('       字段: ' + ', '.join(sorted(fs)[:12]))
L.append('')
L.append('== 按 S>=3.2 挑族代表（高质量 + 一族一条）==')
hi = [max(mem, key=lambda r: r['S']) for fs, mem in fam.items() if max(r['S'] for r in mem) >= 3.2]
hi.sort(key=lambda r: -r['S'])
for r in hi:
    L.append('  %s %-28s S=%.2f F=%.2f TO=%.3f tS=%.2f %s/%s/d%s'
             % (r['aid'], r['cid'][:26], r['S'], r['F'], r['TO'], r['tS'], r['uni'], r['neu'], r['dec']))
L.append('  共 %d 条（= 可尝试的独立机会数）' % len(hi))

io.open(ROOT + '_autologs/_skeleton.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok gate=%d fam=%d hi=%d' % (len(gate), len(fam), len(hi)))
