# -*- coding: utf-8 -*-
"""拉取指定 alpha 的完整表达式与指标，用于提炼低换手高F模板。"""
import json, io, sys
import requests

_R = io.open('_autologs/top_quality_formulas.txt', 'w', encoding='utf-8')


def log(s):
    _R.write(str(s) + '\n')
    _R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

# 高F低换手样板 + 高换手对照
IDS = ['pwRwWoJ3', 'ZYbPbXj1', '9qjqm3Q9', 'e79PvPpE', 'levpXXGl', 'QPbP6aRQ',
       'O0N0R5NY', '9qjqm3Q9',
       '1YX6MA0M', '0mR2K6lr', 'mLgd6nwX', 'e79kPeEM', 'kqjpepz8',
       'N1QxNQK7', 'qMW92Az2', '1YwRK1wW', '9qX8Nr6r', '9qX3M2mq']

seen = set()
for aid in IDS:
    if aid in seen:
        continue
    seen.add(aid)
    r = S.get('https://api.worldquantbrain.com/alphas/%s' % aid)
    if r.status_code != 200:
        log('%s  HTTP %s' % (aid, r.status_code))
        continue
    a = r.json()
    i = a.get('is') or {}
    t = a.get('test') or {}
    st = a.get('settings') or {}
    log('=' * 78)
    log('%s  S=%.2f F=%.2f tS=%.2f TO=%.1f%% ret=%.1f%% DD=%.1f%% margin=%.2fbp grade=%s' % (
        aid, i.get('sharpe') or 0, i.get('fitness') or 0, t.get('sharpe') or 0,
        (i.get('turnover') or 0) * 100, (i.get('returns') or 0) * 100,
        (i.get('drawdown') or 0) * 100, (i.get('margin') or 0) * 1e4, a.get('grade')))
    log('set: univ=%s neut=%s decay=%s trunc=%s delay=%s nan=%s' % (
        st.get('universe'), st.get('neutralization'), st.get('decay'),
        st.get('truncation'), st.get('delay'), st.get('nanHandling')))
    log('expr:')
    log('  ' + ((a.get('regular') or {}).get('code') or ''))
log('DONE')
