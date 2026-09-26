# -*- coding: utf-8 -*-
"""live_watch.py —— 后台进程存活 + 批次进度 + 实时判决最新结论"""
import io, os, re, json, datetime, subprocess

L = []

# 1) 相关进程
try:
    out = subprocess.check_output(
        ['wmic', 'process', 'where', "name like '%python%'", 'get', 'ProcessId,CommandLine'],
        stderr=subprocess.STDOUT).decode('gbk', 'ignore')
except Exception as e:
    out = '(wmic 失败 %s)' % e
L.append('== python 进程 ==')
for ln in out.splitlines():
    ln = ln.strip()
    if not ln or ln.startswith('CommandLine'):
        continue
    if '_autologs' in ln or 'mine' in ln or 'submit' in ln or 'leg' in ln:
        L.append('  ' + ln[:220])

# 2) 实时判决日志规模
for f in ['_autologs/_exempt_live.txt', '_autologs/_exempt_dry_run.txt']:
    if os.path.exists(f):
        st = os.stat(f)
        L.append('')
        L.append('%s : %d bytes, mtime %s' % (f, st.st_size,
                 datetime.datetime.fromtimestamp(st.st_mtime).strftime('%m-%d %H:%M:%S')))

# 3) 批次进度
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

# 4) 运行日志尾部
L.append('')
L.append('== 运行日志尾部（最后 3 行非空）==')
for tag in ['w239', 'w240', 'w241', 'w242', 'w243']:
    for cand in ['_autologs/_%s_run2.txt' % tag, '_autologs/_%s_run.txt' % tag]:
        if not os.path.exists(cand):
            continue
        raw = io.open(cand, 'rb').read()
        t = None
        for enc in ('utf-8', 'utf-16', 'gbk'):
            try:
                t = raw.decode(enc)
                break
            except Exception:
                pass
        if t is None:
            continue
        ls = [x for x in t.splitlines() if x.strip()]
        L.append('  --- %s ---' % os.path.basename(cand))
        for x in ls[-3:]:
            L.append('    ' + x[:200])
        break

io.open('_autologs/_live_watch.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
