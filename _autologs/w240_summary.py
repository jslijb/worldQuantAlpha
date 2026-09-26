# -*- coding: utf-8 -*-
"""w240_summary.py —— 精确统计 w240 批次结果（不凭印象）"""
import io, re, json, os

t = io.open('_autologs/_w240_run.txt', encoding='utf-8', errors='replace').read()
lines = t.splitlines()

rec = []
for ln in lines:
    m = re.search(r'^(\S+)\s+(\S{8}|\S+)\s+(?:NET .*|SF=([\d.]+) S=([\d.]+) F=([\d.]+) T=([\d.]+) tS=([\d.]+).*?\[(\S*)\]\s*$)', ln)
    if not m:
        continue
    key, aid = m.group(1), m.group(2)
    if 'NET' in ln:
        rec.append({'key': key, 'aid': None, 'net': True})
        continue
    rec.append({'key': key, 'aid': aid, 'SF': float(m.group(3)), 'S': float(m.group(4)),
                'F': float(m.group(5)), 'T': float(m.group(6)), 'tS': float(m.group(7)),
                'tag': m.group(8), 'net': False})

ok = [r for r in rec if not r['net'] and 'ASS' in r.get('tag', '') and 'fail' not in r.get('tag', '')]
fail = [r for r in rec if not r['net'] and r not in ok]
net = [r for r in rec if r['net']]

L = []
L.append('w240 批次结果统计')
L.append('  解析到 %d 行；过闸(PASS) %d 条；未过闸 %d 条；网络失败 %d 条' % (len(rec), len(ok), len(fail), len(net)))

# 已提交的 id（台账）
led = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
sub = set()
if os.path.exists(led):
    for ln in io.open(led, encoding='utf-8-sig'):
        p = ln.strip().split(',')
        if p and p[0].strip() and p[0].strip() != 'id':
            sub.add(p[0].strip())

L.append('\n== 过闸候选（按 SF 降序）==')
L.append('  %-30s %-10s %6s %6s %6s %7s %6s %s' % ('骨架 key', 'alpha id', 'SF', 'S', 'F', 'TO', 'tS', '状态'))
for r in sorted(ok, key=lambda x: -x['SF']):
    mark = '★已提交过' if r['aid'] in sub else ''
    L.append('  %-30s %-10s %6.2f %6.2f %6.2f %7.4f %6.2f %s' % (
        r['key'][:30], r['aid'], r['SF'], r['S'], r['F'], r['T'], r['tS'], mark))

L.append('\n== 未过闸（按 SF 降序，前 20）==')
for r in sorted(fail, key=lambda x: -x['SF'])[:20]:
    L.append('  %-30s %-10s %6.2f %6.2f %6.2f %7.4f %6.2f' % (
        r['key'][:30], r['aid'], r['SF'], r['S'], r['F'], r['T'], r['tS']))

new = [r for r in ok if r['aid'] not in sub]
L.append('\n== 过闸且未提交过：%d 条 ==' % len(new))
L.append('  S>=2.5: %d 条；S 中位 %.2f；F 中位 %.2f；TO 中位 %.4f' % (
    sum(1 for r in new if r['S'] >= 2.5),
    sorted(r['S'] for r in new)[len(new) // 2] if new else 0,
    sorted(r['F'] for r in new)[len(new) // 2] if new else 0,
    sorted(r['T'] for r in new)[len(new) // 2] if new else 0))

uniq_keys = sorted(set(r['key'] for r in new))
L.append('  涉及骨架 %d 个：%s' % (len(uniq_keys), ', '.join(k[:24] for k in uniq_keys)))

io.open('_autologs/_w240_summary.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
