# -*- coding: utf-8 -*-
"""combo_gen.py —— idea 组合生成器（李工 1009 指令：两两组合穷尽 → 三三组合）

打什么：docs/methodology/idea.md §1 的原子库
怎么打：docs/methodology/atoms.md

纪律（CLAUDE.md §3.10）：
  - 每条 spec 必须登记 combo_id + 组成 idea_id 到 _autologs/combo_ledger.json
  - 已跑过的组合跳过（可 --revive 只重跑标记为可复活的）
  - 不许凭空写表达式：本文件只做「原子腿 → 加权组合」，不发明新腿

用法：
  python src/knowledge/combo_gen.py --level2 --batch p2a
  python src/knowledge/combo_gen.py --level3 --batch p3a
  python src/knowledge/combo_gen.py --regen-idea   # 回写 idea.md 组合登记簿
"""
import os as _os, io, json, re, sys, argparse, hashlib
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_os.chdir(ROOT)

BUCK = ROOT / '_autologs' / 'idea_buckets.json'
LEDG = ROOT / '_autologs' / 'combo_ledger.json'
SPECS = ROOT / '_autologs'

# 内层 group 归组用：不同分组轴 = corr 更干净（1008-09 组别刀实证）
AXES = ['industry', 'subindustry', 'sector', 'market', 'group']


def inner_axis(leg):
    m = re.findall(r',\s*(subindustry|industry|sector|market|group)\s*\)', leg)
    return m[-1] if m else None


def field_of(leg):
    """粗取字段名，用于去重/多样性判定。"""
    ids = re.findall(r'\b([a-z][a-z0-9_]{3,})\b', leg)
    stop = {'group_rank', 'ts_rank', 'ts_delta', 'ts_mean', 'ts_std_dev', 'rank',
            'bucket', 'range', 'abs', 'vec_avg', 'vec_sum', 'ts_delay', 'ts_av_diff',
            'ts_backfill', 'ts_arg_min', 'returns', 'volume', 'close', 'open', 'assets',
            'adv20', 'subindustry', 'industry', 'sector', 'market', 'group', 'if_else'}
    out = [x for x in ids if x not in stop]
    return out


def combo_id(legs):
    h = hashlib.md5('|'.join(sorted(legs)).encode()).hexdigest()[:8]
    return 'C' + h


def load_buckets():
    b = json.load(open(BUCK, encoding='utf-8'))
    out = []
    for k, arr in b.items():
        for i, it in enumerate(arr):
            out.append({
                'id': '%s%03d' % (k, i + 1),
                'cls': k,
                'leg': it['leg'],
                'n': it['n'],
                'axis': inner_axis(it['leg']),
                'fields': field_of(it['leg']),
            })
    return out


def load_ledger():
    if LEDG.exists():
        return json.load(open(LEDG, encoding='utf-8'))
    return {}


def save_ledger(lg):
    json.dump(lg, open(LEDG, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def build_expr(main, aux):
    """主腿 1.5 + 辅腿 0.6，辅腿换分组轴去同质。"""
    m = main['leg']
    a = aux['leg']
    # 主腿换轴：若辅腿与主腿同轴，则主腿保留、副腿换到不同轴
    ma, aa = main['axis'], aux['axis']
    if ma and ma == aa:
        for ax in AXES:
            if ax != ma:
                a2 = re.sub(r',\s*%s\s*\)' % ma, ', %s)' % ax, a)
                if a2 != a:
                    a = a2
                    break
    return '1.5*(%s)+0.6*(%s)' % (m, a), ('%s|%s' % (main['id'], aux['id'])), aux['id']


def gen(level, batch, size, lead_n, revive_only):
    atoms = load_buckets()
    lg = load_ledger()
    atoms = [a for a in atoms if a['n'] >= lead_n]
    by = {'F': [a for a in atoms if a['cls'] == 'F'], 'T': [a for a in atoms if a['cls'] == 'T']}

    pairs = []
    if level == 2:
        for c1 in ('F', 'T'):
            for c2 in ('F', 'T'):
                if c1 == 'T' and c2 == 'F':
                    continue  # F×T 与 T×F 同一集合
                for i, m in enumerate(by[c1]):
                    for a in by[c2]:
                        if m['id'] == a['id']:
                            continue
                        if set(m['fields']) & set(a['fields']):
                            continue  # 字段重叠=同信息源，跳过
                        pairs.append((m, a))
    else:
        for c in ('FFF', 'FFT', 'FTT', 'TTT'):
            cs = list(c)
            for i, a1 in enumerate(by[cs[0]]):
                for a2 in by[cs[1]]:
                    if a1['id'] == a2['id'] or set(a1['fields']) & set(a2['fields']):
                        continue
                    for a3 in by[cs[2]]:
                        if a3['id'] in (a1['id'], a2['id']) or set(a3['fields']) & (set(a1['fields']) | set(a2['fields'])):
                            continue
                        pairs.append((a1, (a2, a3)))

    # 去重 + 排除已跑
    fresh, seen = [], set()
    for m, a in pairs:
        legs = [m['leg']] + ([a['leg']] if isinstance(a, dict) else [x['leg'] for x in a])
        cid = combo_id(legs)
        if cid in seen:
            continue
        seen.add(cid)
        st = lg.get(cid, {}).get('status', '未使用')
        if revive_only and st not in ('可复活', '未使用'):
            continue
        if not revive_only and st != '未使用':
            continue
        fresh.append((cid, m, a))

    # 稳定排序后按主腿轮转取，保证主腿覆盖面（避免全压在 F001 一条腿上）
    fresh.sort(key=lambda x: (-x[1]['n'], x[0]))
    buckets = {}
    for it in fresh:
        buckets.setdefault(it[1]['id'], []).append(it)
    order = sorted(buckets, key=lambda k: (-len(buckets[k]), k))
    sel, i = [], 0
    while len(sel) < size:
        added = False
        for k in order:
            lst = buckets[k]
            if i < len(lst):
                sel.append(lst[i]); added = True
                if len(sel) >= size:
                    break
        if not added:
            break
        i += 1
    sel = sel[:size]
    spec = {}
    recs = []
    expr_seen = set()
    for k, (cid, m, a) in enumerate(sel):
        if isinstance(a, dict):
            expr, ids, _ = build_expr(m, a)
        else:
            m2 = dict(m); m2['axis'] = inner_axis(m['leg'])
            e1, i1, _ = build_expr(m2, a[0])
            e2, i2, _ = build_expr(dict(a[1], axis=inner_axis(a[1]['leg'])), a[0])
            expr = '%s+0.5*(%s)' % (e1, a[1]['leg'])
            ids = i1 + '|' + i2
        if expr in expr_seen:
            continue
        expr_seen.add(expr)
        key = '%s_%03d' % (batch, len(spec))
        spec[key] = {'expr': expr}
        lg[cid] = {'combo_id': cid, 'level': level, 'batch': batch, 'spec_key': key,
                   'idea_ids': ids, 'expr': expr, 'status': '已跑', 'result': {}}
        recs.append((cid, key, ids))

    assert len(set(v['expr'] for v in spec.values())) == len(spec), '表达式重复，中止'
    p = SPECS / ('spec_%s.json' % batch)
    json.dump(spec, open(p, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    save_ledger(lg)
    print('生成 %d 条 -> %s' % (len(spec), p))
    for cid, key, ids in recs[:8]:
        print('  %s  %s  %s' % (cid, key, ids))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--level2', action='store_true')
    ap.add_argument('--level3', action='store_true')
    ap.add_argument('--batch', required=True)
    ap.add_argument('--size', type=int, default=120)
    ap.add_argument('--lead-n', type=int, default=3, help='主腿最低使用次数')
    ap.add_argument('--revive', action='store_true', help='只出标记为可复活的组合')
    a = ap.parse_args()
    gen(2 if a.level2 else 3, a.batch, a.size, a.lead_n, a.revive)
