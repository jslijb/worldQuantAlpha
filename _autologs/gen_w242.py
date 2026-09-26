# -*- coding: utf-8 -*-
"""gen_w242.py —— 「换桶分组」批量扫（实证依据：9qX3M2mq_v2__r_bvol 平台 selfCorr 0.6846 入池）

0920 实证：同家族 9qX3M2mq_v2 走 subindustry/sector 都在 0.72+，换成
  bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")
后平台 selfCorr = 0.6846 → 直接入池。故把该杠杆扫到判决日志里 corr 最近的那批家族上。

变体：
  __bvol      波动率桶（已验证有效）
  __bdv       成交额桶 bucket(rank(ts_mean(volume*close, 20)))（9qjZ8oZ2 用的就是它）
  __bvol_u1k  波动率桶 + TOP1000（官方得分杠杆：池越小 Quality 分越高）

分组替换规则：把顶层 group_rank(x, <subindustry|industry|sector>) 的组参数整体换成桶。
只匹配 `, subindustry)` / `, industry)` / `, sector)`（顶层组参数独有此形态；
桶表达式内部用 range="..."，不会误伤）。
"""
import io, json, os, re

ROOT = 'D:/Python/worldquant/'
MINED = ROOT + 'data/alpha_quality_analysis/mined'

TARGETS = ['w162_06', 'w162_06__g_ind', 'w162_06__g_sec', 'w164_04',
           'D_e79kPeEM_d15', 'kqjpepz8_v2', 'e79kPeEM_v2', 'x162_w164_04_SEC',
           'x172_w164_04_OVN', 'x174_w125_d_AMIINT', 'Acap_SUB', 'w214_x54c_SEC']

BVOL = 'bucket(rank(ts_std_dev(returns, 20)), range="0.1, 1, 0.1")'
BDV = 'bucket(rank(ts_mean(volume*close, 20)), range="0.1, 1, 0.1")'

# 建 _cid -> 文件 索引
bycid = {}
for x in sorted(os.listdir(MINED)):
    if not x.endswith('.json'):
        continue
    try:
        d = json.load(io.open(os.path.join(MINED, x), encoding='utf-8'))
    except Exception:
        continue
    c = d.get('_cid')
    if c:
        bycid[c] = x

rev = re.compile(r', (subindustry|industry|sector)\)')


def regroup(expr, bucket):
    new, n = rev.subn(', %s)' % bucket, expr)
    return new, n


combos = {}
report = []
for cid in TARGETS:
    f = bycid.get(cid)
    if not f:
        report.append('%-22s : 未找到 mined 产出' % cid)
        continue
    d = json.load(io.open(os.path.join(MINED, f), encoding='utf-8'))
    reg = d.get('regular') or {}
    expr = reg.get('code') if isinstance(reg, dict) else reg
    if not expr:
        report.append('%-22s : 无 regular 表达式' % cid)
        continue
    i = d.get('is') or {}
    base = dict(neutralization=d.get('_neut') or 'SUBINDUSTRY',
                decay=d.get('_decay') if d.get('_decay') is not None else 10,
                truncation=0.08)
    report.append('%-22s S=%.2f F=%.2f TO=%.3f legs_g1=%d'
                  % (cid, i.get('sharpe') or 0, i.get('fitness') or 0,
                     i.get('turnover') or 0, len(rev.findall(expr))))

    for tag, bucket, univ in (('bvol', BVOL, None),
                              ('bdv', BDV, None),
                              ('bvol_u1k', BVOL, 'TOP1000')):
        e2, n = regroup(expr, bucket)
        if n == 0:
            continue
        m = dict(base)
        m['expr'] = e2
        if univ:
            m['universe'] = univ
        m['_note'] = '换桶->%s%s（源 %s，平台同法已验证 0.6846 入池）' % (
            '波动率桶' if bucket == BVOL else '成交额桶',
            ' + TOP1000' if univ else '', cid)
        combos['%s__%s' % (cid, tag)] = m

io.open(ROOT + '_autologs/leg_combos_w242.json', 'w', encoding='utf-8').write(
    json.dumps(combos, ensure_ascii=False, indent=1))
report.append('')
report.append('w242 combos = %d' % len(combos))
io.open(ROOT + '_autologs/_w242_gen.txt', 'w', encoding='utf-8').write('\n'.join(report))
print('ok')
