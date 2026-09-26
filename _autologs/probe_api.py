# -*- coding: utf-8 -*-
import json, io, sys
import requests

_R = io.open('_autologs/probe_api.txt', 'w', encoding='utf-8')


def log(s):
    _R.write(str(s) + '\n')
    _R.flush()


S = requests.Session()
S.auth = tuple(json.load(io.open('brain_credentials.txt', encoding='utf-8')))
S.post('https://api.worldquantbrain.com/authentication')

for path, params in [
    ('https://api.worldquantbrain.com/users/self/alphas', {'limit': 3, 'offset': 0, 'order': '-dateSubmitted'}),
    ('https://api.worldquantbrain.com/users/self/alphas', {'limit': 3, 'offset': 0}),
]:
    r = S.get(path, params=params)
    log('URL=%s params=%s' % (path, params))
    log('status=%s ctype=%s len=%d' % (r.status_code, r.headers.get('content-type'), len(r.text)))
    log('raw[:600]=%s' % r.text[:600])
    log('-' * 70)

r = S.get('https://api.worldquantbrain.com/users/self')
log('self status=%s' % r.status_code)
log(r.text[:900])
