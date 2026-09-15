#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_snapshot.py — 项目变更快照提交（唯一入口）

用途：每挖完一批 Alpha 因子（或完成一轮提交 / 文档更新）后调用一次，
      把变更提交进本地 git 仓库。自动识别变更内容并生成有意义的信息。

用法：
    python src/ops/git_snapshot.py                     # 自动识别变更、自动生成信息
    python src/ops/git_snapshot.py "补充说明"           # 追加自定义说明行
    python src/ops/git_snapshot.py --dry-run           # 只显示将要提交什么，不真提交

行为约定：
    - 无变更时静默跳过，不产生空提交
    - 只做本地 commit，不 push（本仓库无远端）
    - 首步自检 brain_credentials.txt 未被纳入版本控制，发现即中止
    - 提交前打一次凭据自检；提交后打印本次 commit 摘要

可从任意工作目录调用（自动向上定位项目根）。
"""

import os
import re
import subprocess
import sys
from pathlib import Path

LEDGER_REL = "data/alpha_quality_analysis/SUBMITTED_LEDGER.csv"
MINED_DIR_REL = "data/alpha_quality_analysis/mined"


def find_root() -> Path:
    """向上查找项目根（以 CLAUDE.md + brain_credentials.txt 为标志）。"""
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        if (parent / "CLAUDE.md").exists() and (parent / "brain_credentials.txt").exists():
            return parent
    raise SystemExit("找不到项目根：向上未发现同时含 CLAUDE.md 与 brain_credentials.txt 的目录")


ROOT = find_root()


def git(*args: str, check: bool = False) -> subprocess.CompletedProcess:
    """在项目根执行 git 命令，输出统一用 utf-8 容错解码。"""
    p = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    p.out = p.stdout.decode("utf-8", "replace")
    p.err = p.stderr.decode("utf-8", "replace")
    if check and p.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} 失败：\n{p.err}")
    return p


def collect_changes() -> list:
    """返回 [(状态码, 路径), ...]。状态码取 porcelain 前两位。"""
    p = git("status", "--porcelain")
    items = []
    for line in p.out.splitlines():
        if not line.strip():
            continue
        code, rest = line[:2], line[3:]
        if " -> " in rest:  # 重命名：取新路径
            rest = rest.split(" -> ", 1)[1]
        items.append((code, rest.strip().strip('"')))
    return items


def count_lines_from_head(rel: str):
    """读 HEAD 版本某文件的行数；文件不存在返回 None。"""
    p = git("show", f"HEAD:{rel}")
    if p.returncode != 0:
        return None
    return len([x for x in p.out.splitlines() if x.strip()])


def count_lines_now(rel: str):
    f = ROOT / rel
    if not f.exists():
        return None
    try:
        return len([x for x in f.read_text(encoding="utf-8-sig").splitlines() if x.strip()])
    except Exception:
        return None


def build_message(changes: list, note: str) -> str:
    """按变更内容组装 commit message（标题 + 正文摘要）。"""
    new_mined, mod_mined, del_mined = [], [], []
    other = []
    for code, path in changes:
        norm = path.replace("\\", "/")
        if norm.startswith(MINED_DIR_REL + "/") and norm.endswith(".json"):
            if code.strip() == "??" or code.strip() == "A":
                new_mined.append(norm)
            elif code.strip() == "D":
                del_mined.append(norm)
            else:
                mod_mined.append(norm)
        else:
            other.append((code, norm))

    # 识别挖矿批次号（w120_a.json → w120）
    batches = sorted({m.group(1) for m in
                      (re.match(r"(w\d+)_", Path(p).name) for p in new_mined) if m})

    ledger_now = count_lines_now(LEDGER_REL)
    ledger_head = count_lines_from_head(LEDGER_REL)
    ledger_delta = (ledger_now - ledger_head) if (ledger_now is not None and ledger_head is not None) else None

    docs_cnt = sum(1 for _, p in other if p.startswith("docs/") or p.endswith(".md"))
    src_cnt = sum(1 for _, p in other if p.startswith("src/"))

    # ---- 标题 ----
    parts = []
    if batches:
        b = ", ".join(batches[:4]) + (" 等" if len(batches) > 4 else "")
        parts.append(f"挖矿 {b}: +{len(new_mined)} 候选")
    elif new_mined:
        parts.append(f"挖矿: +{len(new_mined)} 候选")
    if ledger_delta is not None and ledger_delta > 0:
        parts.append(f"提交 +{ledger_delta}")
    if src_cnt:
        parts.append(f"代码 {src_cnt} 改")
    if not parts and docs_cnt:
        parts.append(f"文档 {docs_cnt} 改")
    if not parts:
        parts.append(f"杂项变更 {len(changes)} 项")

    if batches:
        head = f"mine({batches[0]}): " + " / ".join(parts)
    elif ledger_delta is not None and ledger_delta > 0:
        head = "submit: " + " / ".join(parts)
    elif docs_cnt and not new_mined:
        head = "docs: " + " / ".join(parts)
    else:
        head = "chore: " + " / ".join(parts)

    # ---- 正文 ----
    body = []
    if note:
        body.append(note)
        body.append("")
    if ledger_delta is not None and ledger_delta != 0:
        body.append(f"台账: {ledger_head} → {ledger_now} 行 ({ledger_delta:+d})")
    if new_mined:
        body.append(f"新增模拟记录: {len(new_mined)} 条")
    if mod_mined:
        body.append(f"更新模拟记录: {len(mod_mined)} 条")
    if del_mined:
        body.append(f"删除模拟记录: {len(del_mined)} 条")
        for p in del_mined[:10]:
            body.append(f"  - {p}")
    if other:
        body.append(f"其他变更: {len(other)} 项")
        for code, p in sorted(other, key=lambda x: x[1])[:25]:
            body.append(f"  {code.strip():2} {p}")
        if len(other) > 25:
            body.append(f"  ... 另有 {len(other) - 25} 项")

    return head, "\n".join(body)


def main() -> int:
    argv = [a for a in sys.argv[1:]]
    dry = "--dry-run" in argv or "-n" in argv
    argv = [a for a in argv if a not in ("--dry-run", "-n")]
    note = argv[0] if argv else ""

    # ---- 前置自检 1：仓库存在 ----
    if not (ROOT / ".git").exists():
        print("[中止] 项目尚未初始化 git 仓库，请先运行：git init -b main")
        return 1

    # ---- 前置自检 2：凭据绝不被跟踪（红线） ----
    tracked = git("ls-files", "--error-unmatch", "brain_credentials.txt")
    if tracked.returncode == 0:
        print("[中止·红线] brain_credentials.txt 已被纳入版本控制！")
        print("  立即修复：git rm --cached brain_credentials.txt")
        print("  并确认 .gitignore 首节含 brain_credentials.txt")
        return 2

    # ---- 前置自检 3：暂存区无凭据文件 ----
    staged = git("diff", "--cached", "--name-only")
    for line in staged.out.splitlines():
        if Path(line.strip()).name == "brain_credentials.txt":
            print("[中止·红线] 暂存区出现 brain_credentials.txt，拒绝提交")
            return 2

    changes = collect_changes()
    if not changes:
        print("无变更，跳过提交（不产生空提交）")
        return 0

    head, body = build_message(changes, note)
    full = head if not body else f"{head}\n\n{body}"

    print(f"项目根: {ROOT}")
    print(f"变更项: {len(changes)}")
    print("-" * 56)
    print(full)
    print("-" * 56)

    if dry:
        print("[dry-run] 未真正提交")
        return 0

    git("add", "-A", check=True)
    cp = subprocess.run(
        ["git", "commit", "-F", "-"],
        cwd=str(ROOT), input=full.encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    out = cp.stdout.decode("utf-8", "replace")
    err = cp.stderr.decode("utf-8", "replace")
    if cp.returncode != 0:
        print("[提交失败]")
        print(out or err)
        return 3

    log = git("log", "-1", "--stat", "--format=%h %ad %s", "--date=format:%Y-%m-%d %H:%M")
    print(log.out.strip())
    print("\n[完成] 已提交到本地仓库（未 push，本仓库无远端）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
