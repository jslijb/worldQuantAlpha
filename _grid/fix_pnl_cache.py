# -*- coding: utf-8 -*-
"""fix_pnl_cache.py —— 修复 PnL 缓存里的「累计值未差分」脏数据

背景
----
GET /alphas/{id}/recordsets/pnl 返回的 records 是【累计 PnL】。
2026-10-15 及之前某版写入代码漏了差分，直接落盘累计值；
2026-11-13 之后的代码是对的（已差分）。

后果
----
累计值直接算 Sharpe 会得到荒谬值（实测 VkdgXYpJ 本地 27.77 / 平台 2.02）。

判据（只用 lag-1 自相关）
------------------------
实测依据（2026-11-15，8920 个缓存全量扫描）：
    正常日 PnL   lag1 ≈ -0.01 ~ +0.03（d5aAQPpv -0.0112 / 58zdrVaM +0.0313）
    累计未差分   lag1 ≈ +0.997 （VkdgXYpJ 0.9977 / vRO3L3eQ 0.9977 / blOwPg0m 0.9979）
两者差一个数量级，阈值取 0.99 即可分开。

⚠ 不能用「单调率」做判据：累计值早期日波动（±2万）相对累计值（前100天中位 19万）仍不小，
  实测单调率只有 0.50~0.55，与随机无异。第一版脚本就是栽在这里，漏判了 3 条已提交 alpha。

双保险
------
差分后必须满足 |lag1_new| < 0.5 才写盘；不满足则跳过并告警（说明判据失效，不是真累计值）。

用法
----
python _grid/fix_pnl_cache.py                  # 只检测（含已提交/未提交分组统计）
python _grid/fix_pnl_cache.py --apply          # 修复全部
python _grid/fix_pnl_cache.py --apply --submitted-only   # 只修已提交的（先验证用）
"""
import json, io, os, sys, math, statistics as st

sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
CACHE = 'data/alpha_quality_analysis/pnl'
SUB = '_logs/submitted_full.json'
APPLY = '--apply' in sys.argv
ONLY_SUB = '--submitted-only' in sys.argv

LAG1_TH = 0.99
LAG1_OK = 0.5      # 差分后 |lag1| 必须低于此值


def lag1(v):
    n = len(v)
    if n < 10:
        return 0.0
    m = st.mean(v)
    num = sum((v[i] - m) * (v[i - 1] - m) for i in range(1, n))
    den = sum((x - m) ** 2 for x in v)
    return num / den if den else 0.0


def mono_rate(v):
    if len(v) < 2:
        return 0.0
    up = sum(1 for i in range(1, len(v)) if v[i] >= v[i - 1])
    return max(up, len(v) - 1 - up) / (len(v) - 1)


SUBIDS = set()
if os.path.exists(SUB):
    SUBIDS = set(x['id'] for x in json.load(io.open(SUB, encoding='utf-8')))
print('已提交名单 %d 条（用于分组统计）' % len(SUBIDS))

files = sorted(os.listdir(CACHE))
print('缓存文件 %d 个' % len(files))

bad = []
ok = 0
err = 0
for fn in files:
    if not fn.endswith('.json'):
        continue
    p = os.path.join(CACHE, fn)
    try:
        s = json.load(io.open(p, encoding='utf-8'))
    except Exception:
        err += 1; continue
    if len(s) < 60:
        continue
    ks = sorted(s.keys())
    v = [s[k] for k in ks]
    l1 = lag1(v)
    if l1 > LAG1_TH:
        bad.append((fn[:-5], l1, mono_rate(v), len(v), sum(v)))
    else:
        ok += 1

in_sub = [b for b in bad if b[0] in SUBIDS]
out_sub = [b for b in bad if b[0] not in SUBIDS]
print('正常（已差分）%d，疑似累计 %d（其中已提交 %d / 未提交 %d），损坏 %d' % (
    ok, len(bad), len(in_sub), len(out_sub), err))

if in_sub:
    print('\n【已提交且疑为累计】%d 条 —— 这些可以用平台 is.sharpe 直接验证' % len(in_sub))
    print('%-12s %8s %8s %6s %14s' % ('alpha_id', 'lag1', '单调率', 'n日', 'sum'))
    for aid, l1, mr, n, sm in sorted(in_sub, key=lambda t: -t[1])[:30]:
        print('%-12s %8.4f %8.4f %6d %14.0f' % (aid, l1, mr, n, sm))

if APPLY:
    target = in_sub if ONLY_SUB else bad
    # 先备份（可回滚：对日值做前缀和即恢复累计值）
    import shutil
    bak = '_logs/replay/pnl_backup'
    os.makedirs(bak, exist_ok=True)
    nb = 0
    for aid, l1, mr, n, sm in target:
        src = os.path.join(CACHE, aid + '.json')
        dst = os.path.join(bak, aid + '.json')
        if not os.path.exists(dst) and os.path.exists(src):
            shutil.copy2(src, dst); nb += 1
    print('\n已备份 %d 个原文件到 %s' % (nb, bak))

    print('开始修复 %d 个文件%s...' % (len(target), '（仅已提交）' if ONLY_SUB else ''))
    fixed = 0
    skipped = []
    for aid, l1, mr, n, sm in target:
        p = os.path.join(CACHE, aid + '.json')
        s = json.load(io.open(p, encoding='utf-8'))
        ks = sorted(s.keys())
        raw = [s[k] for k in ks]
        ser = {ks[i]: raw[i] - raw[i - 1] for i in range(1, len(ks))}
        l1n = lag1([ser[k] for k in sorted(ser)])
        if abs(l1n) > LAG1_OK:
            skipped.append((aid, l1, l1n)); continue
        json.dump(ser, io.open(p, 'w', encoding='utf-8'))
        fixed += 1
    print('已修复 %d 个，跳过 %d 个' % (fixed, len(skipped)))
    if skipped:
        print('  跳过的（差分后 lag1 仍高，判据不适用）：')
        for aid, a, b in skipped[:20]:
            print('    %-12s 修前 %.4f -> 修后 %.4f' % (aid, a, b))
elif bad:
    print('\n（仅检测，未写入。加 --apply 执行修复）')
