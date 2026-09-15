#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把同一官方课程下的多个「视频中英对照」md 合并成一份合集文档。

背景
----
平台 Learn 一个课程组（video-course）常含多个视频。逐个存成 md 会让
`docs/study/learn/` 文件数爆炸、难以检索。本脚本按官方课程组把同一组的
视频译文合并为**一份**合集，内部保留每个视频的完整中英对照。

输入文件约定（由人工/前序步骤生成）
----
每个视频 md 采用统一体例：
    # 视频 NN｜标题 — 中英逐段对照
    > 归档信息（引用块）
    ## 一、中文译文
    ## 二、英文原文（官方 transcript，逐段）
    ## 三、字幕勘误（官方字幕为自动生成）
    ## 四、本视频的量化术语对照
    ## 五、与本视频相关的面试考点

合并后结构
----
    # 课程合集标题
    > 合集归档信息
    ## 目录（视频清单）
    ---
    # 视频 1｜…（正文：中文译文 + 英文原文）
    # 视频 2｜…
    ---
    # 附录 A：字幕勘误汇总
    # 附录 B：术语总表（跨视频合并去重）
    # 附录 C：面试考点汇总（按视频分节）

用法
----
    python src/tools/merge_video_notes.py \
        --title "Alpha 入门培训系列（introduction-alphas）" \
        --course-id introduction-alphas \
        --out "docs/study/learn/视频合集_Alpha入门培训系列.md" \
        docs/study/learn/视频0*.md
"""
import argparse
import pathlib
import re
import sys

SEC_RE = re.compile(r"^##\s*([一二三四五六七八九十]+)、(.+?)\s*$", re.M)


def split_sections(text: str) -> dict:
    """按 `## 一、xxx` 切段，返回 {'一': (标题, 正文), ...}。"""
    marks = [(m.start(), m.group(1), m.group(2)) for m in SEC_RE.finditer(text)]
    out = {}
    for i, (pos, num, title) in enumerate(marks):
        end = marks[i + 1][0] if i + 1 < len(marks) else len(text)
        out[num] = (title.strip(), text[pos:end].strip())
    return out


def clean_title(raw: str) -> str:
    """把源文件 H1 洗成干净的视频标题。

    源 H1 形如：`视频 01｜What is an Alpha?（什么是 Alpha）— 中英逐段对照`
    目标：     `What is an Alpha?（什么是 Alpha）`
    """
    t = raw.strip()
    t = re.sub(r"^视频\s*\d+\s*[｜|]\s*", "", t)          # 去「视频 NN｜」前缀
    t = re.sub(r"\s*[—\-–]\s*中英逐段对照\s*$", "", t)     # 去「— 中英逐段对照」后缀
    return t.strip()


def parse_head(text: str) -> tuple:
    h1 = re.search(r"^#\s*(.+?)\s*$", text, re.M)
    title = clean_title(h1.group(1)) if h1 else "(无标题)"
    # 引用块里的信息行
    meta = [l for l in text.splitlines() if l.startswith(">")]
    return title, meta


def brief_meta(meta: list) -> str:
    """从源文件归档信息里抽出「课程页 / 视频源 / 时长」，拼成一行简要信息。"""
    page, src, dur = "", "", ""
    for l in meta:
        if "课程页" in l:
            m = re.search(r"(https?://\S+)", l)
            if m:
                page = m.group(1)
        if "视频源" in l:
            src = re.sub(r"^>\s*-?\s*视频源[：:]\s*", "", l).strip()
        if "时长" in l:
            m = re.search(r"时长\s*\*\*([^*]+)\*\*", l) or re.search(r"时长\s*([0-9]+\s*分\s*[0-9]+\s*秒)", l)
            if m:
                dur = m.group(1).strip()
    bits = []
    if page:
        bits.append(f"课程页：<{page}>")
    if dur:
        bits.append(f"时长：{dur}")
    if src:
        bits.append(f"视频源：{src}")
    return " ｜ ".join(bits)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--title", required=True, help="合集标题")
    ap.add_argument("--course-id", default="", help="官方课程组 id")
    ap.add_argument("--course-url", default="", help="官方课程页 URL")
    ap.add_argument("--out", required=True)
    ap.add_argument("--no-delete-sources", action="store_true", help="保留源文件不删")
    args = ap.parse_args()

    files = [pathlib.Path(f) for f in args.files]
    files = [f for f in files if f.exists()]
    if not files:
        print("没有可用的输入文件")
        return 1

    bodies, errata, gloss, exams = [], [], [], []
    for f in files:
        text = f.read_text(encoding="utf-8")
        title, meta = parse_head(text)
        secs = split_sections(text)
        zh = secs.get("一", ("中文译文", ""))[1]
        en = secs.get("二", ("英文原文", ""))[1]
        er = secs.get("三", ("字幕勘误", ""))[1]
        gl = secs.get("四", ("术语对照", ""))[1]
        ex = secs.get("五", ("面试考点", ""))[1]
        bodies.append((f.name, title, zh, en, brief_meta(meta)))
        errata.append((title, er))
        gloss.append((title, gl))
        exams.append((title, ex))
        print(f"  解析 {f.name}: 中文{len(zh)} 英文{len(en)} 勘误{len(er)} 术语{len(gl)} 考点{len(ex)}")

    out = []
    out.append(f"# {args.title}\n")
    out.append("> **合集归档信息（本文件由多个视频译文合并而成）**")
    if args.course_id:
        out.append(f"> - 官方课程组：`{args.course_id}`")
    if args.course_url:
        out.append(f"> - 课程页：<{args.course_url}>")
    out.append(f"> - 含视频：**{len(bodies)} 个**（清单见下表）")
    out.append("> - 字幕来源：**平台官方 transcript**（`GET /video-courses`），非本地 ASR；抓取日期 2026-09-15")
    out.append("> - 译法：按量化行业习惯翻译；括号内英文为原词")
    out.append("> - 合并工具：`src/tools/merge_video_notes.py`")
    out.append("> - ⚠️ 官方字幕为自动生成，ASR 误识在各视频正文内就地标注，另见文末「附录 A：字幕勘误汇总」\n")

    out.append("## 目录\n")
    out.append("| # | 视频标题 | 源文件 |")
    out.append("|---|---|---|")
    for i, (fname, title, _, _, _) in enumerate(bodies, 1):
        out.append(f"| {i} | {title} | `{fname}` |")
    out.append("\n---\n")

    for i, (fname, title, zh, en, meta) in enumerate(bodies, 1):
        out.append(f"# 视频 {i}｜{title}\n")
        if meta:
            out.append(f"> {meta}")
        out.append(f"> 源文件：`{fname}`\n")
        out.append(zh + "\n")
        out.append(en + "\n")
        out.append("\n---\n")

    out.append("# 附录 A：字幕勘误汇总（官方字幕为自动生成）\n")
    out.append("> 各视频正文内已就地标注，此处汇总便于速查。\n")
    for title, er in errata:
        if not er:
            continue
        body = re.sub(r"^##\s*三、.+\n*", "", er).strip()
        out.append(f"### {title}\n")
        out.append(body + "\n")

    out.append("\n---\n")
    out.append("# 附录 B：术语总表（跨视频合并去重）\n")
    out.append("> 按英文术语去重；同一术语在多个视频出现时保留首次出现处的解释。\n")
    seen = {}
    for title, gl in gloss:
        body = re.sub(r"^##\s*四、.+\n*", "", gl).strip()
        for line in body.splitlines():
            m = re.match(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*$", line)
            if not m:
                continue
            key = m.group(1)
            if key in ("英文", "---", "") or set(key) <= set("-: "):
                continue
            if key not in seen:
                seen[key] = (m.group(2), m.group(3), m.group(4))
    if seen:
        # 判断来源表有没有第 4 列（公式/口径）
        has4 = any(v[2] for v in seen.values())
        out.append("| 英文 | 中文 | 说明 |" + (" 公式 / 口径 |" if has4 else ""))
        out.append("|---|---|---|" + ("---|" if has4 else ""))
        for k, (cn, desc, extra) in sorted(seen.items(), key=lambda x: x[0].lower()):
            out.append(f"| {k} | {cn} | {desc} |" + (f" {extra} |" if has4 else ""))
    out.append("")

    out.append("\n---\n")
    out.append("# 附录 C：面试考点汇总\n")
    for i, (title, ex) in enumerate(exams, 1):
        if not ex:
            continue
        body = re.sub(r"^##\s*五、.+\n*", "", ex).strip()
        out.append(f"## 视频 {i}｜{title}\n")
        out.append(body + "\n")

    md = "\n".join(out)
    md = re.sub(r"\n{4,}", "\n\n\n", md)
    target = pathlib.Path(args.out)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(md, encoding="utf-8")
    print(f"\n[已写] {target}  ({len(md)} 字符, {md.count(chr(10))} 行)")

    if not args.no_delete_sources:
        for f in files:
            f.unlink()
            print(f"[已删源文件] {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
