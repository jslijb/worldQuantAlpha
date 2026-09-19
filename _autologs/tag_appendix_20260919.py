# -*- coding: utf-8 -*-
"""给旧 methodology 文档头部加降级声明（一次性工具）"""
import pathlib

ROOT = pathlib.Path(r"D:\Python\worldquant\docs\methodology")
FILES = [
    "01_骨架与配方/01_黄金骨架库.md",
    "02_参数与设置/01_参数甜点表.md",
    "03_过墙与提交/01_相关性墙破法.md",
    "04_失败模式/01_checks_FAIL全解.md",
    "05_历史因子复盘/01_历史资产盘点.md",
    "05_历史因子复盘/02_低质量因子升级动作.md",
    "06_打法手册/PLAYBOOK.md",
]
HEADER = (
    "> **[历史附录 · 2026-09-19 降级]** 本文结论以 [`00_总纲.md`](../00_总纲.md) 为准；"
    "与总纲冲突处一律按总纲。本文保留原貌，作为判死/实证过程的证据链，不再更新。\n\n"
)

for rel in FILES:
    p = ROOT / rel
    text = p.read_text(encoding="utf-8")
    if "历史附录" in text.split("\n", 1)[0] or "[历史附录" in text[:200]:
        print("skip (already tagged):", rel)
        continue
    p.write_text(HEADER + text, encoding="utf-8")
    print("tagged:", rel)
