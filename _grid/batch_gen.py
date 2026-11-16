# -*- coding: utf-8 -*-
"""batch_gen.py —— 批次生成器（唯一允许的批次生产入口）

为什么要有它：
  2026-11-15 之前，我的批次是"一条一条手打表达式"。手打就必然回到肌肉记忆，
  肌肉记忆就是 group_rank —— 今天 157 条里 122 条用它。李工骂了三次，说
  "看似改了实际没改"。所以把生成动作收归到本文件：只允许给【内核】和【外壳族名】，
  由机器拼装 + 校验 + 打分布直方图，人不许再直接写完整表达式。

硬约束（缺一不可，全部机器强制）：
  1. 单数据集：一条表达式只能用到同一个 dataset 的字段（+ 6 个豁免分组字段）。
  2. 算子禁用以 op_ban.py 为准，不在这里硬编码名单。
  3. 同一批次必须覆盖 ≥ min_shells 个不同外壳族，否则拒绝产出。
  4. 产出前打印算子直方图，最大单算子占比 > 50% 拒绝产出。

用法：
    from batch_gen import build_batch, histogram, assert_diverse
    batch = build_batch('fundamental6', kernels, shell_names=['rk','qt','tsQt',...])
    print(histogram(batch))
"""
import io
import json
import collections
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from op_ban import is_banned, OpBanned
from transforms import FAMILIES, POST

# 豁免分组字段（不算作"用了第二个数据集"）
EXEMPT_GROUPS = {'country', 'exchange', 'market', 'sector', 'industry', 'subindustry'}

_FAM = {n: fn for n, fn, _ in FAMILIES + POST}


def shells(names=None):
    return list(names) if names else [n for n, _f, _d in FAMILIES]


def build_batch(dataset, kernels, shell_names=None, settings=None,
                prefix=None, cid_style='{ds}_{k}_{sh}', known_fields=None):
    """kernels: [(核名, 核表达式, 该核用到的字段列表)]
    known_fields: 该 dataset 的合法字段集合；给了就强制校验单数据集，不给只做禁用校验。
    返回 ([...], [被拒原因...])

    ★ 2026-11-16 起：kernels 的核可以带第 4/5 个元素 —— idea_id 与 mech（一句话机制说明）。
      两者都必填，由 save() → assert_mechanism() 强制（缺一即拒产出）。
      浅构造（无关系算子/变换层数<2）同样被拒。
    """
    shell_names = shells(shell_names)
    prefix = prefix or dataset[:6].upper()
    out, rejected = [], []
    for k in kernels:
        kname, core, flds = k[0], k[1], k[2]
        idea_id = k[3] if len(k) > 3 else None
        mech = k[4] if len(k) > 4 else None
        if known_fields is not None:
            stray = [f for f in flds if f not in EXEMPT_GROUPS and f not in known_fields]
            if stray:
                rejected.append((kname, '*', '跨数据集字段 %s（不属 %s）' % (stray, dataset)))
                continue
        for sh in shell_names:
            fn = _FAM.get(sh)
            if not fn:
                rejected.append((kname, sh, '未知外壳族'))
                continue
            try:
                code = fn(core)
            except Exception as e:                       # noqa: BLE001
                rejected.append((kname, sh, '拼装异常 %s' % e))
                continue
            hit = is_banned(code)
            if hit:
                rejected.append((kname, sh, '命中禁用 %s' % hit))
                continue
            cid = cid_style.format(ds=prefix, k=kname, sh=sh)
            out.append({
                'cid': cid, 'code': code,
                'settings': settings or {},
                'dataset': dataset, 'kernel': kname, 'shell': sh,
                'fields': list(flds),
                'idea_id': idea_id, 'mech': mech,
            })
    return out, rejected


def histogram(batch, top=15):
    c = collections.Counter()
    for b in batch:
        for op in re.findall(r'\b([a-z_]+)\s*\(', b['code']):
            c[op] += 1
    tot = sum(c.values()) or 1
    lines = ['算子直方图（共 %d 次调用 / %d 条）:' % (tot, len(batch))]
    for op, n in c.most_common(top):
        lines.append('  %-18s %4d  %5.1f%%' % (op, n, n / tot * 100))
    shell_c = collections.Counter(b['shell'] for b in batch)
    lines.append('外壳分布: ' + ', '.join('%s×%d' % kv for kv in shell_c.most_common()))
    return '\n'.join(lines), c, tot


def assert_diverse(batch, min_shells=6, max_op_share=0.5):
    """批次多样性硬门，不通过直接抛异常（不许"打完日志照样跑"）"""
    _txt, c, tot = histogram(batch)
    used = {b['shell'] for b in batch}
    if len(used) < min_shells:
        raise AssertionError('外壳族只用 %d 个 < %d: %s' % (len(used), min_shells, used))
    ds = {b['dataset'] for b in batch}
    if len(ds) != 1:
        raise AssertionError('批次混了多个数据集: %s' % ds)
    if c:
        op, n = c.most_common(1)[0]
        if n / tot > max_op_share:
            raise AssertionError('单算子 %s 占 %.0f%% > %.0f%%'
                                 % (op, n / tot * 100, max_op_share * 100))
    return True


def assert_mechanism(batch):
    """机制说明 + 构造深度硬门（2026-11-16 李工批评后加）

    事故背景（事实）：11-15 那批"新数据集 ATOM 批"21 条 S 全部 -1.27~0.67，
    我据此下结论"新数据集过不了门、只能靠量价续命"。
    **根因是用浅构造测高价值数据**：那批是"各字段独立归一化后任意符号相加"，
    字段之间的关系被抹掉（21 条里只有 3 条含比值/乘法/条件）。

    三条硬门：
      M1 每个核必须带 mech（一句话说清"在赌什么"）—— 空则拒。
      M2 构造深度必须过 _grid/depth_check.py（D1 关系算子 / D2 变换层数 / D3 禁并行相加）。
      M3 idea_id 必须显式给出 —— 缺失则拒（diversity.py 的 idea 维度不能再靠 cid 前缀凑）。

    ★ 这三道门是**发模拟前**的拦截，不是事后解释。
    """
    import depth_check as DC
    for b in batch:
        mech = (b.get('mech') or '').strip()
        if not mech:
            raise AssertionError(
                '核 %r 缺机制说明(mech)：每条候选必须能用一句话说清"在赌什么"，'
                '说不清就是字段堆砌（11-15 那 21 条 S -1.27~0.67 的根因）' % b.get('cid'))
        if not (b.get('idea_id') or '').strip():
            raise AssertionError(
                '核 %r 缺 idea_id：diversity 的 idea 维度必须显式登记，'
                '不能再靠 cid 前缀凑（换批次名就绕门的漏洞）' % b.get('cid'))
        ok, d = DC.check(b['code'])
        if not ok:
            raise AssertionError(
                '核 %r 构造过浅：%s\n    code=%s\n    修法：字段做成关系（比值/差/条件/相关性）'
                '+ 反复变换（差分后除波动、均值差再归一），参考 atom_complex.py 的 C1~C6'
                % (b.get('cid'), '; '.join(d['不合格原因']), b['code']))
    return True


def save(batch, path):
    assert_diverse(batch)
    assert_mechanism(batch)
    json.dump(batch, io.open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return path
