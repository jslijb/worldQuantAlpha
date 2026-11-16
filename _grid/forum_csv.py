# -*- coding: utf-8 -*-
"""导出全量索引 CSV"""
import csv
import json
import os

LGDIR = r'D:\Python\worldquant\_logs'
OUT = r'D:\Python\worldquant\docs\external\论坛全量索引_1513帖.csv'

all_posts = json.load(open(os.path.join(LGDIR, 'forum_posts_full.json'), encoding='utf-8'))
filt = json.load(open(os.path.join(LGDIR, 'forum_filtered.json'), encoding='utf-8'))
sel = json.load(open(os.path.join(LGDIR, 'forum_selected.json'), encoding='utf-8'))

rel = {str(t['id']): t['rel'] for t in filt['tagged']}
CUT15, CUT1Y = '2025-05-15', '2025-11-15'

rows = []
for x in all_posts:
    pid = str(x['id'])
    d = x['created_at'][:10]
    if d < CUT15:
        continue
    rows.append({
        'date': d,
        'id': pid,
        'title': (x.get('title') or '').replace('\n', ' '),
        'votes': x.get('votes') or 0,
        'comments': x.get('comments') or 0,
        'within_1y': 'Y' if d >= CUT1Y else '',
        'kw_class': rel.get(pid, 'drop'),
        'in_curated': ('Y' if pid in sel else ''),
        'sel_src': (sel[pid]['src'] if pid in sel else ''),
        'curated_cats': '/'.join(sorted(set(sel[pid]['cats']))) if pid in sel else '',
        'body_len': len(x.get('details') or ''),
        'url': x.get('url') or '',
    })

rows.sort(key=lambda r: r['date'], reverse=True)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)

print('写入', len(rows), '行 ->', OUT)
print('近1年:', sum(1 for r in rows if r['within_1y'] == 'Y'))
print('索引精选:', sum(1 for r in rows if r['in_curated'] == 'Y'))
print('关键词VF:', sum(1 for r in rows if r['kw_class'] == 'vf'))
print('关键词Alpha:', sum(1 for r in rows if r['kw_class'] == 'alpha'))
