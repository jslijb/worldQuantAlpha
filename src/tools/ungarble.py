# -*- coding: utf-8 -*-
"""ungarble.py —— 还原被 PowerShell 重定向搞坏的中文输出

成因：python 以 UTF-8 写 stdout → PowerShell 按 CP936 解码 → 再写成 UTF-16。
还原：UTF-16 解码 → CP936 编码 → UTF-8 解码。

用法：python src/tools/ungarble.py <输入> [输出]
      不传输出则打印到 stdout，并把结果写同目录 <名>.clean.txt
"""
import sys, pathlib as _pl


def ungarble(raw: bytes) -> str:
    txt = raw.decode('utf-16', errors='ignore')
    if 'SF=' not in txt and '\x00' not in txt[:200]:
        txt = raw.decode('utf-8', errors='ignore')
    best = txt
    for enc in ('cp936', 'gbk', 'latin-1'):
        try:
            back = txt.encode(enc, errors='ignore').decode('utf-8', errors='ignore')
        except Exception:
            continue
        # 还原成功的判据：中文变多了、乱码块变少了
        if back.count('\ufffd') <= txt.count('\ufffd') and _score(back) > _score(best):
            best = back
    return best


def _score(s: str) -> int:
    han = sum(1 for ch in s if '\u4e00' <= ch <= '\u9fff')
    bad = s.count('\ufffd')
    return han - bad * 3


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    src = _pl.Path(sys.argv[1])
    out = _pl.Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix('.clean.txt')
    txt = ungarble(src.read_bytes())
    out.write_text(txt, encoding='utf-8')
    print(f'→ {out}')
