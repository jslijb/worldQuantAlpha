# -*- coding: utf-8 -*-
"""backfill_live_1116.py —— 用 11-15/11-16 真实模拟件回灌 live 多样性库。

## 为什么需要（11-16 实测）

`diversity.commit()` 从未被调用 ⇒ live event 表自建库起只有 **10 条** ⇒
门控分母 T = 10 + 本批条数 ⇒ 任何 ≥6 条的批在 operator/neutralization/decay 维
必然超限 ⇒ **门在数学上无解** ⇒ 11-15 全部批次都是靠 `--no-gate` 硬绕过去的
（实测 `_sim_atom1115/_sim_lowto*` 各 BLOCK 6~13 处照放）。

修法不是改阈值（阈值是李工的 10% 硬线），而是**把 live 库填成真实的样子**：
live = "规则生效后我们实际用过什么"，这正是门该管的区间。
历史更早的用量已在 basis='history'/'lifetime' 里（95047 条），不重复计入。

## 数据来源

`data/alpha_quality_analysis/mined/*.json` —— sim_run.py 落盘的真实平台模拟结果，
每条含 cid / 表达式 / 实际 settings（decay/neutralization/truncation/universe）。
只取**11-15 之后**（规则生效后）落盘的件。

用法：
    python _grid/backfill_live_1116.py --dry-run
    python _grid/backfill_live_1116.py
"""
import io, os, sys, json, glob, re, argparse, datetime, collections

ROOT = r'D:\Python\worldquant'
sys.path.insert(0, os.path.join(ROOT, '_grid'))
import diversity as DIV

MINED = os.path.join(ROOT, 'data/alpha_quality_analysis/mined')
CUTOFF = '2026-11-15'          # 规则生效日（含）


def mined_entries():
    """从 mined/*.json 抽 (cid, code, settings)。"""
    out = []
    for p in glob.glob(os.path.join(MINED, '*.json')):
        bn = os.path.basename(p)[:-5]
        try:
            d = json.load(io.open(p, encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        code = d.get('code') or d.get('expression') or d.get('expr') or ''
        if not code:
            continue
        st = d.get('settings') or {}
        item = {'cid': bn, 'code': code}
        for k in ('decay', 'neutralization', 'truncation', 'universe'):
            v = st.get(k)
            if v is not None:
                item[k] = v
        out.append(item)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--cutoff', default=CUTOFF)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    ents = mined_entries()
    # 只取 11-15 之后落盘的：按文件 mtime 过滤
    import time
    cut_ts = None
    for d in ('2026-11-15',):
        cut_ts = time.mktime(time.strptime(d, '%Y-%m-%d'))
    sel = []
    for e in ents:
        p = os.path.join(MINED, e['cid'] + '.json')
        try:
            mt = os.path.getmtime(p)
        except OSError:
            continue
        if mt >= cut_ts:
            sel.append(e)
    if args.limit:
        sel = sel[:args.limit]

    print('mined 共 %d 件，其中 %s 之后落盘 %d 件' % (len(ents), args.cutoff, len(sel)))
    if not sel:
        print('无件可回灌')
        return

    # ★ 过滤掉 settings 缺失的历史件：mined/*.json 大多没存 settings
    #   （落盘只存了 is/test 指标），⇒ universe/neutralization/decay/truncation
    #   全记成 '?' ⇒ '?' 会占 15~27% 变成一个假"最重项"，污染分母。
    #   只保留**四个参数齐全**的件，让 live 库分母干净。
    full = [e for e in sel if all(e.get(k) is not None
                                  for k in ('decay', 'neutralization', 'truncation', 'universe'))]
    print('其中四个回测参数齐全的 %d 件（其余因缺 settings 记成 ? 会污染分母，排除）'
          % len(full))
    if not full:
        print('无参数齐全的件，无法回灌 live')
        return
    sel = full

    # 预览
    agg = collections.defaultdict(collections.Counter)
    for e in sel:
        for dim, dd in DIV.parse_alpha(e).items():
            for k, v in dd.items():
                agg[dim][k] += v

    # ★ 只回灌**参数与算子维度**（universe/neutralization/decay/truncation/operator）。
    #   dataset 维度历史件的字段映射不全（infer_dataset 走旧表）⇒ '?' 占 43%；
    #   idea 维度历史件本来就没登记 idea_id（那时还没这机制）⇒ 100% 是 '?'。
    #   把 '?' 灌进库 = 造一个 43% 的假"最重项"污染分母 ⇒ 这两个维度不回灌。
    BACKFILL_DIMS = ('operator', 'universe', 'neutralization', 'decay', 'truncation')
    sel2 = []
    for e in sel:
        e2 = dict(e)
        # 把 dataset/idea 从本件里剥掉（parse_alpha 会重算，先算好再剥）
        e2['_skip_dims'] = ('dataset', 'idea')
        sel2.append(e2)
    print('\n回灌后 live 库各维度预期分布：')
    for dim in DIV.DIMS:
        c = agg[dim]
        tot = sum(c.values())
        if not tot:
            continue
        print('  %-15s 项数=%-4d 总量=%-6d top=%s'
              % (dim, len(c), tot, [(k, v, '%.0f%%' % (100.0 * v / tot))
                                    for k, v in c.most_common(6)]))

    if args.dry_run:
        print('\n[dry-run] 未写入')
        return

    n = DIV.commit(sel, tag='backfill_live_1116', basis='live', check=False,
                   dims=BACKFILL_DIMS)
    print('\n已回灌 %d 件到 live 库（维度 %s）' % (n, ', '.join(BACKFILL_DIMS)))
    for dim in DIV.DIMS:
        h = DIV._counts(dim, 'live')
        print('  %-15s live 项数=%-4d 总量=%d' % (dim, len(h), sum(h.values())))


if __name__ == '__main__':
    main()
