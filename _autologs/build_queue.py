# -*- coding: utf-8 -*-
"""build_queue.py —— 汇总 _judge_now.txt 最近 N 个块 → 生成可用队列 QUEUE.md
门：tS>=1.25 且 TO<=0.20 且无 FAIL（直通或豁免过）。按 F 降序。
用法：python build_queue.py [N=9]
"""
import io, re, sys, os, time
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
os.chdir(ROOT)
txt = io.open(ROOT / '_autologs/_judge_now.txt', encoding='utf-8').read()
blocks = [b for b in txt.split('==== ') if b.strip()]
n = int(sys.argv[1]) if len(sys.argv) > 1 else 9
recs = {}
heads = []
for b in blocks[-n:]:
    heads.append(b.splitlines()[0])
    cur = None
    for ln in b.splitlines()[1:]:
        m = re.match(r'^---- (\w{8}) ----', ln)
        if m:
            cur = {'id': m.group(1)}
            continue
        if cur is None:
            continue
        m = re.search(r'S=([\d.]+) F=([\d.]+) TO=([\d.]+) tS=(\S+) FAIL=(\S*)', ln)
        if m:
            cur.update(S=float(m.group(1)), F=float(m.group(2)), TO=float(m.group(3)),
                       tS=float(m.group(4)) if m.group(4) not in ('None', '-') else -9,
                       FAIL=m.group(5))
        if 'corr=' in ln and 'corr_max' not in cur:
            cur['corr_max'] = float(re.search(r'corr=([\d.]+)', ln).group(1))
        if '直通' in ln:
            cur['verdict'] = '直通'
        m = re.search(r'gap = ([\+\-][\d.]+)', ln)
        if m:
            cur['gap'] = float(m.group(1))
        if cur.get('verdict'):
            recs[cur['id']] = cur  # 后块覆盖前块
clean, backup = [], []
for r in recs.values():
    passed = r.get('verdict') == '直通' or (r.get('gap') is not None and r['gap'] <= 0)
    if not passed:
        continue
    ok = r.get('tS', -9) >= 1.25 and r.get('TO', 9) <= 0.20 and r.get('FAIL', '') in ('', '[]')
    (clean if ok else backup).append(r)
clean.sort(key=lambda r: -r['F'])
backup.sort(key=lambda r: -r['F'])
L = []
L.append('# 可用候选队列（%s 生成，池 114）' % time.strftime('%m-%d %H:%M'))
L.append('')
L.append('来源块：%s' % ' | '.join(h.split('====')[0].strip() for h in heads))
L.append('')
L.append('**三条使用铁律**')
L.append('1. **提交当天必须重判**（`judge_now.py <id>`）：本表 corr 基于 PnL 113/114 的池子，当天新入池的 alpha 未进矩阵，need 时变。')
L.append('2. **同日提 2 条前必跑 `pair_now.py <id1> <id2>`**，corr >0.66 的两条只能提一条（一池一家族一口）。')
L.append('3. 顺序按 F 降序；保底优先第 1 条，加交条件 = 候选 F > 当天已交均值。')
L.append('')
L.append('## A. 过全部质量闸（tS>=1.25 + TO<=20%% + 无 FAIL）：%d 条' % len(clean))
L.append('')
L.append('| # | id | S | F | TO | tS | corr_max | 备注 |')
L.append('|---|---|---|---|---|---|---|---|')
for i, r in enumerate(clean, 1):
    L.append('| %d | `%s` | %.2f | %.2f | %.1f%% | %.2f | %.4f | |' % (
        i, r['id'], r['S'], r['F'], r['TO'] * 100, r['tS'], r.get('corr_max', 0)))
L.append('')
L.append('## B. 直通但破质量闸（备胎，按 F 降序）：%d 条' % len(backup))
L.append('')
L.append('| # | id | S | F | TO | tS | corr_max | 破哪条 |')
L.append('|---|---|---|---|---|---|---|---|')
for i, r in enumerate(backup, 1):
    why = []
    if r.get('tS', -9) < 1.25:
        why.append('tS%.2f' % r['tS'])
    if r.get('TO', 9) > 0.20:
        why.append('TO%.0f%%' % (r['TO'] * 100))
    if r.get('FAIL'):
        why.append('FAIL')
    L.append('| %d | `%s` | %.2f | %.2f | %.1f%% | %.2f | %.4f | %s |' % (
        i, r['id'], r['S'], r['F'], r['TO'] * 100, r['tS'], r.get('corr_max', 0), ','.join(why)))
rep = '\n'.join(L)
io.open(ROOT / '_autologs/QUEUE.md', 'w', encoding='utf-8').write(rep)
print('A 队 %d 条 / B 队 %d 条 -> _autologs/QUEUE.md' % (len(clean), len(backup)))
for r in clean[:8]:
    print('  A %-10s F=%.2f tS=%.2f TO=%.0f%% corr=%.4f' % (r['id'], r['F'], r['tS'], r['TO'] * 100, r.get('corr_max', 0)))
