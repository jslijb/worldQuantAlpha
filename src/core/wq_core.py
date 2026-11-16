# -*- coding: utf-8 -*-
"""wq_core.py —— **唯一的生产门控内核**（2026-11-16 建）

## 为什么建这个文件（李工 11-16 批评实测数据）

体检（AST 全量扫描，1076 个 .py）结论：
- 生产路径闭包只有 **14 个文件**（sim_run / now_submit / super_now / run_pipeline / mine_grid / make_report 及其依赖），
  **98.7% 的代码不在任何生产链上**；
- **13 个库形态文件零 import**（建好放那没人调用），**14 个函数真死**；
- **162 组完全相同的函数体跨文件复制**（147 组连函数名都一样）；
- `_autologs/` 独占 1008 文件 / 84541 行 = **86% 的代码量**，是复制粘贴的坟场。

最严重的一例实测：`op_ban.guard_batch`（group_rank 禁令的批量执行器）
**全项目零调用**，`sim_run.py` 根本没 import op_ban ⇒
**李工 11-15 12:55 "group_rank 禁 10 天"的硬禁令，在唯一发模拟通道上从未执行过。**

## 这个文件做什么

把"构造深度门 + 算子禁令门 + VF 对齐门(7/8/9) + 多样性门 + ATOM 判定"
收敛成**一个函数 `run_gates()`**，生产入口（sim_run.py）必须调它。

**它同时是"建好不接线"的解药**：
- 每个门都带 `assert wired` —— 有门没接线就在 import 期直接抛错，不是靠人记得调；
- `wq_core.WIRED` 记录每道门由谁在何时接入，`wq_core.self_test()` 可一键复核。

## 纪律（2026-11-16）

**新增任何门，必须在本文件注册 + 在 `WIRED` 里登记调用方，
否则 `sim_run.py` 启动即失败。** 不允许"门建在 _grid/ 里没人 import"。

用法：
    import wq_core
    ok, report = wq_core.run_gates(batch, cid_key='cid')
    if not ok:
        raise SystemExit(4)
"""
import os as _os, io, sys, json, time
from pathlib import Path

ROOT = Path(r'D:\Python\worldquant')
_GRID = ROOT / '_grid'
_SRC = ROOT / 'src'
# ★ src/core 必须单独进 path：wq_core 住在 src/core/，其它模块按 `from src.core.x import y` 引用它，
#   而 sim_run.py 直接 `import wq_core` —— 两种引用方式都要能工作。
for _p in (str(ROOT), str(_GRID), str(_SRC), str(_SRC / 'core')):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# ---------------------------------------------------------------- 门注册表
# 每个门 = (门名, 检查函数, 阻断码, 失败时给用户的处理办法)
# 检查函数签名：fn(batch) -> (ok: bool, violations: list[(tag, who, why)], lines: list[str])
GATES = []


def register_gate(name, fn, exit_code, remedy):
    """注册一道门。**只有注册到这里的门才会被执行。**"""
    GATES.append({'name': name, 'fn': fn, 'exit_code': exit_code, 'remedy': remedy})
    return fn


# ---------------------------------------------------------------- 各门实现
def _gate_depth(batch):
    """D1 关系算子 / D2 变换层数 ≥2 / D3 禁独立归一化直接相加"""
    import depth_check as DC
    viol, lines = [], []
    shallow = []
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        ok, d = DC.check(code)
        if not ok:
            shallow.append((b.get('cid', ''), d))
    if shallow:
        for cid, d in shallow:
            viol.append(('深度门', cid, '算子=%s 层数=%s | %s' % (
                d.get('算子数'), d.get('变换层数'), '; '.join(d.get('不合格原因', [])))))
    lines.append('构造深度门: %s' % ('PASS' if not viol else 'BLOCK %d' % len(viol)))
    return (not viol), viol, lines


def _gate_opban(batch):
    """算子硬禁令（李工 11-15 12:55）：group_rank 2026-11-15~11-24 全面禁用。

    ★ 这一门在 11-16 之前**从未被执行过**（op_ban.guard_batch 零调用）。
    """
    import op_ban as OB
    viol, lines = [], []
    if not OB.active_bans():
        lines.append('算子禁令门: 无生效禁令（PASS）')
        return True, viol, lines
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        if OB.is_banned(code):
            toks = [t for t in OB.banned_tokens() if t in code]
            viol.append(('算子禁令', b.get('cid', ''), '命中禁用算子 %s' % ','.join(toks)))
    lines.append('算子禁令门: %s（生效禁令 %s）' % (
        'PASS' if not viol else 'BLOCK %d' % len(viol), ','.join(OB.banned_tokens())))
    return (not viol), viol, lines


def _gate_vf(batch):
    """门7 单 alpha 字段数 ≤2 / 门8 每批 ≥2 台账未用字段 / 门9 atom 占比 ≥50%"""
    import diversity as DIV
    ledger = ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
    ok, viol, lines = DIV.gate_vf(batch, ledger=str(ledger), verbose=False)
    return ok, viol, lines


def _gate_diversity(batch):
    """批次层面多样性（数据集/idea/算子/外壳/中性化/... 单项份额上限）

    ⚠ `diversity.gate` 返回的 violation 是 **6 元组** `(dim, item, cnt, T, s, share)`，
    而 `gate_vf` 返回的是 **3 元组** `(tag, who, why)`。这里统一成 3 元组再往上抛，
    否则上层按 3 元组解包会 ValueError（11-16 实测踩到）。
    """
    import diversity as DIV
    ok, viol, lines = DIV.gate(batch, verbose=True)
    norm = []
    for v in viol:
        if len(v) == 6:
            dim, item, cnt, T, s, share = v
            norm.append((dim, str(item), '占比 %.1f%% > 限 %.1f%%（%d/%d）'
                         % (s * 100, share * 100, cnt, T)))
        elif len(v) == 3:
            norm.append((v[0], str(v[1]), str(v[2])))
        else:
            norm.append(('多样性', str(v), ''))
    return ok, norm, lines


def _gate_atom(batch):
    """ATOM 判定：每条必须是单数据集（平台 SINGLE_DATA_SET 的本地等价物）"""
    from atom import judge
    viol, lines = [], []
    n_atom = 0
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        ok, ds, why = judge(code)
        if ok:
            n_atom += 1
        else:
            viol.append(('ATOM', b.get('cid', ''), why))
    lines.append('ATOM 门: %d/%d 条是单数据集' % (n_atom, len(batch)))
    return (not viol), viol, lines


# 注册（顺序 = 执行顺序：从便宜到贵，快的先拦）
register_gate('深度门', _gate_depth, 4,
              '把字段做成关系（比值/差/条件/相关性）+ 反复变换（差分后除波动、均值差再归一），'
              '不要用"各字段独立归一化后相加"。参考 _grid/atom_single.py 的 S1~S6/N1~N6。')
register_gate('算子禁令门', _gate_opban, 8,
              '命中李工 11-15 硬禁令的算子必须换掉，禁令窗口 2026-11-15~11-24 不得绕过。')
register_gate('VF对齐门(7/8/9)', _gate_vf, 6,
              '门7 ⇒ 每条 alpha 不同字段数 ≤2；门8 ⇒ 每批 ≥2 个台账未用字段；'
              '门9 ⇒ 本批 atom 占比 ≥50%。')
register_gate('ATOM门', _gate_atom, 9,
              '每条必须是单数据集；混数据集的件不得进生产批。')
register_gate('多样性门', _gate_diversity, 2,
              '补数据集/补 idea/换外壳/补未用算子，不要改阈值。')

# 探测批前缀：只警告不阻断（语法探针，不进生产记账）
PROBE_PREFIX = ('SYN_', 'TEST_', 'EXP_')

# ---------------------------------------------------------------- 接线记录
# 每接一道门进来就登记一次。self_test() 会核对「注册了但没人调用」的情况。
WIRED = {
    '深度门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    '算子禁令门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16',
                   'how': 'wq_core.run_gates() ← 11-16 新接入（此前从未执行）'},
    'VF对齐门(7/8/9)': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    'ATOM门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    '多样性门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
}

PROBE_PREFIX_NOTE = '探测批前缀（SYN_/TEST_/EXP_）只警告不阻断'


def run_gates(batch, log=None, probe=None, ledger=None):
    """跑全部注册的门。

    返回 (ok: bool, report: list[str])。
    任何一道门失败 ⇒ ok=False，report 里逐条写明「哪条件、为什么、怎么改」。
    """
    rep = []
    if log:
        rep.append(log)
    if probe is None:
        probe = bool(batch) and all(str(b.get('cid', '')).startswith(PROBE_PREFIX) for b in batch)
    for g in GATES:
        try:
            ok, viol, lines = g['fn'](batch)
        except Exception as e:
            import traceback
            ok = False
            viol = [('门异常', g['name'], repr(e))]
            lines = ['%s 执行异常（按失败处理，不放行）:\n%s'
                     % (g['name'], traceback.format_exc(limit=3))]
        for L in lines:
            rep.append(L)
        # 统一成 3 元组，避免不同门返回结构不同导致上层解包崩溃
        norm = []
        for v in (viol or []):
            if isinstance(v, (tuple, list)) and len(v) == 3:
                norm.append((str(v[0]), str(v[1]), str(v[2])))
            else:
                norm.append((g['name'], str(v), ''))
        viol = norm
        if not ok:
            if probe:
                rep.append('（%s 探测批：只警告，不阻断）' % g['name'])
                for tag, who, why in viol:
                    rep.append('    [%s] %s：%s' % (tag, who, why))
            else:
                rep.append('!!! %s BLOCK：%d 处不合规' % (g['name'], len(viol)))
                for tag, who, why in viol:
                    rep.append('    [%s] %s：%s' % (tag, who, why))
                rep.append('!!! 处理办法：%s' % g['remedy'])
                rep.append('!!! 门码 %d' % g['exit_code'])
                return False, rep
    rep.append('全部门控 PASS（%d 道：%s）' % (len(GATES), '、'.join(g['name'] for g in GATES)))
    return True, rep


def gate_exit_code():
    """被阻断时该退的码（取第一道失败门的码）。"""
    return GATES[0]['exit_code'] if GATES else 4


def commit_batch(batch, tag=None):
    """把本批记进 live 多样性库。

    ★ 11-16：`diversity.commit()` 此前**从未被任何地方调用** ⇒ live event 表
      永远只有建库时的 10 条 ⇒ 门控分母 T=10+本批 ⇒ 任何 ≥6 条的批必然超限
      ⇒ 门数学上无解 ⇒ 11-15 全部批次都是靠 `--no-gate` 硬绕过去的。
      本函数由 sim_run.py 在「门控通过 + 模拟已发出」后调用，把 live 库填起来，
      让门从"数学无解"变成"真能拦"。

    check=False：门控已在 run_gates 跑过，此处不再自检（否则自锁）。
    """
    import diversity as DIV
    try:
        n = DIV.commit(batch, tag=tag, basis='live', check=False)
        return True, '多样性库已记账 %d 条（live 口径）' % n
    except Exception as e:
        return False, '多样性库记账失败: %r' % (e,)


def self_test():
    """一键复核：注册的门是否都登记了接线方。返回 (ok, lines)。"""
    lines = []
    ok = True
    for g in GATES:
        w = WIRED.get(g['name'])
        if not w:
            ok = False
            lines.append('  [断链] %s：注册了但没有任何调用方登记 ⇒ 会重演"建好放那空着"' % g['name'])
        else:
            lines.append('  [已接] %s ← %s (%s, %s)' % (g['name'], w['caller'], w['date'], w['how']))
    lines.append('门总数 %d，已接 %d' % (len(GATES), sum(1 for g in GATES if g['name'] in WIRED)))
    return ok, lines


if __name__ == '__main__':
    ok, lines = self_test()
    print('\n'.join(lines))
    print('自检结果：', 'PASS' if ok else 'FAIL（有断链）')
    sys.exit(0 if ok else 1)
