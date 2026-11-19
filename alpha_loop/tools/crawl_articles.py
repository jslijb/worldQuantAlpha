from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path("docs/forum/alpha_inspiration")
ARTICLES = OUT / "articles"
IMG_DIR = OUT / "images"
PROFILE = Path("alpha_loop/state/pw_profile2")
ARTICLES.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)
FORCE = os.environ.get("AQ_FORCE") == "1"


def slug(idx: int, title: str) -> str:
    clean = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", title)[:40].strip("_")
    return f"{idx:03d}_{clean or 'post'}"


def wait_content(page) -> bool:
    deadline = time.time() + 30
    while time.time() < deadline:
        time.sleep(1)
        try:
            txt = page.inner_text("body")
        except Exception:
            continue
        low = txt.lower()
        if "security verification" in low or "checking your browser" in low:
            continue
        if len(txt) > 400:
            return True
    return False


def main() -> int:
    links = json.loads((OUT / "_links.json").read_text(encoding="utf-8"))
    links = [L for L in links if "/community/posts/new" not in L["url"]]
    done = set() if FORCE else {p.name.split("__")[0] for p in ARTICLES.glob("*.md")}
    index = []
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=False, viewport={"width": 1400, "height": 900},
            args=["--disable-blink-features=AutomationControlled"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        for i, L in enumerate(links, 1):
            name = slug(i, L.get("title") or "")
            if name in done:
                continue
            ok = False
            for attempt in range(3):
                try:
                    page.goto(L["url"], wait_until="domcontentloaded", timeout=90000)
                except Exception:
                    time.sleep(3)
                    continue
                if wait_content(page):
                    ok = True
                    break
                print(f"[{i}] CHALLENGE_RETRY {attempt + 1}", flush=True)
                time.sleep(6)
            if not ok:
                print(f"[{i}] SKIP_CF", flush=True)
                continue
            post = page.query_selector(".post") or page.query_selector("main") or page.query_selector("body")
            body = post.inner_text() if post else page.inner_text("body")
            title_el = page.query_selector("h1")
            title = (title_el.inner_text().strip() if title_el else "") or L.get("title") or ""
            codes = []
            for el in page.query_selector_all(".post pre, .post code"):
                t = (el.inner_text() or "").strip()
                if len(t) > 12:
                    codes.append(t)
            imgs = page.query_selector_all(".post img")
            local_imgs = []
            for k, img in enumerate(imgs, 1):
                src = img.get_attribute("src") or ""
                if not src or src.startswith("data:"):
                    continue
                try:
                    resp = page.request.get(src)
                    if resp.status != 200:
                        continue
                    ext = ".png"
                    low = src.lower()
                    for cand in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                        if cand in low:
                            ext = cand
                            break
                    fn = IMG_DIR / f"{name}_{k:02d}{ext}"
                    fn.write_bytes(resp.body())
                    local_imgs.append(fn.name)
                except Exception:
                    pass
            md = (f"# {title}\n\n- URL: {L['url']}\n"
                  f"- 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                  f"- 图片: {len(local_imgs)}\n\n## 正文\n\n{body}\n")
            if codes:
                md += "\n## 代码/表达式（文本）\n\n"
                for c in codes:
                    md += f"```\n{c}\n```\n\n"
            if local_imgs:
                md += "\n## 代码/正文截图\n\n" + "\n".join(f"- images/{n}" for n in local_imgs) + "\n"
            (ARTICLES / f"{name}.md").write_text(md, encoding="utf-8")
            index.append({"idx": i, "file": name, "title": title, "url": L["url"],
                          "chars": len(body), "codes": len(codes), "imgs": len(local_imgs)})
            print(f"[{i}/{len(links)}] {name} chars={len(body)} codes={len(codes)} imgs={len(local_imgs)}",
                  flush=True)
        ctx.close()
    (OUT / "_index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE", len(index), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())