# -*- coding: utf-8 -*-
"""acct_counts.py —— 账号 alpha 计数 + 排行榜五数（count 口径，不数翻页）

⚠ 本机顽固坑：`/users/self/alphas` 的 offset 硬上限 1000，超了报 400。
   正确做法 = 读响应里的 `count` 字段 + 用过滤器切分，**绝不要靠翻页累加**。
   （0916 与 0920 各踩过一次：把"翻不动"当成"账号只有这么多"。）
"""
import os, json, io, time, requests

os.chdir('D:/Python/worldquant')
s = requests.Session()
s.auth = tuple(json.load(open('brain_credentials.txt')))
for _a in range(6):
    try:
        if s.post('https://api.worldquantbrain.com/authentication', timeout=60).status_code == 201:
            break
    except Exception:
        time.sleep(3)

L = []
BASE = 'https://api.worldquantbrain.com/users/self/alphas'


def cnt(**params):
    p = {'limit': 1}
    p.update(params)
    for _a in range(5):
        try:
            r = s.get(BASE, params=p, timeout=60)
        except Exception:
            time.sleep(3); continue
        if r.status_code != 200:
            return 'HTTP%d' % r.status_code
        return r.json().get('count')
    return 'ERR'


L.append('== 账号 alpha 计数（count 口径）==')
L.append('  全部          = %s' % cnt())
L.append('  stage=OS      = %s   <- 已入池（提交成功）' % cnt(stage='OS'))
L.append('  stage=IS      = %s' % cnt(stage='IS'))
L.append('  UNSUBMITTED   = %s   <- 待提交' % cnt(status='UNSUBMITTED'))
L.append('  ACTIVE        = %s' % cnt(status='ACTIVE'))
L.append('')
L.append('  按 universe 切（待提交池）：')
# ⚠ 0922 修：`universe=` 不是平台认的过滤器名（五个池会返回同一个全量值，曾误导判断）。
#   平台过滤器用 `settings.universe`；若仍无区分度则降级读本地快照统计。
UNIS = ('TOP3000', 'TOP2000', 'TOP1000', 'TOP500', 'TOP200')
res = {}
for u in UNIS:
    res[u] = cnt(status='UNSUBMITTED', **{'settings.universe': u})
nums = [v for v in res.values() if isinstance(v, int)]
if not nums or len(set(nums)) <= 1:
    L.append('    ⚠ 平台不支持按 universe 过滤（返回同一值 %s），以下为本地快照统计：'
             % (nums[0] if nums else 'N/A'))
    try:
        import collections
        D = json.load(io.open('data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json',
                              encoding='utf-8'))
        if isinstance(D, dict):
            D = D.get('results', [])
        c = collections.Counter((a.get('settings') or {}).get('universe') for a in D)
        for k, v in c.most_common():
            L.append('    %-9s = %s' % (k, v))
        L.append('    （本地快照共 %d 条，会随拉取时间过期）' % len(D))
    except Exception as e:
        L.append('    本地快照读取失败: %s' % e)
else:
    for u in UNIS:
        L.append('    %-9s = %s' % (u, res[u]))

r = s.get('https://api.worldquantbrain.com/competitions/challenge', timeout=60)
if r.status_code == 200:
    lb = (r.json().get('leaderboard') or {})
    L.append('')
    L.append('== 排行榜（competitions/challenge）==')
    for k in ('rank', 'score', 'isScore', 'daysOfSubmission', 'uniquenessScore'):
        L.append('  %-18s = %s' % (k, lb.get(k)))
else:
    L.append('排行榜 HTTP %d' % r.status_code)

io.open('_autologs/_acct.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
