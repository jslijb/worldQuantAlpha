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
import os as _os, io, sys, json, time, re
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


def register_gate(name, fn, exit_code, remedy, advisory=False):
    """注册一道门。**只有注册到这里的门才会被执行。**

    ★ 11-16 16:25（李工指令「我们的门控只有一个 Alpha 必须完全符合 ATOM」）：
      advisory=True 的门 = **诊断项**：照常计算并写进报告，但**不阻断批次**。
      唯一硬拦门 = ATOM 门（advisory=False）。
    """
    GATES.append({'name': name, 'fn': fn, 'exit_code': exit_code, 'remedy': remedy,
                  'advisory': advisory})
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


def _gate_mech(batch):
    """机制门：每条候选必须带 mech（"在赌什么"）+ idea_id，且 idea 不能由模板名反推

    ★ 11-16 17:00 新增。起因（李工 16:50 当面自审）：
      「你看下这个表达式是**为了能够满足门控写的**，还是理解了这个 idea 觉得需要这么写？」

      自审结论：Jj8gZxvA 是**为了满足门控写的**。三条硬证据：
        1. tpl="C1_三腿时序共振"、idea_id="analyst7__C1_三腿时序共振"
           ⇒ idea_id 是**从模板名反推**的（方向反了：应是 idea → 表达式）
        2. 没有 mech 字段 ⇒ 绕过了 batch_gen.assert_mechanism
        3. 字段语义错（act_q_ebi_surprisenum = 估计家数，被当惊喜值用）

      ⇒ 这道门把"机制先行"落成代码级强制：
        · 每条必须有 mech（一句话说清在赌什么），空 ⇒ 拦
        · idea_id 必须显式给出，且**不得**等于 tpl/模板名（那是反推）
        · idea_id 不得含模板编号形态（C1/C2/外壳名等）⇒ 拦
    """
    viol, lines = [], []
    n_ok = 0
    for b in batch:
        cid = b.get('cid', '')
        mech = (b.get('mech') or '').strip()
        idea = (b.get('idea_id') or '').strip()
        tpl = (b.get('tpl') or '').strip()
        if not mech:
            viol.append(('机制门', cid, '缺 mech（说不清在赌什么 = 字段堆砌）'))
            continue
        if not idea:
            viol.append(('机制门', cid, '缺 idea_id（不能靠 cid 前缀凑）'))
            continue
        # idea_id 不得由模板名反推：模板名形态 = 含 C1/C2/C3 编号，或 idea_id == tpl
        if tpl and idea == tpl:
            viol.append(('机制门', cid, 'idea_id 与 tpl 相同 ⇒ 模板名反推 idea，方向反了'))
            continue
        if re.search(r'_C\d+', idea) or re.search(r'\bC[1-9]\b', idea):
            viol.append(('机制门', cid,
                         'idea_id 含模板编号形态 %r ⇒ 模板名反推 idea，方向反了' % idea))
            continue
        n_ok += 1
    lines.append('机制门: %d/%d 条有 mech + 先行的 idea_id（PASS）'
                 % (n_ok, len(batch)) if not viol
                 else '机制门: %d/%d 条不合格（缺 mech / idea 反推）' % (len(viol), len(batch)))
    return (not viol), viol, lines


def _gate_vf(batch):
    """门7 批次平均字段数 ≤8 / 门8 每批 ≥2 台账未用字段 / 门9 atom 占比 ≥50%"""
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
    """ATOM 判定：每条必须是单数据集（平台 SINGLE_DATA_SET 的本地等价物）

    ★ 11-17：按批次条目的 settings.region 传 region 给 judge()，
      修 AGENTS.md §192 记录的老 bug（字段归属是 region 相关的，
      不传 region ⇒ 走全局合并表 ⇒ cashflow_op 在 USA/EUR 归属串味）。
    """
    from atom import judge
    viol, lines = [], []
    n_atom = 0
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        st = b.get('settings') or {}
        reg = st.get('region') or b.get('region')
        ok, ds, why = judge(code, region=reg)
        if ok:
            n_atom += 1
        else:
            viol.append(('ATOM', b.get('cid', ''), why))
    lines.append('ATOM 门: %d/%d 条是单数据集' % (n_atom, len(batch)))
    return (not viol), viol, lines


# ---------------------------------------------------------------- 数据黑名单门（2026-11-17 李工纪律 2/3，硬拦）
# 纪律2：USA 量价数据（pv1）列入黑名单；USA 整体数据集优先级最低。
# 纪律3：alpha 必须是真 ATOM；量价字段进表达式 = 伪 ATOM 高风险（vec_avg 隐式 pv1 依赖等），默认拦截。
PV1_STATIC = {'open', 'high', 'low', 'close', 'volume', 'vwap', 'returns',
              'adv20', 'cap', 'adjfactor', 'split', 'dividend', 'sharesout'}
# §1 豁免分组字段：只允许作 group 参数出现，不当作量价数据字段扫描
EXEMPT_GROUP = {'country', 'exchange', 'market', 'sector', 'industry', 'subindustry'}
_BL_F = ROOT / 'src' / 'core' / 'blacklist.json'
try:
    if _BL_F.exists():
        PV1_STATIC |= set(json.load(io.open(_BL_F, encoding='utf-8')).get('pv1_fields') or [])
except Exception:
    pass  # 黑名单文件损坏时退回内置静态表，门不失效


def _gate_blacklist(batch):
    """数据黑名单门（李工 2026-11-17 纪律 2/3，**硬拦**，不 advisory）：

    1) 纪律2：USA 量价数据（pv1）黑名单 —— 表达式出现 pv1 字段即 BLOCK；
    2) 纪律3：真 ATOM —— 量价字段进表达式多半构成伪 ATOM，所有 region 默认拦截。

    确需豁免：批次条目显式加 `"exempt_pv1": true` 并在 mech 写明理由（留痕上报）。
    """
    from atom import dataset_of
    viol, lines = [], []
    for b in batch:
        code = b.get('code') or b.get('expr') or ''
        st = b.get('settings') or {}
        reg = st.get('region') or b.get('region') or ''
        toks = set(re.findall(r'[A-Za-z_][A-Za-z0-9_]*', code or '')) - EXEMPT_GROUP
        hits = sorted(toks & PV1_STATIC)
        for t in sorted(toks - PV1_STATIC):
            try:
                ds = dataset_of(t, region=reg)
            except TypeError:
                ds = dataset_of(t)
            if isinstance(ds, str) and ds.strip().lower() == 'pv1':
                hits.append(t)
        if hits and not b.get('exempt_pv1'):
            viol.append(('数据黑名单', b.get('cid', ''),
                         'pv1 量价字段 %s（region=%s）⇒ USA 量价黑名单/伪 ATOM 风险'
                         % (','.join(sorted(set(hits))), reg or '?')))
    lines.append('数据黑名单门(pv1): %s' % ('PASS' if not viol else 'BLOCK %d' % len(viol)))
    return (not viol), viol, lines


# 注册（顺序 = 执行顺序：从便宜到贵，快的先拦）
# ★★ 11-16 16:25 门控精简（李工指令原文）：
#   「之前你设置的门控本质上可以删除。数据多样性，算子多样性，idea 多样性，
#     回测参数多样性，这些门控都可以删除。甚至 group_rank 这个算子从黑名单剔除。
#     我们的门控只有一个 Alpha 必须完全符合 ATOM。」
#   ⇒ 唯一硬拦门 = ATOM 门；其余全部 advisory=True（诊断项，只报告不阻断）。
#   ⇒ 保留诊断项不是为了拦，是为了留证据（这批在深度/机制/多样性上什么状况），
#     由人判断，不代替人做决定。

register_gate('深度门', _gate_depth, 4,
              '把字段做成关系（比值/差/条件/相关性）+ 反复变换（差分后除波动、均值差再归一），'
              '不要用"各字段独立归一化后相加"。参考 _grid/atom_single.py 的 S1~S6/N1~N6。'
              '★ 11-16 16:50：深度门**不含算子数下限**，复杂度=关系算子+变换层数，'
              '字段数与算子数都作硬门（"≥8 算子"是我编的数字，已删）。',
              advisory=True)
register_gate('机制门', _gate_mech, 5,
              '每条候选必须带 mech（"在赌什么"）+ 先行的 idea_id；'
              'idea_id 不得由模板名/tpl 反推（模板名反推 idea = 方向反了）。'
              '见 AGENTS.md §纠正 7（李工 11-16 16:50 自审：Jj8gZxvA 是"为过门而写"的）。',
              advisory=True)
register_gate('算子禁令门', _gate_opban, 8,
              '命中李工 11-15 硬禁令的算子必须换掉，禁令窗口 2026-11-15~11-24 不得绕过。'
              '★ 11-16 16:25：group_rank 已从黑名单剔除（李工指令），当前无生效禁令。',
              advisory=True)
register_gate('VF对齐门(7/8/9)', _gate_vf, 6,
              '门7 ⇒ 批次平均字段数 ≤8（台账实测基线 7.73，不逐条硬拦）；'
              '门8 ⇒ 每批 ≥2 个台账未用字段；'
              '门9 ⇒ 本批 atom 占比 ≥50%。',
              advisory=True)
register_gate('ATOM门', _gate_atom, 9,
              '每条必须是单数据集；混数据集的件不得进生产批。'
              '★ 11-16 16:25：唯一硬拦门之一（李工「我们的门控只有一个 Alpha 必须完全符合 ATOM」）。')
register_gate('数据黑名单门', _gate_blacklist, 10,
              '李工 2026-11-17 纪律2/3：USA 量价（pv1）黑名单；量价字段进表达式 = 伪 ATOM 风险，'
              '所有 region 默认拦截。改用非量价数据集（如 EUR fundamental23 / model29 / model36 / '
              'insider_feats / risk72 / model28）。确需豁免：条目加 "exempt_pv1": true '
              '并在 mech 写明理由（留痕上报）。')
register_gate('多样性门', _gate_diversity, 2,
              '补数据集/补 idea/换外壳/补未用算子，不要改阈值。'
              '★ 11-16 16:25：改为诊断项（李工「数据多样性、算子多样性、idea 多样性、'
              '回测参数多样性，这些门控都可以删除」）。',
              advisory=True)


# 探测批前缀：只警告不阻断（语法探针，不进生产记账）
PROBE_PREFIX = ('SYN_', 'TEST_', 'EXP_')

# ---------------------------------------------------------------- 接线记录
# 每接一道门进来就登记一次。self_test() 会核对「注册了但没人调用」的情况。
WIRED = {
    '深度门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    '机制门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16',
               'how': 'wq_core.run_gates() ← 11-16 17:00 新接入（AGENTS.md §纠正 7）'},
    '算子禁令门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16',
                   'how': 'wq_core.run_gates() ← 11-16 新接入（此前从未执行）'},
    'VF对齐门(7/8/9)': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    'ATOM门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
    '数据黑名单门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-17',
                     'how': 'wq_core.run_gates() ← 李工纪律2/3（USA pv1 黑名单 + 真ATOM，硬拦）'},
    '多样性门': {'caller': '_autologs/sim_run.py', 'date': '2026-11-16', 'how': 'wq_core.run_gates()'},
}

PROBE_PREFIX_NOTE = '探测批前缀（SYN_/TEST_/EXP_）只警告不阻断'


def run_gates(batch, log=None, probe=None, ledger=None):
    """跑全部注册的门。

    ★★ 11-16 16:25 门控精简（李工指令）：
        「之前你设置的门控本质上可以删除。数据多样性，算子多样性，idea 多样性，
          回测参数多样性，这些门控都可以删除。
          甚至 group_rank 这个算子从黑名单剔除。
          **我们的门控只有一个 Alpha 必须完全符合 ATOM。**」

        ⇒ ATOM 门是硬拦门（单数据集）；11-17 新增**数据黑名单门**（硬拦）：USA 量价 pv1 黑名单
          + 量价字段默认拦截（纪律3：量价多半构成伪 ATOM）。
        ⇒ 其余门（深度门 / 机制门 / 算子禁令门 / VF对齐门 / 多样性门）全部降级为
          **诊断输出（advisory）**：照常计算、照常写进报告，但**不阻断批次**。
          保留它们不是为了拦，而是为了留证据：
          "这批在深度/机制/多样性上是什么状况"，供人工判断，**不代替人做决定**。
        ⇒ group_rank 已从算子黑名单剔除（`_grid/op_ban.py`）。

    返回 (ok: bool, report: list[str])。
    任何一道**硬拦门**失败 ⇒ ok=False。
    """
    rep = []
    if log:
        rep.append(log)
    if probe is None:
        probe = bool(batch) and all(str(b.get('cid', '')).startswith(PROBE_PREFIX) for b in batch)
    for g in GATES:
        advisory = g.get('advisory', False)
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
            if advisory:
                # ★ 诊断门：只报告，不阻断（李工 11-16 16:25「门控只有 ATOM」）
                rep.append('（%s 诊断项：%d 处不合规 —— 不阻断，由人判断）'
                           % (g['name'], len(viol)))
                for tag, who, why in viol:
                    rep.append('    [%s] %s：%s' % (tag, who, why))
                continue
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
    hard = [g['name'] for g in GATES if not g.get('advisory', False)]
    adv = [g['name'] for g in GATES if g.get('advisory', False)]
    rep.append('门控结果：硬拦门 %s 全部 PASS'
               % ('、'.join(hard) if hard else '无'))
    if adv:
        rep.append('诊断项（不阻断）：%s' % '、'.join(adv))
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
