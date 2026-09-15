# -*- coding: utf-8 -*-
"""补全表达式库：把脚本里抽出的全部原始片段（含被过滤的）追加进去，确保删除前的信息零丢失"""
import json
from pathlib import Path
ROOT = Path(r'D:\Python\worldquant')
d = json.load(open(ROOT / '_autologs' / 'expr_all.json', encoding='utf-8'))
py_only = d['py_only']
lib = ROOT / 'src' / 'archive' / 'expr_library.py'
txt = lib.read_text(encoding='utf-8')
# 已在库里的
import re
alr = set(re.findall(r"^\s+'(.+?)',$", txt, re.M))
missing = [e for e in py_only if e not in alr]
print('py_only 总数:', len(py_only), ' 库中缺失:', len(missing))
if missing:
    add = ['', '# ---- 脚本独有原始片段补全（含模板/代码片段，未经筛选，确保零丢失）----',
           'PY_ONLY_RAW = [']
    for e in missing:
        add.append('    %r,' % e)
    add += [']', '']
    lib.write_text(txt.rstrip('\n') + '\n' + '\n'.join(add), encoding='utf-8')
    print('已追加', len(missing), '条')
# 验证库可导入
import importlib.util
spec = importlib.util.spec_from_file_location('expr_library', lib)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
print('库导入校验: ALL_EXPR=%d  LEG_VALUE=%d  PY_ONLY=%d  QUALIFIED=%d' % (
    len(m.ALL_EXPR), len(m.LEG_VALUE), len(m.PY_ONLY), len(m.QUALIFIED)))
