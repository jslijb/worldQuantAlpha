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
    python src/tools/fetch_learn_docs.py all                       # ★ 一次抓完全部文档页
    python src/tools/fetch_learn_docs.py all --root docs/study/learn/docs --no-images

产出
----
  - `_autologs/learn_docs/tutorials.json`      目录树原始 JSON
  - `_autologs/learn_docs/{page_id}.json`      单页原始 JSON（未加工，证据留档）
  - 目标 md 文件（--out 指定，或默认 `_autologs/learn_docs/{page_id}.md`）
  - 图片默认落到 md 同目录的 `images/{page_id}/`

`all` 子命令的落盘结构（按**官方课程结构**组织）
--------------------------------------------
    docs/study/learn/docs/
    ├── NN_<课程id>/             NN = 官方 sequence
    │   └── MM_<页面id>.md       MM = 该课程内页序
    ├── images/<页面id>/         该页配图（md 中按 ../../images/... 引用）
    └── README_官方文档结构.md    逐页清单索引

  - 幂等：图片已存在则跳过（断点续抓），可反复执行。
  - 文档页内嵌的视频会**自动反查课程库**，若有官方字幕则在页首挂一行提示。

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
    """按块顺序收集页面里的全部图片 URL（TEXT 块内嵌的 + IMAGE 块的）。"""
    urls = []
    for b in blocks:
        t = b.get("type")
        if t == "TEXT":
            for m in RE_IMG.finditer(b.get("value") or ""):
                u = html_mod.unescape(m.group(1)).strip()
                if u and u not in urls:
                    urls.append(u)
        elif t == "IMAGE":
            u = ((b.get("value") or {}).get("url") or "").strip()
            if u and u not in urls:
                urls.append(u)
    return urls


def download_images(s: requests.Session, urls: list, dest: pathlib.Path, page_id: str,
                    rel_prefix: str = "") -> dict:
    """下载图片，返回 {原始URL: 相对路径}。相对路径以 md 所在目录为基准。

    rel_prefix 为空时按 `images/{page_id}/` 组织（图片与 md 同级）；
    否则用调用方给的相对前缀（批量抓取时图片集中放 `docs/images/{page_id}/`）。
    """
    dest.mkdir(parents=True, exist_ok=True)
    mapping = {}
    for i, u in enumerate(urls, 1):
        full = u if u.startswith("http") else IMG_HOST + u
        raw_name = pathlib.Path(full.split("?")[0]).name
        ext = pathlib.Path(raw_name).suffix or ".png"
        if ext.lower() not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
            ext = ".png"
        # 优先用原始文件名（可读、可追溯），无名字则退回序号
        stem = pathlib.Path(raw_name).stem if raw_name and re.match(r"^[\w.\-]+$", raw_name) else ""
        name = f"{i:02d}_{stem}{ext}" if stem else f"{page_id}_{i:02d}{ext}"
        rel = f"{rel_prefix}/{name}" if rel_prefix else f"images/{page_id}/{name}"
        target = dest / name
        if target.exists() and target.stat().st_size > 0:      # 断点续抓：已有就跳过
            mapping[u] = rel
            print(f"    [img] 已存在 {name}")
            continue
        try:
            r = s.get(full, timeout=60)
            if r.status_code == 200 and r.content:
                target.write_bytes(r.content)
                mapping[u] = rel
                print(f"    [img] {name}  {len(r.content)} bytes")
            else:
                print(f"    [img] 失败 {r.status_code}  {full}")
        except Exception as e:
            print(f"    [img] 异常 {e}  {full}")
    return mapping


# ---------------------------------------------------------------- 组装 md

def simulation_example_to_md(val: dict) -> str:
    """SIMULATION_EXAMPLE 块 → 表达式 + 完整模拟设置表。"""
    st = val.get("settings") or {}
    code = (val.get("regular") or "").strip()
    if not code:
        code = json.dumps(val, ensure_ascii=False)

    CN = {
        "instrumentType": "标的类型", "region": "地区", "universe": "股票池",
        "delay": "Delay", "decay": "Decay", "neutralization": "中性化",
        "truncation": "Truncation", "pasteurization": "Pasteurization",
        "unitHandling": "Unit Handling", "nanHandling": "NaN Handling",
        "language": "语言", "maxTrade": "Max Trade",
    }
    out = ["**示例 Alpha 表达式**\n", "```", code, "```\n"]
    if st:
        out.append("| 设置项 | 值 |")
        out.append("|---|---|")
        for k in CN:
            if k in st:
                out.append(f"| {CN[k]}（`{k}`） | `{st[k]}` |")
        for k in st:
            if k not in CN:
                out.append(f"| `{k}` | `{st[k]}` |")
        out.append("")
    return "\n".join(out)


def equation_to_md(raw: str) -> str:
    """EQUATION 块 → LaTeX 原文（原样保留，不解释）。"""
    e = (raw or "").strip()
    if not e:
        return ""
    return "**公式**\n\n$$\n" + e + "\n$$\n"


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
        elif t == "IMAGE":
            v = b.get("value") or {}
            url = (v.get("url") or "").strip()
            title = (v.get("title") or pathlib.Path(url.split("?")[0]).name or "image").strip()
            local = image_map.get(url)
            if local:
                out.append(f"\n![{title}]({local})\n")
            else:
                out.append(f"\n> 🖼️ **图片未取到**（{title}）：<{url}>\n")
        elif t == "EQUATION":
            md = equation_to_md(b.get("value"))
            if md:
                out.append("\n" + md + "\n")
        elif t == "SIMULATION_EXAMPLE":
            out.append("\n" + simulation_example_to_md(b.get("value") or {}) + "\n")
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


# ---------------------------------------------------------------- 批量抓取

# 官方课程 → 本地目录序号的映射（按 tutorials.json 里的 sequence 排序生成）
def _video_index() -> dict:
    """{YouTube/Vidyard uid: (course_id, video_id, title, 字幕字符数)}，用于给文档内嵌视频挂字幕线索。"""
    p = pathlib.Path("_autologs/learn_video/video_courses.json")
    if not p.exists():
        return {}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}
    idx = {}
    for c in d.get("results", []):
        for v in c.get("videos", []):
            uid = str(v.get("uid") or "").strip()
            if uid:
                idx[uid] = (c["id"], v["id"], v.get("title"), len(v.get("transcript") or ""))
    return idx


def _embedded_video_hint(raw: str, vidx: dict) -> str:
    """若页面内嵌视频能在课程库里反查到字幕，返回一行提示；否则空串。"""
    m = RE_IFRAME_SRC.search(raw or "")
    if not m:
        return ""
    yt = re.search(r"(?:youtube\.com/embed/|youtu\.be/)([\w-]{6,})", html_mod.unescape(m.group(1)))
    if not yt:
        return ""
    hit = vidx.get(yt.group(1))
    if not hit:
        return ""
    cid, vid, title, n = hit
    return (f"> 📝 该视频在课程库中**有官方字幕**：`{cid}` → `{vid}`（{title}，{n} 字符）"
            f"，可直接翻译。见 `课程视频总表.md`")


def cmd_all(s: requests.Session, root: pathlib.Path, no_images: bool) -> int:
    data = fetch_tutorials(s)
    OUT = pathlib.Path("_autologs/learn_docs")
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tutorials.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    vidx = _video_index()
    root.mkdir(parents=True, exist_ok=True)
    img_root = root / "images"

    courses = sorted(data["results"], key=lambda x: x.get("sequence") or 0)
    index_rows = []
    n_ok = n_fail = n_img = 0
    n_video_hit = 0

    for ci, c in enumerate(courses, 1):
        cid = c["id"]
        cdir = root / f"{ci:02d}_{cid}"
        cdir.mkdir(parents=True, exist_ok=True)
        pages = sorted(c.get("pages", []), key=lambda x: x.get("sequence") or 0)
        print(f"\n■ {ci:02d} {cid}（{c.get('category')}，{len(pages)} 页）")
        for pi, p in enumerate(pages, 1):
            pid = p["id"]
            rel_img = f"../images/{pid}"          # md 在 <root>/<课程目录>/ 下，图片在 <root>/images/
            target = cdir / f"{pi:02d}_{pid}.md"

            r = s.get(f"{BASE}/tutorial-pages/{pid}", timeout=60)
            if r.status_code != 200:
                print(f"  [{pi:02d}] {pid}  失败 {r.status_code}")
                n_fail += 1
                index_rows.append((ci, cid, pi, pid, p.get("title"), p.get("duration"), "❌ 抓取失败", 0, 0, 0, 0, 0))
                continue
            page = r.json()
            (OUT / f"{pid}.json").write_text(json.dumps(page, ensure_ascii=False, indent=2), encoding="utf-8")

            image_map = {}
            if not no_images:
                urls = collect_image_urls(page.get("content", []))
                if urls:
                    image_map = download_images(s, urls, img_root / pid, pid, rel_prefix=rel_img)
                    n_img += len(image_map)

            md = build_md(page, image_map, f"https://platform.worldquantbrain.com/learn/documentation/{pid}")

            # 内嵌视频 → 尝试挂字幕线索
            hint = ""
            for b in page.get("content", []):
                if b.get("type") == "TEXT" and "<iframe" in (b.get("value") or ""):
                    hint = _embedded_video_hint(b["value"], vidx)
                    break
            if hint:
                n_video_hit += 1
                md = md.replace("\n---\n", "\n" + hint + "\n\n---\n", 1)

            target.write_text(md, encoding="utf-8")
            n_ok += 1
            n_img_page = len(image_map)
            n_expr = sum(1 for b in page.get("content", []) if b.get("type") == "SIMULATION_EXAMPLE")
            n_eq = sum(1 for b in page.get("content", []) if b.get("type") == "EQUATION")
            n_tbl = sum(1 for b in page.get("content", []) if b.get("type") == "TABLE")
            blocks = len(page.get("content", []))
            print(f"  [{pi:02d}] {pid:56s} {len(md):6d}字符 块{blocks:2d} 图{n_img_page} 例{n_expr} 式{n_eq} 表{n_tbl}")
            index_rows.append((ci, cid, pi, pid, p.get("title"), p.get("duration"),
                               f"✅ `{target.relative_to(root.parent).as_posix()}`", n_img_page, len(md),
                               n_expr, n_eq, n_tbl))

    # ---- 生成索引 ----
    L = []
    tot_expr = sum(r[9] for r in index_rows)
    tot_eq = sum(r[10] for r in index_rows)
    tot_tbl = sum(r[11] for r in index_rows)
    L.append("# 平台 Learn 文档全文归档（官方 documentation 全部页面）\n")
    L.append(f"> 来源：`GET /tutorials`（目录树）+ `GET /tutorial-pages/{{id}}`（正文），需登录")
    L.append(f"> 抓取日期：2026-09-15 ｜ 脚本：`src/tools/fetch_learn_docs.py all`")
    L.append(f"> 合计 **{data['count']} 个课程 / {n_ok + n_fail} 页**，成功 **{n_ok}** 页、失败 {n_fail} 页")
    L.append(f"> 素材：图片 **{n_img}** 张 ｜ 示例表达式（含完整模拟设置）**{tot_expr}** 个 ｜ 公式 **{tot_eq}** 条 ｜ 表格 **{tot_tbl}** 个")
    L.append(f"> 其中 {n_video_hit} 页内嵌的视频**在课程库里有官方字幕**，可直接翻译")
    L.append("> 原文照录：文字 / 表格 / 图片 / 公式均按接口内容原样转换，未改写、未删节\n")
    L.append("---\n")
    L.append("## 目录结构\n")
    L.append("```")
    L.append("docs/study/learn/docs/")
    L.append("├── NN_<课程id>/              官方课程目录（NN = 官方 sequence）")
    L.append("│   └── MM_<页面id>.md        MM = 该课程内页序")
    L.append("├── images/<页面id>/          该页配图（md 中按 ../images/... 引用）")
    L.append("└── README_官方文档结构.md     本文件（逐页清单）")
    L.append("```\n")
    L.append("> 原始 JSON 证据留档在 `_autologs/learn_docs/{页面id}.json`（未加工的接口返回）。\n")
    L.append("---\n")
    L.append("## 逐页清单\n")
    cur = None
    for ci, cid, pi, pid, title, dur, status, nimg, nch, ne, nq, nt in index_rows:
        if cid != cur:
            cur = cid
            cc = next((x for x in courses if x["id"] == cid), {})
            L.append(f"\n### {ci:02d} `{cid}` ｜ {cc.get('category')} ｜ {len(cc.get('pages', []))} 页\n")
            L.append("| # | 官方页面 id | 标题 | 时长 | 图 | 例 | 式 | 表 | 正文字符 | 归档 |")
            L.append("|---|---|---|---|---|---|---|---|---|---|")
        L.append(f"| {pi:02d} | `{pid}` | {title} | {dur or '-'} | {nimg} | {ne} | {nq} | {nt} | {nch} | {status} |")
    L.append("")
    (root / "README_官方文档结构.md").write_text("\n".join(L), encoding="utf-8")
    print(f"\n[索引] {root / 'README_官方文档结构.md'}")
    print(f"完成：成功 {n_ok} 页，失败 {n_fail} 页，图片 {n_img} 张，示例表达式 {tot_expr} 个，公式 {tot_eq} 条，表格 {tot_tbl} 个，内嵌视频命中字幕 {n_video_hit} 页")
    return 0 if n_fail == 0 else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="抓取 BRAIN Learn 文档（文字/表格/图片/视频链接）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("tree", help="打印官方目录树")
    p1.add_argument("--json", action="store_true", help="直接输出 JSON")

    p2 = sub.add_parser("page", help="抓取单个文档页")
    p2.add_argument("page_id")
    p2.add_argument("--out", help="输出 md 路径")
    p2.add_argument("--no-images", action="store_true", help="跳过图片下载")

    p3 = sub.add_parser("all", help="抓取全部文档页（按官方课程结构落盘）")
    p3.add_argument("--root", default="docs/study/learn/docs", help="归档根目录")
    p3.add_argument("--no-images", action="store_true", help="跳过图片下载")

    args = ap.parse_args()
    s = login()

    if args.cmd == "tree":
        return cmd_tree(s, args.json, None)
    if args.cmd == "page":
        return cmd_page(s, args.page_id, args.out, args.no_images)
    if args.cmd == "all":
        return cmd_all(s, pathlib.Path(args.root), args.no_images)
    return 2


if __name__ == "__main__":
    sys.exit(main())
