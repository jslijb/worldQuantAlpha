# -*- coding: utf-8 -*-
"""蓝海字段筛选器（按论坛置顶帖 ATOM 的算法）

帖子原文（第 85 行）：
  "真正的无人区蓝海在哪里？在于按 onboard 时间（dateCreated）由近到远（降序）排列，
   再结合 alphaCount 由低到高（升序）筛选出来的『最新上线字段』"
帖子第 180 行补充门槛：
  "优先锁定最近 1~3 个月新 onboard、覆盖率 >= 80% 且 Pyramid 倍率在 1.2x 以上"

用法：
  python _grid/bluesea.py list --top 40
  python _grid/bluesea.py fields --per-ds 1 --max 12      # 每个数据集取最新 1 个，共 12 个
  python _grid/bluesea.py build --max 12 --out _autologs/_atom_batch.json
"""
import json, io, sys, os, datetime, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
META = os.path.join(ROOT, 'data', 'alpha_quality_analysis', 'fields_usa_meta.json')

COV_MIN = 0.80        # 帖子：覆盖率 >= 80%
PYR_MIN = 1.2         # 帖子：Pyramid 倍率 >= 1.2x
NEVER_USED_MAX = 50   # alphaCount 上限（帖子没给硬数，这里只排除已被大量使用的）


def load():
    if not os.path.exists(META):
        sys.exit('缺 %s，先跑 _autologs/_pull_bluesea_full.py' % META)
    d = json.load(io.open(META, encoding='utf-8'))
    out = []
    for o in d:
        ds = o.get('dataset')
        ds = ds.get('id') if isinstance(ds, dict) else ds
        try:
            cov = float(o.get('coverage') or 0)
        except Exception:
            cov = 0.0
        try:
            pyr = float(o.get('pyramidMultiplier') or 0)
        except Exception:
            pyr = 0.0
        out.append({
            'id': o.get('id'),
            'dataset': ds,
            'category': (o.get('category') or {}).get('id') if isinstance(o.get('category'), dict) else o.get('category'),
            'type': o.get('type'),
            'dateCreated': o.get('dateCreated') or '',
            'coverage': cov,
            'alphaCount': int(o.get('alphaCount') or 0),
            'pyramid': pyr,
            'desc': (o.get('description') or '')[:70],
        })
    return out


def bluesea(rows, cov_min=COV_MIN, pyr_min=PYR_MIN, ac_max=NEVER_USED_MAX):
    sel = [r for r in rows
           if r['coverage'] >= cov_min and r['pyramid'] >= pyr_min
           and r['alphaCount'] <= ac_max and r['type'] == 'MATRIX' and r['id']]
    # 帖子算法：dateCreated 降序（最新优先） + alphaCount 升序（用得最少优先）
    # 坑（11-15 修正）：不能写成 sort(key=(date, -ac), reverse=True) —— reverse 会把
    # -alphaCount 一起倒过来，变成 alphaCount 大的排前面，与帖子要求正好相反。
    # 用两次稳定排序：先按 alphaCount 升序，再按 dateCreated 降序。
    sel.sort(key=lambda r: r['alphaCount'])
    sel.sort(key=lambda r: r['dateCreated'], reverse=True)
    return sel


def pick_diverse(sel, per_ds=1, maxn=12):
    """每个数据集最多取 per_ds 个，保证跨数据集分散（避免同族挤在一起）"""
    cnt = collections.Counter()
    out = []
    for r in sel:
        if cnt[r['dataset']] >= per_ds:
            continue
        out.append(r)
        cnt[r['dataset']] += 1
        if len(out) >= maxn:
            break
    return out


# 论坛帖的 4 个模板；T1/T4 原版用 group_rank（李工 11-15 起禁用 10 天），改用 group_neutralize 保留行业中性语义
TPL = {
    'T1b': ('长短均值比_替换', 'group_neutralize(ts_mean({field},20)/ts_mean({field},120)-1, subindustry)'),
    'T2':  ('时序标准化中性',   'group_neutralize(ts_zscore({field},60), subindustry)'),
    'T3':  ('一年分位反转',     'ts_decay_linear(-ts_rank({field},252), 10)'),
    'T4b': ('信噪比差分_替换',   'group_neutralize(ts_delta({field},20)/ts_std_dev({field},60), industry)'),
}


def build(rows, per_ds=1, maxn=12, tpls=None, dataset_only=None):
    sel = pick_diverse(bluesea(rows), per_ds=per_ds, maxn=maxn)
    if dataset_only:
        sel = [r for r in sel if r['dataset'] in dataset_only]
    tpls = tpls or ['T2', 'T3']
    sys.path.insert(0, HERE)
    from op_ban import is_banned
    out = []
    for r in sel:
        for k in tpls:
            name, t = TPL[k]
            code = t.format(field=r['id'])
            if is_banned(code):
                continue
            out.append({
                'cid': 'ATOM_%s_%s' % (r['id'][:22], k),
                'code': code,
                'dataset': r['dataset'],
                'idea_id': 'ATOM_%s' % name,
                'shell': k,
                'fields': [r['id']],
                'settings': {'region': 'USA', 'delay': 1, 'universe': 'TOP3000',
                             'neutralization': 'SUBINDUSTRY', 'decay': 6, 'truncation': 0.08},
            })
    return out, sel


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else 'list'
    def arg(k, d=None):
        return a[a.index(k) + 1] if k in a else d
    rows = load()
    print('字段元数据 %d 条（已过滤前）' % len(rows), flush=True)
    sel = bluesea(rows)
    print('过 coverage>=%.2f / pyramid>=%.1fx / alphaCount<=%d 的：%d 条'
          % (COV_MIN, PYR_MIN, NEVER_USED_MAX, len(sel)), flush=True)
    print('涉及数据集 %d 个' % len({r['dataset'] for r in sel}), flush=True)
    print()

    if cmd == 'list':
        n = int(arg('--top', 40))
        print('%-34s %-14s %-11s %7s %6s %5s' % ('字段', '数据集', '上线时间', '覆盖率', '已用', '倍率'))
        for r in sel[:n]:
            print('%-34s %-14s %-11s %7.3f %6d %5.1fx'
                  % (r['id'][:34], str(r['dataset'])[:14], r['dateCreated'][:10],
                     r['coverage'], r['alphaCount'], r['pyramid']))
        return

    if cmd == 'fields':
        per = int(arg('--per-ds', 1)); mx = int(arg('--max', 12))
        pick = pick_diverse(sel, per, mx)
        print('每个数据集取 %d 个、共 %d 个：' % (per, len(pick)))
        for r in pick:
            print('  %-34s %-14s %s  cov=%.3f  used=%d  %s'
                  % (r['id'][:34], str(r['dataset'])[:14], r['dateCreated'][:10],
                     r['coverage'], r['alphaCount'], r['desc'][:36]))
        return

    if cmd == 'build':
        mx = int(arg('--max', 12)); per = int(arg('--per-ds', 1))
        tpls = (arg('--tpls', 'T2,T3')).split(',')
        out_p = arg('--out', os.path.join(ROOT, '_autologs', '_atom_batch.json'))
        ds_only = arg('--datasets')
        ds_only = set(ds_only.split(',')) if ds_only else None
        b, pick = build(rows, per, mx, tpls, ds_only)
        json.dump(b, io.open(out_p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('生成 %d 条 → %s' % (len(b), out_p))
        for o in b:
            print('  %-40s %s' % (o['cid'][:40], o['code']))
        return

    sys.exit('未知命令：%s（可用 list / fields / build）' % cmd)


if __name__ == '__main__':
    main()
