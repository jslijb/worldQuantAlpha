# -*- coding: utf-8 -*-
"""parse_judge.py —— 解析 _judge_now.txt 最后 N 个块，给出可过/失效清单
用法：python parse_judge.py [N]
输出同时写 _autologs/_parse_judge.txt
"""
import io, re, sys, os
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
os.chdir(ROOT)
txt = io.open(ROOT / '_autologs/_judge_now.txt', encoding='utf-8').read()
blocks = [b for b in txt.split('==== ') if b.strip()]
n = int(sys.argv[1]) if len(sys.argv) > 1 else 1
out = []
lines = []
merged = blocks[-n:]
for b in merged:
    out.append('块头: ' + b.splitlines()[0])
# 合并最后 n 个块（可能因并发跑成多块）
alllines = []
for b in merged:
    alllines += b.splitlines()[1:]
lines = alllines
recs, cur = [], None
for ln in lines:
    m = re.match(r'^---- (\w{8}) ----', ln)
    if m:
        if cur:
            recs.append(cur)
        newid = m.group(1)
        cur = None if any(r['id'] == newid for r in recs) else {'id': newid}
        continue
    if cur is None:
        continue
    m = re.search(r'S=([\d.]+) F=([\d.]+) TO=([\d.]+) tS=(\S+) FAIL=(\S*)', ln)
    if m:
        cur.update(S=float(m.group(1)), F=float(m.group(2)), TO=float(m.group(3)), tS=m.group(4), FAIL=m.group(5))
    if 'corr=' in ln and 'corr_max' not in cur:
        cur['corr_max'] = float(re.search(r'corr=([\d.]+)', ln).group(1))
    m = re.search(r'need=1\.10x[\d.]+=([\d.]+)', ln)
    if m:
        cur['need'] = float(m.group(1))
    if '直通' in ln:
        cur['verdict'] = '直通'
    m = re.search(r'gap = ([\+\-][\d.]+)', ln)
    if m:
        cur['gap'] = float(m.group(1))
if cur:
    recs.append(cur)


def passes(r):
    if r.get('verdict') == '直通':
        return True
    return r.get('gap') is not None and r['gap'] <= 0


ok = [r for r in recs if passes(r)]
bad = [r for r in recs if not passes(r)]
out.append('总判 %d 条，仍可过 %d 条' % (len(recs), len(ok)))
ok.sort(key=lambda r: -r.get('F', 0))
for r in ok:
    out.append('PASS %-10s S=%.2f F=%.2f TO=%.3f tS=%s corr_max=%s need=%s gap=%s' % (
        r['id'], r.get('S', 0), r.get('F', 0), r.get('TO', 0), r.get('tS'), r.get('corr_max'), r.get('need'), r.get('gap')))
out.append('---- 失效，按 corr_max 升序（离墙最近的在前）----')
bad.sort(key=lambda r: r.get('corr_max') or 9)
for r in bad[:25]:
    out.append('DEAD %-10s S=%.2f F=%.2f tS=%s corr_max=%s need=%s gap=%s' % (
        r['id'], r.get('S', 0), r.get('F', 0), r.get('tS'), r.get('corr_max'), r.get('need'), r.get('gap')))
rep = '\n'.join(out)
print(rep)
io.open(ROOT / '_autologs/_parse_judge.txt', 'w', encoding='utf-8').write(rep)
