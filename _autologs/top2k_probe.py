# -*- coding: utf-8 -*-
"""top2k_probe.py —— 看撞墙的 TOP2000 候选是什么骨架、值不值得换挡改造"""
import os as _os, pathlib as _pl, json, io
_p = _pl.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / 'brain_credentials.txt').exists():
        _os.chdir(_d); break

IDS = ['YP58Mr5l', 'A10ev37X', 'O0rR8mjg', 'd5OY1Xgv', 'GrdXOVGP', 'O0r6VZzJ', 'vRkYpk1a']
data = json.load(io.open('data/alpha_quality_analysis/raw_from_api/all_unsubmitted.json', encoding='utf-8'))
if isinstance(data, dict):
    data = data.get('results', [])
L = []
seen_expr = {}
for a in data:
    if a.get('id') not in IDS:
        continue
    st = a.get('settings') or {}
    b = a.get('is') or {}
    code = ((a.get('regular') or {}).get('code') or '')
    L.append('=' * 100)
    L.append('%s  %s/%s d%s dec%s trunc%s delay%s   S=%.2f F=%.2f TO=%.4f tS=%.2f op=%s'
             % (a['id'], st.get('universe'), st.get('neutralization'), st.get('delay'),
                st.get('decay'), st.get('truncation'), st.get('delay'),
                b.get('sharpe') or 0, b.get('fitness') or 0, b.get('turnover') or 0,
                (a.get('test') or {}).get('sharpe') or 0, a.get('operatorCount')))
    L.append('  %s' % code[:520])
    seen_expr.setdefault(code, []).append(a['id'])

L.append('')
L.append('=' * 100)
L.append('去重后骨架 = %d 个' % len(seen_expr))
for k, v in seen_expr.items():
    L.append('  %s  <= %s' % (v, k[:120]))

# 这些表达式在池子里有没有 TOP3000 版（说明只是换了池，材质相同）
L.append('')
L.append('同表达式在平台其它池的版本（含已提交池）：')
sub = set()
for ln in io.open('data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig'):
    p = ln.split(',', 1)
    if p and p[0].strip() and p[0].strip() != 'id':
        sub.add(p[0].strip().strip('"'))
allsame = {}
for a in data:
    code = ((a.get('regular') or {}).get('code') or '')
    if code in seen_expr:
        st = a.get('settings') or {}
        allsame.setdefault(code, []).append((a['id'], st.get('universe'), 'OS' if a['id'] in sub else 'IS'))
for k, v in allsame.items():
    L.append('  ' + str(v))

io.open('_autologs/_top2k_probe.txt', 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('done')
