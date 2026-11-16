# -*- coding: utf-8 -*-
"""论坛帖子离线查询工具
用法:
  python _grid/forum_show.py 43751636849047          # 按 ID 打全文
  python _grid/forum_show.py --grep "Osmosis 分配"     # 全库搜正文
  python _grid/forum_show.py --grep "value factor" --since 2025-11-15 --limit 20
  python _grid/forum_show.py --list vf --top 30       # 列 VF 类高票帖
"""
import argparse
import json
import os
import re
import sys

LGDIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '_logs')
FULL = os.path.join(LGDIR, 'forum_posts_full.json')

TAG = re.compile(r'<[^>]+>')


def plain(h):
    if not h:
        return ''
    s = re.sub(r'<br\s*/?>', '\n', h, flags=re.I)
    s = re.sub(r'</(p|div|li|tr|h[1-6]|blockquote)>', '\n', s, flags=re.I)
    s = TAG.sub('', s)
    for a, b in [('&nbsp;', ' '), ('&amp;', '&'), ('&lt;', '<'), ('&gt;', '>'),
                 ('&quot;', '"'), ('&#39;', "'"), ('&hellip;', '…')]:
        s = s.replace(a, b)
    return re.sub(r'\n{3,}', '\n\n', s).strip()


def load():
    if not os.path.exists(FULL):
        sys.exit('缺 %s，先跑 _grid/forum_full.py' % FULL)
    return json.load(open(FULL, encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('pid', nargs='?', help='帖子 ID')
    ap.add_argument('--grep', help='在标题+正文里搜关键词')
    ap.add_argument('--since', default='2025-05-15', help='起始日期，默认 2025-05-15')
    ap.add_argument('--limit', type=int, default=10)
    ap.add_argument('--chars', type=int, default=0, help='每帖正文截断字符数，0=全文')
    ap.add_argument('--list', help='按关键词分类列帖（vf / alpha）')
    ap.add_argument('--top', type=int, default=30, help='--list 时按票数取前 N')
    a = ap.parse_args()

    ps = load()
    by = {str(x['id']): x for x in ps}

    if a.pid:
        p = by.get(str(a.pid))
        if not p:
            sys.exit('没找到 %s' % a.pid)
        body = plain(p.get('details'))
        print('ID      :', p['id'])
        print('标题    :', p.get('title'))
        print('时间    :', p['created_at'][:19], '| 票', p.get('votes'), '| 评论', p.get('comments'))
        print('作者    :', p.get('author') or '-')
        print('长度    :', len(body))
        print('=' * 90)
        print(body[:a.chars] if a.chars else body)
        return

    if a.list:
        filt = json.load(open(os.path.join(LGDIR, 'forum_filtered.json'), encoding='utf-8'))
        rel = {str(t['id']): t for t in filt['tagged']}
        rows = [(int(p.get('votes') or 0), str(p['id'])) for p in ps
                if rel.get(str(p['id']), {}).get('rel') == a.list
                and p['created_at'][:10] >= a.since]
        rows.sort(reverse=True)
        for v, pid in rows[:a.top]:
            p = by[pid]
            print('%3d票 %3d评 %s | %s | %s' % (v, p.get('comments') or 0,
                                                p['created_at'][:10], pid,
                                                (p.get('title') or '')[:66]))
        print('--- 共 %d 条匹配' % len(rows))
        return

    if a.grep:
        kw = a.grep.lower()
        hits = []
        for p in ps:
            if p['created_at'][:10] < a.since:
                continue
            body = plain(p.get('details'))
            blob = ((p.get('title') or '') + '\n' + body).lower()
            if kw not in blob:
                continue
            n = blob.count(kw)
            hits.append((n, int(p.get('votes') or 0), str(p['id']), p, body))
        hits.sort(key=lambda x: (-x[0], -x[1]))
        print('命中 %d 篇（关键词 %r，since %s）' % (len(hits), a.grep, a.since))
        for n, v, pid, p, body in hits[:a.limit]:
            print('')
            print('=' * 90)
            print('%s | %s | %d票 | 命中%d次 | %s' % (p['created_at'][:10], pid, v, n,
                                                      (p.get('title') or '')[:60]))
            # 打印关键词附近片段
            low = body.lower()
            idx = low.find(kw)
            s = max(0, idx - 160)
            seg = body[s:idx + 240].replace('\n', ' ')
            print('  …%s…' % seg)
        return

    ap.print_help()


if __name__ == '__main__':
    main()
