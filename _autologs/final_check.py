# -*- coding: utf-8 -*-
"""final_check.py —— 收工检查：修正判决器结果 + 批次产出 + 台账"""
import io, os, re, json, glob, datetime, csv

L = []
ROOT = 'D:/Python/worldquant/'
os.chdir(ROOT)

# 1) 修正判决器的日志（最新 exempt_*.log）
logs = sorted(glob.glob('_autologs/exempt_*.log'), key=os.path.getmtime, reverse=True)
L.append('== 最新判决日志 ==')
for f in logs[:4]:
    st = os.stat(f)
    L.append('  %s  %d bytes  %s' % (f, st.st_size, datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')))
if logs:
    t = io.open(logs[0], encoding='utf-8', errors='replace').read()
    ls = t.splitlines()
    L.append('  --- %s 尾部 ---' % logs[0])
    for x in ls[-6:]:
        L.append('    ' + x[:220])
    # 统计
    cm = [float(x) for x in re.findall(r'corr_max=([\d.]+)', t)]
    star = [x for x in ls if x.strip().startswith('\u2605')]
    pas = [x for x in ls if '\u76f4\u901a\u63d0\u4ea4' in x or 'ACCEPTED' in x]
    L.append('  判决 %d 条；其中 ★(豁免放行)/直通 = %d 条' % (len(cm), len(star) + len(pas)))
    if cm:
        L.append('  corr_max: min=%.4f  中位=%.4f  max=%.4f' % (min(cm), sorted(cm)[len(cm)//2], max(cm)))
        low = sorted(cm)[:8]
        L.append('  最低 8 个 corr_max: ' + ', '.join('%.4f' % v for v in low))
    for x in (star + pas)[:10]:
        L.append('  ★ ' + x[:220])

# 2) 批次产出
OUT = 'data/alpha_quality_analysis/mined'
L.append('')
L.append('== 批次进度 ==')
for tag in ['w239', 'w240', 'w241', 'w242', 'w243']:
    cf = '_autologs/leg_combos_%s.json' % tag
    if not os.path.exists(cf):
        continue
    c = json.load(io.open(cf, encoding='utf-8'))
    done = sum(1 for cid in c if os.path.exists('%s/%s.json' % (OUT, cid)))
    L.append('  %s: %d/%d' % (tag, done, len(c)))

L.append('')
L.append('== mined 最新 12 个产出 ==')
fs = sorted([(os.path.getmtime(OUT + '/' + x), x) for x in os.listdir(OUT)], reverse=True)[:12]
for m, x in fs:
    L.append('  %s  %s' % (datetime.datetime.fromtimestamp(m).strftime('%m-%d %H:%M:%S'), x))

# 3) 台账
rows = []
with io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig', newline='') as f:
    rd = csv.reader(f); next(rd)
    for r in rd:
        if r and r[0].strip():
            rows.append(r)
ids = []
for r in rows:
    if r[0] not in ids:
        ids.append(r[0])
L.append('')
L.append('== 台账 ==')
L.append('  行数 %d  唯一 id %d' % (len(rows), len(ids)))
today = [r for r in rows if len(r) > 8 and '2026-09-20' in r[8]]
L.append('  美东 2026-09-20 提交行数 %d（去重 %d）' % (len(today), len(set(r[0] for r in today))))
S = []
for r in rows:
    try:
        S.append(float(r[2]))
    except Exception:
        pass
if S:
    L.append('  S 中位 %.2f 均值 %.2f max %.2f' % (sorted(S)[len(S)//2], sum(S)/len(S), max(S)))

io.open('_autologs/_final_check.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
