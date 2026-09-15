#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
git_snapshot.py — 项目变更快照提交（唯一入口）

用途：每挖完一批 Alpha 因子（或完成一轮提交 / 文档更新）后调用一次，
      把变更提交进本地 git 仓库。自动识别变更内容并生成有意义的信息。

用法：
    python src/ops/git_snapshot.py                     # 自动识别变更 → 提交 → 推送到远端
    python src/ops/git_snapshot.py "补充说明"           # 追加一行自定义说明
    python src/ops/git_snapshot.py --dry-run           # 只显示将要提交什么，不真提交
    python src/ops/git_snapshot.py --no-push           # 只提交本地，不推送
    python src/ops/git_snapshot.py --allow-public      # 允许推送到公开仓库（默认拦截）

行为约定：
    - 无变更时静默跳过，不产生空提交
    - 提交后若配置了远端 origin 则自动推送（--no-push 跳过）
    - ★ 推送前探测远端可见性：检测到 GitHub 公开仓库即拦截并告警（alpha 表达式属核心资产，不外泄）
    - 首步自检 brain_credentials.txt 未被纳入版本控制，发现即中止
    - 提交后打印本次 commit 摘要；推送失败不阻断本地提交

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
    mined_cnt = len(new_mined)
    if mined_cnt:
        if len(batches) <= 1:
            parts.append(f"新增 {mined_cnt} 条候选")
        else:
            b = ", ".join(batches[:3]) + (" 等" if len(batches) > 3 else "")
            parts.append(f"{b} 共新增 {mined_cnt} 条候选")
    elif mod_mined:
        parts.append(f"更新 {len(mod_mined)} 条模拟记录")
    if ledger_delta and ledger_delta > 0:
        parts.append(f"台账 +{ledger_delta}")
    if src_cnt:
        parts.append(f"代码 {src_cnt} 项")
    if docs_cnt:
        parts.append(f"文档 {docs_cnt} 项")

    if not parts:
        parts.append(f"杂项变更 {len(changes)} 项")

    # 前缀：优先体现"挖矿"与"提交"这两类主线动作
    if len(batches) == 1:
        prefix = f"mine({batches[0]})"
    elif batches or mod_mined:
        prefix = "mine"
    elif ledger_delta and ledger_delta > 0:
        prefix = "submit"
    elif src_cnt and not docs_cnt:
        prefix = "code"
    elif docs_cnt and not src_cnt:
        prefix = "docs"
    else:
        prefix = "chore"

    head = f"{prefix}: " + " / ".join(parts)

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


def remote_visibility(url: str) -> str:
    """探测远端是否为公开仓库（仅对 github.com 有效）。

    返回 'public' / 'not-public' / 'unknown'。
    原理：匿名 HEAD 请求仓库主页——200 = 公开，404 = 私有或不存在。
    """
    m = re.match(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", url.strip())
    if not m:
        return "unknown"
    import urllib.error
    import urllib.request

    req = urllib.request.Request(
        f"https://github.com/{m.group(1)}/{m.group(2)}",
        method="HEAD",
        headers={"User-Agent": "git-snapshot/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return "public" if r.status == 200 else "unknown"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return "not-public"   # 私有，或不存在（push 时自会报错）
        return "unknown"
    except Exception:
        return "unknown"


def main() -> int:
    argv = list(sys.argv[1:])
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

    # ---------- 推送远端 ----------
    url = git("remote", "get-url", "origin").out.strip()
    if not url:
        print("\n[完成] 已提交到本地仓库（未配置远端 origin，未推送）")
        return 0
    if no_push:
        print("\n[完成] 已提交到本地仓库（--no-push 指定跳过推送）")
        return 0

    vis = remote_visibility(url)
    if vis == "public" and not allow_public:
        print(f"\n[拦截推送·红线] 远端 {url} 是**公开仓库**。")
        print("  本项目含 1098 条 alpha 表达式、提交台账与完整方法论，")
        print("  推送到公开仓库后无法撤回（会被克隆/索引）。")
        print("  处理办法（任选其一）：")
        print("    1. GitHub 仓库 Settings → General → Danger Zone → Change visibility 改为 Private")
        print("    2. 确认要公开：显式加参数 --allow-public")
        print("  本地提交已保存，不受影响。")
        return 4

    print(f"\n远端 {url}（可见性: {vis}），正在推送 …")
    r = git("push", "-u", "origin", "HEAD")
    if r.returncode == 0:
        print(f"[完成] 已推送到 {url}")
    else:
        print("[警告] 推送失败（本地提交已保存，不受影响）：")
        print((r.err or r.out).strip()[:600])
        print("  常见原因：未登录 GitHub（首次推送会弹出登录窗口）/ 网络不通 / 无仓库写权限")
    return 0


if __name__ == "__main__":
    sys.exit(main())
