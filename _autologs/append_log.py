# -*- coding: utf-8 -*-
"""append_log.py —— 向 daily log 追加小节；旧文件 GBK 混杂 → 统一转 UTF-8 后追加"""
import os, sys
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
os.chdir(ROOT)
TARGET = ROOT / '.workbuddy/memory/2026-09-22.md'
SRC = ROOT / '_autologs/_section25.md'
raw = TARGET.read_bytes()
txt = None
for e in ('utf-8-sig', 'utf-8', 'gbk', 'cp936'):
    try:
        txt = raw.decode(e)
        print('原编码:', e)
        break
    except Exception:
        continue
if txt is None:
    txt = raw.decode('gbk', errors='replace')
    print('原编码: gbk(replace)')
sec = SRC.read_bytes().decode('utf-8')
TARGET.write_bytes((txt + sec).encode('utf-8'))
print('已追加并统一为 UTF-8，新大小', len((txt + sec).encode('utf-8')))
