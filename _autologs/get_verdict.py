# -*- coding: utf-8 -*-
"""取指定 alpha 的完整提交判决书（POST /alphas/{id}/submit 的 403 回执全文）。"""
import json, io, sys, requests

aid = sys.argv[1] if len(sys.argv) > 1 else 'j2Az8n0E'
R = io.open('_autologs/_verdict_%s.txt' % aid, 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

r = S.post('https://api.worldquantbrain.com/alphas/%s/submit' % aid)
log('POST status = %s' % r.status_code)
log('headers: Retry-After=%s Location=%s' % (r.headers.get('Retry-After'), r.headers.get('Location')))
log('')
try:
    j = r.json()
except Exception:
    log('raw: %s' % r.text[:2000])
    j = None

if isinstance(j, dict):
    chk = ((j.get('is') or {}).get('checks') or [])
    log('--- checks (%d) ---' % len(chk))
    for c in chk:
        log('  %-30s %-8s limit=%-8s value=%s' % (c.get('name'), c.get('result'), c.get('limit'), c.get('value')))
    fails = [c.get('name') for c in chk if c.get('result') == 'FAIL']
    log('')
    log('FAILS = %s' % (fails or 'NONE  ← 无 FAIL，不应记为拒信'))
    sc = (j.get('is') or {}).get('selfCorrelated') or {}
    if sc:
        log('')
        log('selfCorrelated: %s' % json.dumps(sc, ensure_ascii=False)[:1500])
    log('')
    log('full json:')
    log(json.dumps(j, ensure_ascii=False, indent=1)[:6000])
