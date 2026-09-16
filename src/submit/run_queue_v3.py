# -*- coding: utf-8 -*-
# 串行提交队列（调 submit_v3.py，一次一个，绝不并发）
# 用法: python run_queue_v3.py w122_b w126_h w126_g w125_c w124_e w125_f w125_a w125_d
import subprocess, json, csv, sys, os

PY = sys.executable
cids = sys.argv[1:]
assert cids, '给出 cid 列表'

# 已入池 id（跳过）
done = set()
led = 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv'
if os.path.exists(led):
    for r in csv.DictReader(open(led, encoding='utf-8-sig')):
        if r.get('id'): done.add(r['id'].strip())

# 已有裁决的（ACCEPTED/REJECTED 都算已决，跳过；TIMEOUT 可重试）
decided = {}
vd = 'data/alpha_quality_analysis/SUBMIT_VERDICTS.csv'
if os.path.exists(vd):
    for r in csv.DictReader(open(vd, encoding='utf-8-sig')):
        if r.get('alpha_id'): decided[r['alpha_id']] = r['verdict']

for cid in cids:
    f = f'data/alpha_quality_analysis/mined/{cid}.json'
    if not os.path.exists(f):
        print(f'[skip] {cid}: mined json 不存在'); continue
    d = json.load(open(f, encoding='utf-8'))
    aid = d.get('id')
    if not aid: print(f'[skip] {cid}: 无 id'); continue
    if aid in done: print(f'[skip] {cid} {aid}: 已在台账'); continue
    if decided.get(aid) in ('ACCEPTED', 'REJECTED'):
        print(f'[skip] {cid} {aid}: 已有裁决 {decided[aid]}'); continue
    print(f'\n########## 提交 {cid} = {aid} ##########', flush=True)
    rc = subprocess.call([PY, 'src/submit/submit_v3.py', aid, cid])
    if rc != 0:
        print(f'{cid} 提交脚本异常退出({rc})，停止队列'); sys.exit(1)
print('\n=== 队列执行完毕 ===')
