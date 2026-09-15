# -*- coding: utf-8 -*-
import json, requests
sess = requests.Session()
sess.auth = tuple(json.load(open('brain_credentials.txt')))
assert sess.post('https://api.worldquantbrain.com/authentication').status_code == 201

fields = [
    'fnd6_newq_xoptdqp',            # w126_a 锚 aC=9
    'fnd6_newqv1300_spceepsq',      # w126_b 锚 aC=9
    'fnd6_newqv1300_pncq',          # w126_c 锚 aC=16
    'fnd6_newqv1300_tfvceq',        # w126_g 新增锚 aC=87
    'fnd6_newqv1300_pncepsq',       # w126_f 报 unknown variable
    # 对照组：已验证有数据的
    'fnd6_newqv1300_cicurrq',       # E3 锚
    'fnd6_newqv1300_spcep12',       # w125_g 锚 aC=9
]
for f in fields:
    try:
        r = sess.get(f'https://api.worldquantbrain.com/data-fields/{f}')
        if r.status_code != 200:
            print('%-32s HTTP %d %s' % (f, r.status_code, r.text[:80]))
            continue
        d = r.json()
        print('%-32s coverage=%s  alphaCount=%s  type=%s' % (
            f, d.get('coverage'), d.get('alphaCount'), d.get('type')))
    except Exception as e:
        print(f, 'EXC', e)
