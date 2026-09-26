# -*- coding: utf-8 -*-
"""核实指定 alpha 的平台真实状态 + 统计 ACTIVE 总数。"""
import json, io, requests

R = io.open('_autologs/_verify_status.txt', 'w', encoding='utf-8')


def log(s):
    R.write(str(s) + '\n')
    R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

CHECK = ['j2Az8n0E', 'blRmGJ9r', 'O0N55k1Y', 'E5prgA1K', 'O0NP30KR']
for aid in CHECK:
    r = S.get('https://api.worldquantbrain.com/alphas/%s' % aid)
    if r.status_code != 200:
        log('%s HTTP %s' % (aid, r.status_code))
        continue
    a = r.json()
    i = a.get('is') or {}
    t = a.get('test') or {}
    log('%s status=%-14s dateSubmitted=%s  S=%.2f F=%.2f tS=%.2f TO=%.1f%%' % (
        aid, a.get('status'), a.get('dateSubmitted'), i.get('sharpe') or 0,
        i.get('fitness') or 0, t.get('sharpe') or 0, (i.get('turnover') or 0) * 100))

# 平台 ACTIVE 总数（分页取前 400 条已提交）
rows, off = [], 0
while len(rows) < 400:
    r = S.get('https://api.worldquantbrain.com/users/self/alphas',
              params={'limit': 100, 'offset': off, 'order': '-dateSubmitted'})
    j = r.json()
    if isinstance(j, list):
        log('PAGE-ERR list at off=%d' % off)
        break
    res = j.get('results') or []
    if not res:
        break
    rows += res
    off += len(res)
    if off >= j.get('count', 0):
        break
sub = [a for a in rows if a.get('dateSubmitted')]
act = [a for a in sub if a.get('status') == 'ACTIVE']
log('')
log('fetched=%d  submitted=%d  ACTIVE=%d' % (len(rows), len(sub), len(act)))
