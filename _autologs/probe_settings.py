# -*- coding: utf-8 -*-
"""probe_settings.py —— 从 mined 产出里统计 settings(universe/delay/decay/neutralization/truncation) 分布（自写 UTF-8）"""
import io, json, os, collections

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined'
L = []

keys = ['universe', 'delay', 'decay', 'neutralization', 'truncation', 'region', 'pasteurization', 'nanHandling', 'instrumentType', 'language', 'unitHandling', 'maxTrade', 'maxPosition']
cnt = {k: collections.Counter() for k in keys}
n = 0
samples = {}
for x in sorted(os.listdir(MINED)):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MINED, x), encoding='utf-8'))
    except Exception:
        continue
    s = d.get('settings') or {}
    if not s:
        # 也许平铺在顶层
        s = {k: d.get(k) for k in keys if k in d}
    if not s:
        continue
    n += 1
    for k in keys:
        v = s.get(k)
        if v is not None:
            cnt[k][str(v)] += 1
    if len(samples) < 3:
        samples[x] = s

L.append('可读到 settings 的 mined 文件数: %d' % n)
L.append('')
for k in keys:
    if cnt[k]:
        L.append('%s:' % k)
        for v, c in cnt[k].most_common(8):
            L.append('    %-28s %d' % (v, c))
    else:
        L.append('%s: (无)' % k)

L.append('')
L.append('== 样本 settings ==')
for k, v in samples.items():
    L.append('  %s -> %s' % (k, json.dumps(v, ensure_ascii=False)[:500]))

# 顶层有哪些字段
if samples:
    first = list(samples)[0]
    d = json.load(io.open(os.path.join(MINED, first), encoding='utf-8'))
    L.append('')
    L.append('== mined json 顶层字段 (%s) ==' % first)
    L.append('  ' + ', '.join(sorted(d.keys())))

io.open(ROOT + '_autologs/_settings_probe.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
