# -*- coding: utf-8 -*-
"""run_judge_file.py —— 从 _passers59.txt 读 id、剔除台账已提交的，再跑 judge_now
用法：python run_judge_file.py [id列表文件，默认 _passers59.txt]
"""
import io, sys, os, runpy
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
os.chdir(ROOT)
fn = sys.argv[1] if len(sys.argv) > 1 else '_passers59.txt'
ids = [x for x in io.open(ROOT / '_autologs' / fn, encoding='utf-8').read().split() if x]
led = io.open(ROOT / 'data/alpha_quality_analysis/SUBMITTED_LEDGER.csv', encoding='utf-8-sig').read()
submitted = set()
for ln in led.splitlines()[1:]:
    aid = ln.split(',')[0].strip().strip('"')
    if aid:
        submitted.add(aid)
ids = [i for i in ids if i not in submitted]
print('待判 %d 条（剔除已提交后）' % len(ids), flush=True)
sys.argv = ['judge_now.py'] + ids
runpy.run_path(str(ROOT / '_autologs/judge_now.py'), run_name='__main__')
