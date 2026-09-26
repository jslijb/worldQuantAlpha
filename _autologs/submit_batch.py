# -*- coding: utf-8 -*-
"""submit_batch.py —— 指定 alpha id 列表连续提交，每条自带 UTF-8 记录（自写）"""
import io, json, subprocess, sys, os

ROOT = 'D:/Python/worldquant/'
PY = sys.executable
IDS = [
    ('KPNwG8Oj', '0920-w189bdv-d6'),   # w189_01__g_bdv__d6  S2.58 F2.06 TO24.7% tS1.84 需≥2.55
    ('78NKjWL1', '0920-w41b-d4'),      # w41_b__d4           S3.19 F2.31 TO28.3% tS2.80 需≥~2.71
    ('QPb5G6ZQ', '0920-w39i-d4'),      # w39_i__d4           S3.20 F2.27 TO25.5% tS3.06 需≥~3.10
]

L = []
for aid, tag in IDS:
    r = subprocess.run([PY, ROOT + 'src/submit/submit_v3.py', aid, tag],
                       capture_output=True, text=True, timeout=600, cwd=ROOT,
                       encoding='utf-8', errors='replace')
    out = (r.stdout or '') + (r.stderr or '')
    keep = [x for x in out.splitlines()
            if ('POST /submit' in x or 'verdict' in x or 'selfCorr' in x
                or '台账' in x or 'FAIL' in x or 'REJECT' in x)]
    L.append('=== %s  (%s) ===' % (aid, tag))
    L += ['  ' + x for x in (keep or out.splitlines()[-4:])]
    L.append('')

io.open(ROOT + '_autologs/_submit_batch.txt', 'w', encoding='utf-8').write('\n'.join(L))
print('ok')
