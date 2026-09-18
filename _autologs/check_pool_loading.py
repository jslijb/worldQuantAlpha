# -*- coding: utf-8 -*-
"""排查 leg_lab 池子装载：台账 86 条是否全部进了池子，缓存时间 vs 搜索时间"""
import os, csv, json, time
os.chdir(r'D:\Python\worldquant')
out = []

# 台账 id
led = [r[0] for r in csv.reader(open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig')) if r and r[0] and len(r[0]) == 8]
out.append('ledger ids: %d' % len(led))

# PnL 缓存覆盖与时间
pc = 'data/alpha_quality_analysis/pnl'
cache = {}
for f in os.listdir(pc):
    if f.endswith('.json'):
        cache[f[:-5]] = os.path.getmtime(os.path.join(pc, f))
out.append('cache files: %d' % len(cache))

missing = [a for a in led if a not in cache]
out.append('pool members missing from cache: %s' % (missing if missing else 'NONE'))

# 关键撞点的缓存写入时间 vs 今日搜索开始时间（w197 搜索约 0918 20:20 前后启动）
# 用文件时间判断搜索时缓存是否已存在
import datetime
for aid in ['pwRwWoJ3', 'LLNL3qqm', 'vRjG1Jzw', 'YP57jVzo', 'YPbLZK2W', 'O0N0R5NY', 'MPaPe0oo', '9qjqm3Q9', 'rY07MXgd']:
    if aid in cache:
        ts = datetime.datetime.fromtimestamp(cache[aid]).strftime('%m-%d %H:%M')
        out.append('%s cached_at %s' % (aid, ts))
    else:
        out.append('%s NOT IN CACHE' % aid)

# 搜索日志的时间戳（第一个锚启动时间）
for lg in ['search_w196.log', 'search_w197a.log', 'search_w198.log']:
    p = '_autologs/' + lg
    if os.path.exists(p):
        out.append('%s mtime %s' % (lg, datetime.datetime.fromtimestamp(os.path.getmtime(p)).strftime('%m-%d %H:%M')))

open('_autologs/r8.txt', 'w', encoding='utf-8').write('\n'.join(out))
