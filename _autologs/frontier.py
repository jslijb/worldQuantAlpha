# -*- coding: utf-8 -*-
"""frontier.py —— 解析 submit_exempt 干跑日志，量化"离直通线还差多少"
输出：corr_max 分布 + 按可救性分档（假设中性化换挡 -0.09）
"""
import re, io, json, os

LOG = '_autologs/_dry3_latest.txt'
rows = []
pat = re.compile(r'^\s*[✗★✓]\s+(\S+)\s+(\S+)\s+SF=([\d.]+)(?:\s+S=([\d.]+)\s+corr_max=([\d.]+))?')
for ln in io.open(LOG, encoding='utf-8').read().splitlines():
    m = pat.match(ln)
    if not m:
        continue
    aid, cid, sf, S, cm = m.groups()
    to = None
    md = re.search(r'TO=\s*([\d.]+)%', ln)
    need = re.search(r'需≥([\d.]+)', ln)
    rows.append(dict(aid=aid, cid=cid, SF=float(sf), S=float(S) if S else None,
                     corr=float(cm) if cm else None,
                     need=float(need.group(1)) if need else None))

# 补 TO / F：从 mined 里读
DIRECT = 0.685
for r in rows:
    p = f'data/alpha_quality_analysis/mined/{r["cid"]}.json'
    if os.path.exists(p):
        try:
            d = json.load(io.open(p, encoding='utf-8'))
            i = d.get('is') or {}
            r['TO'] = i.get('turnover') or 0
            r['F'] = i.get('fitness') or 0
            r['decay'] = d.get('_decay'); r['neut'] = d.get('_neut')
        except Exception:
            pass

L = []
L.append(f'判决总数 {len(rows)}（达标池）')
band = {}
for r in rows:
    if r['corr'] is None:
        band.setdefault('直通(<0.66)', []).append(r); continue
    c = r['corr']
    if c < 0.66:
        k = '直通(<0.66)'
    elif c < 0.685:
        k = '0.66~0.685(近直通)'
    elif c < 0.78:
        k = '0.685~0.78(中性化换挡可能救回)'
    elif c < 0.90:
        k = '0.78~0.90(需大改)'
    else:
        k = '>=0.90(重做)'
    band.setdefault(k, []).append(r)

for k in ['直通(<0.66)', '0.66~0.685(近直通)', '0.685~0.78(中性化换挡可能救回)',
          '0.78~0.90(需大改)', '>=0.90(重做)']:
    v = band.get(k, [])
    L.append(f'\n【{k}】{len(v)} 条')
    v.sort(key=lambda r: -(r.get('F') or 0))
    for r in v[:25]:
        L.append('  %-24s S=%s F=%.2f TO=%s%% corr=%s decay=%s neut=%s'
                 % (r['cid'], ('%.2f' % r['S']) if r['S'] else 'NA', r.get('F', 0),
                    ('%.1f' % ((r.get('TO') or 0) * 100)), r['corr'], r.get('decay'), r.get('neut')))

io.open('_autologs/_frontier.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('rows', len(rows))
