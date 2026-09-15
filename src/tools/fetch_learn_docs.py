#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""抓取 BRAIN 平台 Learn **文档**（tutorial-pages）原文：文字 + 表格 + 图片 + 视频链接。

背景
----
平台 Learn 有两套内容：
  1. **文档**（documentation）：`GET /tutorials` 返回目录树（课程 → 页面），
     `GET /tutorial-pages/{page_id}` 返回单页正文（content 块数组）。
  2. **视频课程**（courses）：`GET /video-courses`（见 fetch_learn_video.py）。

本脚本只处理第 1 套。文档页面是 SPA，直接抓 HTML 拿不到正文，
但走登录态 API 可以拿到结构化 content（TEXT / HEADING / TABLE 块）。

用法
----
    python src/tools/fetch_learn_docs.py tree                      # 打印官方目录树
    python src/tools/fetch_learn_docs.py tree --json               # 存目录树 JSON
    python src/tools/fetch_learn_docs.py page <page_id>            # 抓单页 → _autologs/learn_docs/
    python src/tools/fetch_learn_docs.py page <page_id> --out docs/study/learn/03_xxx.md
    python src/tools/fetch_learn_docs.py page <page_id> --no-images

产出
----
  - `_autologs/learn_docs/tutorials.json`      目录树原始 JSON
  - `_autologs/learn_docs/{page_id}.json`      单页原始 JSON（未加工，证据留档）
  - 目标 md 文件（--out 指定，或默认 `_autologs/learn_docs/{page_id}.md`）
  - 图片默认落到 md 同目录的 `images/{page_id}/`

说明
----
  - 图片 URL 形如 `https://api.worldquantbrain.com/content/images/{hash}/{n}/original/`，
    **需要登录态**才能下载，脚本已带 session。
  - 页面里的视频是 YouTube iframe 嵌入（可能带 start/end 秒数），
    本脚本保留为链接并标注时间区间；**不下载视频**。
"""
import argparse
import html as html_mod
import json
import os
import pathlib
import re
import sys

import requests

BASE = "https://api.worldquantbrain.com"
IMG_HOST = "https://api.worldquantbrain.com"

# --- 向上定位项目根 ---
_p = pathlib.Path(__file__).resolve()
for _d in [_p.parent, *_p.parents]:
    if (_d / "brain_credentials.txt").exists():
        os.chdir(_d)
        break


def login() -> requests.Session:
    user, pwd = json.loads(
        pathlib.Path("brain_credentials.txt").read_text(encoding="utf-8-sig")
    )
    s = requests.Session()
    s.auth = (user, pwd)
    r = s.post(f"{BASE}/authentication", timeout=30)
    r.raise_for_status()
    return s


# ---------------------------------------------------------------- 目录树

def fetch_tutorials(s: requests.Session) -> dict:
    r = s.get(f"{BASE}/tutorials", params={"limit": 100}, timeout=60)
    r.raise_for_status()
    return r.json()


def print_tree(data: dict) -> None:
    print(f"官方 Learn 文档目录（共 {data['count']} 个课程）\n")
    for c in sorted(data["results"], key=lambda x: x.get("sequence") or 0):
        pages = c.get("pages", [])
        print(f"■ {c['id']}  |  {c.get('category')}  |  {len(pages)} 页")
        for p in pages:
            dur = p.get("duration") or "-"
            print(f"    {p['id']:56s} {dur:8s} {p['title']}")
        print()


# ---------------------------------------------------------------- 正文转换

RE_IMG = re.compile(r"<img\s+[^>]*?src=[\"']?([^\"'\s>]+)[\"']?[^>]*>", re.I | re.S)
RE_IFRAME_SRC = re.compile(r'<iframe[^>]*?src=["\']([^"\']+)["\']', re.I | re.S)


def _iframe_to_md(tag: str) -> str:
    """YouTube 等内嵌播放器 → 文字标注 + 链接（含时间区间）。"""
    m = RE_IFRAME_SRC.search(tag)
    if not m:
        return "[内嵌视频（未取到地址）]"
    url = html_mod.unescape(m.group(1))
    yt = re.search(r"(?:youtube\.com/embed/|youtu\.be/)([\w-]{6,})", url)
    if yt:
        vid = yt.group(1)
        start = re.search(r"[?&]start=(\d+)", url)
        end = re.search(r"[?&]end=(\d+)", url)
        rng = ""
        if start:
            rng = f"（{int(start.group(1))}s" + (f" ~ {int(end.group(1))}s）" if end else " 起）")
        watch = f"https://www.youtube.com/watch?v={vid}"
        if start:
            watch += f"&t={start.group(1)}s"
        return f"> 🎬 **内嵌视频**{rng}：<{watch}>"
    return f"> 🎬 **内嵌视频**：<{url}>"


def html_to_md(raw: str, image_map: dict) -> str:
    """把 tutorial-pages 的 HTML 片段转成 Markdown。

    image_map: {原始图片 URL: 本地相对路径}
    """
    txt = raw or ""

    # 1) 内嵌视频 / 图片 先抽出来，避免被后续标签处理打乱。
    #    ⚠️ iframe 的转换结果里含 `<url>` 尖括号写法，必须先退场，
    #    否则会被后面的「剥掉剩余标签」正则（<[^>]+>）误删 —— 最后再放回来。
    _iframes: list = []

    def _stash_iframe(m):
        _iframes.append(_iframe_to_md(m.group(0)))
        return f"\n\n@@IFRAME{len(_iframes) - 1}@@\n\n"

    txt = re.sub(r"<iframe\b[^>]*>.*?</iframe>|<iframe\b[^>]*/?>", _stash_iframe, txt, flags=re.I | re.S)
    txt = RE_IMG.sub(lambda m: "\n\n@@IMG::" + m.group(1) + "@@\n\n", txt)

    # 2) 块级标签
    txt = re.sub(r"<br\s*/?>", "\n", txt, flags=re.I)
    txt = re.sub(r"</p\s*>", "\n\n", txt, flags=re.I)
    txt = re.sub(r"<p\b[^>]*>", "", txt, flags=re.I)
    txt = re.sub(r"</?div\b[^>]*>", "\n", txt, flags=re.I)
    txt = re.sub(r"<h([1-6])\b[^>]*>(.*?)</h\1>", lambda m: "\n" + "#" * int(m.group(1)) + " " + m.group(2) + "\n", txt, flags=re.I | re.S)
    txt = re.sub(r"<li\b[^>]*>", "\n- ", txt, flags=re.I)
    txt = re.sub(r"</li\s*>", "", txt, flags=re.I)
    txt = re.sub(r"</?(ul|ol)\b[^>]*>", "\n", txt, flags=re.I)

    # 3) 行内标签
    txt = re.sub(r"<(/?)strong\b[^>]*>", r"**", txt, flags=re.I)
    txt = re.sub(r"<(/?)b\b[^>]*>", r"**", txt, flags=re.I)
    txt = re.sub(r"<(/?)em\b[^>]*>", r"*", txt, flags=re.I)
    txt = re.sub(r"<(/?)i\b[^>]*>", r"*", txt, flags=re.I)
    txt = re.sub(r"<code\b[^>]*>(.*?)</code>", lambda m: "`" + m.group(1) + "`", txt, flags=re.I | re.S)
    txt = re.sub(r'<a\b[^>]*?href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', lambda m: f"[{re.sub(r'<[^>]+>', '', m.group(2)).strip()}]({html_mod.unescape(m.group(1))})", txt, flags=re.I | re.S)
    txt = re.sub(r"<[^>]+>", "", txt)          # 剩余标签一律剥掉
    txt = html_mod.unescape(txt)

    # 4) 图片占位符 → Markdown 图片
    def _img(m):
        url = m.group(1)
        local = image_map.get(url)
        if local:
            return f"![{pathlib.Path(local).stem}]({local})"
        return f"[图片未下载：{url}]"

    txt = re.sub(r"@@IMG::(.+?)@@", _img, txt)

    # 4b) 放回内嵌视频（此时标签剥离已结束，尖括号安全）
    txt = re.sub(r"@@IFRAME(\d+)@@", lambda m: _iframes[int(m.group(1))], txt)

    # 5) 规整空行
    txt = re.sub(r"[ \t]+\n", "\n", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def table_to_md(tbl: dict) -> str:
    data = (tbl.get("value") or {}).get("data") or []
    if not data:
        return ""
    hdr = (tbl.get("value") or {}).get("firstRowIsTableHeader")
    lines = []
    rows = data
    if hdr:
        lines.append("| " + " | ".join(str(x) for x in rows[0]) + " |")
        lines.append("|" + "---|" * len(rows[0]))
        rows = rows[1:]
    else:
        lines.append("|" + "---|" * len(data[0]))
    for r in rows:
        lines.append("| " + " | ".join(str(x) for x in r) + " |")
    return "\n".join(lines)


# ---------------------------------------------------------------- 图片下载

def collect_image_urls(blocks: list) -> list:
    urls = []
    for b in blocks:
        if b.get("type") != "TEXT":
            continue
        for m in RE_IMG.finditer(b.get("value") or ""):
            u = html_mod.unescape(m.group(1)).strip()
            if u and u not in urls:
                urls.append(u)
    return urls


def download_images(s: requests.Session, urls: list, dest: pathlib.Path, page_id: str) -> dict:
    """下载图片，返回 {原始URL: 相对路径}。相对路径以 md 所在目录为基准。"""
    dest.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for i, u in enumerate(urls, 1):
        full = u if u.startswith("http") else IMG_HOST + u
        ext = pathlib.Path(full.split("?")[0]).suffix or ".png"
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            ext = ".png"
        name = f"{page_id}_{i:02d}{ext}"
        try:
            r = s.get(full, timeout=60)
            if r.status_code == 200 and r.content:
                (dest / name).write_bytes(r.content)
                mapping[u] = f"images/{page_id}/{name}"
                print(f"    [img] {name}  {len(r.content)} bytes")
            else:
                print(f"    [img] 失败 {r.status_code}  {full}")
        except Exception as e:
            print(f"    [img] 异常 {e}  {full}")
    return mapping


# ---------------------------------------------------------------- 组装 md

def build_md(page: dict, image_map: dict, source_url: str) -> str:
    out = []
    out.append(f'# {page["title"]}\n')
    out.append("> **归档信息**")
    out.append(f'> - 页面：<{source_url}>')
    out.append(f'> - 页面 id：`{page["id"]}` ｜ 课程：`{page.get("category")}` ｜ 预计时长：{page.get("duration") or "-"}')
    out.append(f'> - 平台最后更新：{page.get("lastModified")}')
    out.append("> - 来源：**平台官方 tutorial-pages 接口原文**（`GET /tutorial-pages/{id}`），文字/表格/图片均为原样转换，未改写")
    out.append("> - 抓取：`src/tools/fetch_learn_docs.py`｜抓取日期 2026-09-15")
    out.append("\n---\n")

    for b in page.get("content", []):
        t = b.get("type")
        if t == "HEADING":
            lvl = int((b.get("value") or {}).get("level") or 1) + 1   # 页标题占 H1
            out.append("\n" + "#" * min(lvl, 6) + " " + ((b.get("value") or {}).get("content") or "").strip() + "\n")
        elif t == "TEXT":
            md = html_to_md(b.get("value") or "", image_map)
            if md:
                out.append(md + "\n")
        elif t == "TABLE":
            md = table_to_md(b)
            if md:
                out.append("\n" + md + "\n")
        else:
            out.append(f"\n> ⚠️ 未处理的块类型：`{t}`\n")
    return "\n".join(out)


# ---------------------------------------------------------------- main

def cmd_tree(s: requests.Session, as_json: bool, out: pathlib.Path | None) -> int:
    data = fetch_tutorials(s)
    OUT = pathlib.Path("_autologs/learn_docs")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tutorials.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_tree(data)
    print(f"[已存] {OUT / 'tutorials.json'}")
    return 0


def cmd_page(s: requests.Session, page_id: str, out_path: str | None, no_images: bool) -> int:
    r = s.get(f"{BASE}/tutorial-pages/{page_id}", timeout=60)
    print(f"GET /tutorial-pages/{page_id} -> {r.status_code}  {len(r.content)} bytes")
    if r.status_code != 200:
        print(r.text[:400])
        return 1
    page = r.json()

    OUT = pathlib.Path("_autologs/learn_docs")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f"{page_id}.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[已存] {OUT / (page_id + '.json')}")

    target = pathlib.Path(out_path) if out_path else (OUT / f"{page_id}.md")
    target.parent.mkdir(parents=True, exist_ok=True)

    image_map = {}
    if not no_images:
        urls = collect_image_urls(page.get("content", []))
        print(f"发现 {len(urls)} 张图片：")
        image_map = download_images(s, urls, target.parent / "images" / page_id, page_id)
    else:
        print("（--no-images：跳过图片下载）")

    md = build_md(page, image_map, f"https://platform.worldquantbrain.com/learn/documentation/{page_id}")
    target.write_text(md, encoding="utf-8")
    print(f"[已写] {target}  ({len(md)} 字符)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取 BRAIN Learn 文档（文字/表格/图片/视频链接）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("tree", help="打印官方目录树")
    p1.add_argument("--json", action="store_true", help="直接输出 JSON")

    p2 = sub.add_parser("page", help="抓取单个文档页")
    p2.add_argument("page_id")
    p2.add_argument("--out", help="输出 md 路径")
    p2.add_argument("--no-images", action="store_true", help="跳过图片下载")

    args = ap.parse_args()
    s = login()

    if args.cmd == "tree":
        return cmd_tree(s, args.json, None)
    if args.cmd == "page":
        return cmd_page(s, args.page_id, args.out, args.no_images)
    return 2


if __name__ == "__main__":
    sys.exit(main())
