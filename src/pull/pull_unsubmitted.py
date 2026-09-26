# -*- coding: utf-8 -*-
"""pull_unsubmitted.py —— 递归分片拉取账号全部 UNSUBMITTED alpha

为什么需要它：
  `GET /users/self/alphas` 的 **offset 硬上限是 1000**（超了报
  "Cannot display more than the first 1,000 alphas. Apply filters to narrow results."），
  但响应里一直带 `count` 字段 —— 总数看 count，不要看"翻了多深"。
  本人 0920 曾把"翻到 1100 就 400"误读成"账号只有 1100 条"，实际 count = 3652。

本脚本：用 dateCreated 天级区间递归细分，保证每片 count <= 900，再 offset 分页拉全。
输出：
  data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json   全部原始条目
  _autologs/_pull_summary.txt                                     分片与统计摘要
"""
import os, io, json, time, datetime, requests

os.chdir('D:/Python/worldquant')
OUTDIR = 'data/alpha_quality_analysis/raw_from_api/'
os.makedirs(OUTDIR, exist_ok=True)

s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
assert s.post('https://api.worldquantbrain.com/authentication').status_code == 201

U = 'https://api.worldquantbrain.com/users/self/alphas'
LIMIT = 100          # 平台硬上限，传 500/1000 也只回 100
SLICE_MAX = 900      # 每片目标上限，留出余量
LOG = []
CALLS = [0]

def get(qs, limit, offset):
    url = U + '?' + qs + '&limit=%d&offset=%d' % (limit, offset)
    for attempt in range(5):
        try:
            r = s.get(url, timeout=60)
        except Exception as e:
            time.sleep(3)
            continue
        CALLS[0] += 1
        if r.status_code == 200:
            return r.json()
        if r.status_code == 429:
            time.sleep(6 * (attempt + 1))
            continue
        LOG.append('HTTP %s on %s :: %s' % (r.status_code, url[:150], r.text[:80].replace('\n', ' ')))
        return None
    return None

def cnt(qs):
    j = get(qs, 1, 0)
    return (j or {}).get('count', -1)

def day_qs(d):
    nxt = d + datetime.timedelta(days=1)
    return ('dateCreated%3E%3D' + d.strftime('%Y-%m-%dT00:00:00-04:00')
            + '&dateCreated%3C' + nxt.strftime('%Y-%m-%dT00:00:00-04:00'))

def pull(qs, depth=0, tag=''):
    c = cnt(qs)
    if c <= 0:
        return []
    if c <= SLICE_MAX:
        out = []
        for off in range(0, c, LIMIT):
            j = get(qs, LIMIT, off)
            if not j:
                break
            out += j.get('results') or []
            time.sleep(0.25)
        LOG.append('%-34s count=%-5d 取到 %d' % (tag or qs[:30], c, len(out)))
        return out
    if depth >= 3:
        LOG.append('!! 无法细分 %s count=%d' % (tag or qs[:30], c))
        return []
    # 细分：按天
    acc = []
    d = datetime.date(2026, 8, 1)
    end = datetime.date(2026, 9, 23)
    while d < end:
        sub = qs + '&' + day_qs(d)
        acc += pull(sub, depth + 1, d.strftime('%m-%d'))
        d += datetime.timedelta(days=1)
    return acc

BASE = 'status=UNSUBMITTED'
LOG.append('== 基线计数 ==')
LOG.append('  count(UNSUBMITTED) = %d' % cnt(BASE))
LOG.append('  count(全部)        = %d' % cnt(''))

LOG.append('')
LOG.append('== 分片拉取 ==')
rows = pull(BASE)

# 去重
seen = {}
for a in rows:
    if a.get('id'):
        seen[a['id']] = a
LOG.append('')
LOG.append('拉取条目 %d，唯一 id %d' % (len(rows), len(seen)))

json.dump(list(seen.values()), io.open(OUTDIR + 'all_unsubmitted.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
LOG.append('已写出 %sall_unsubmitted.json' % OUTDIR)
LOG.append('API 调用 %d 次' % CALLS[0])

io.open('_autologs/_pull_summary.txt', 'w', encoding='utf-8').write('\n'.join(LOG))
print('ok rows=%d uniq=%d calls=%d' % (len(rows), len(seen), CALLS[0]))
