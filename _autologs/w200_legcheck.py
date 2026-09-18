# -*- coding: utf-8 -*-
"""检查 w200 日内主导批所需的腿 PnL 是否就位"""
import os, json, pathlib as pl
os.chdir(r'D:\Python\worldquant')
MINED = 'data/alpha_quality_analysis/mined'
out = []

def cid2id(cid):
    alias = {'P_int20': 'x180_leg_int', 'M_cov': 'x180_leg_cov'}
    if cid in alias:
        p = pl.Path(MINED) / (alias[cid] + '.json')
        if p.exists():
            d = json.load(open(p, encoding='utf-8'))
            if d.get('id'):
                return d['id']
    if len(cid) == 8 and cid.isalnum():
        return cid
    p = pl.Path(MINED) / (cid + '.json')
    if p.exists():
        d = json.load(open(p, encoding='utf-8'))
        if d.get('id'):
            return d['id']
    for h in pl.Path(MINED).glob('*.json'):
        try:
            d = json.load(open(h, encoding='utf-8'))
        except Exception:
            continue
        if d.get('_cid') == cid and d.get('id'):
            return d['id']
    return None

need = ['P_on5', 'P_int20', 'P_vd', 'P_sd20',
        'L_cfo', 'L_cash', 'L_xr', 'L_int', 'L_acc',
        'M_intc', 'M_g12', 'M_debt', 'M_tstk', 'M_accI', 'M_intI', 'M_cfoQ', 'M_lnoq']
cache = set(f[:-5] for f in os.listdir('data/alpha_quality_analysis/pnl'))
for l in need:
    aid = cid2id(l)
    has_pnl = aid in cache if aid else False
    out.append('%-8s id=%-9s pnl_cache=%s' % (l, aid or 'NONE', has_pnl))
open('_autologs/w200_legcheck.txt', 'w', encoding='utf-8').write('\n'.join(out))
