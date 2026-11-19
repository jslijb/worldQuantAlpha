from __future__ import annotations

import json
import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

OUT = Path("docs/forum/alpha_inspiration")
ARTICLES = OUT / "articles"
IMGS = OUT / "images"
COOKIES = Path("alpha_loop/state/pw_cookies.json")
BASE = "https://support.worldquantbrain.com"
ARTICLES.mkdir(parents=True, exist_ok=True)
IMGS.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


def session() -> requests.Session:
    s = requests.Session()
    for c in json.loads(COOKIES.read_text(encoding="utf-8")):
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
    s.headers["User-Agent"] = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                               "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
    return s


def slug(idx: int, title: str) -> str:
    clean = re.sub(r"[^0-9A-Za-z\u4e00-\u9fff]+", "_", title)[:40].strip("_")
    return f"{idx:03d}_{clean or 'post'}"


def html_to_text(html: str) -> tuple[str, list[str], list[str]]:
    soup = BeautifulSoup(html or "", "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    imgs = []
    for im in soup.find_all("img"):
        src = im.get("src") or ""
        if src:
            imgs.append(urljoin(BASE, src))
    codes = []
    for pre in soup.find_all(["pre", "code"]):
        t = pre.get_text("\n").strip()
        if len(t) > 12:
            codes.append(t)
    for pre in soup.find_all("pre"):
        pre.decompose()
    text = soup.get_text("\n")
    lines = [ln.strip() for ln in text.splitlines()]
    text = "\n".join(ln for ln in lines if ln)
    return text, codes, imgs


def fetch(item, sess) -> dict | None:
    idx, L = item
    pid = L["url"].rstrip("/").split("/")[-1].split("-")[0]
    r = sess.get(f"{BASE}/api/v2/help_center/community/posts/{pid}.json", timeout=30)
    if r.status_code != 200:
        return {"idx": idx, "url": L["url"], "status": r.status_code}
    post = r.json().get("post") or {}
    title = post.get("title") or L.get("title") or ""
    text, codes, imgs = html_to_text(post.get("details") or "")
    comments = []
    try:
        rc = sess.get(f"{BASE}/api/v2/help_center/community/posts/{pid}/comments.json", timeout=30)
        if rc.status_code == 200:
            for c in rc.json().get("comments") or []:
                ct, cc, ci = html_to_text(c.get("details") or "")
                comments.append({"body": ct, "codes": cc, "imgs": ci})
                codes.extend(cc)
                imgs.extend(ci)
    except Exception:
        pass
    name = slug(idx, title)
    local = []
    for k, src in enumerate(dict.fromkeys(imgs), 1):
        try:
            rr = sess.get(src, timeout=40)
            if rr.status_code != 200 or not rr.content:
                continue
            ext = ".png"
            for cand in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
                if cand in src.lower():
                    ext = cand
                    break
            fn = IMGS / f"{name}_{k:02d}{ext}"
            fn.write_bytes(rr.content)
            local.append(fn.name)
        except Exception:
            pass
    md = (f"# {title}\n\n- URL: {L['url']}\n"
          f"- 发布时间: {post.get('created_at')}\n- 楼层: {post.get('comment_count')} 条评论\n"
          f"- 抓取时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n## 正文\n\n{text}\n")
    if codes:
        md += "\n## 代码/表达式\n\n"
        for c in dict.fromkeys(codes):
            md += f"```\n{c}\n```\n\n"
    for i, c in enumerate(comments, 1):
        md += f"\n## 评论 {i}\n\n{c['body']}\n"
        for cc in c["codes"]:
            md += f"\n```\n{cc}\n```\n"
    if local:
        md += "\n## 图片\n\n" + "\n".join(f"- images/{n}" for n in local) + "\n"
    (ARTICLES / f"{name}.md").write_text(md, encoding="utf-8")
    return {"idx": idx, "file": name, "title": title, "url": L["url"],
            "chars": len(text), "codes": len(codes), "imgs": len(local),
            "comments": len(comments)}


def main() -> int:
    links = json.loads((OUT / "_links.json").read_text(encoding="utf-8"))
    links = [L for L in links if "/community/posts/new" not in L["url"]]
    items = list(enumerate(links, 1))
    sess = session()
    results, errors = [], []
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(fetch, it, sess): it for it in items}
        for n, f in enumerate(futures, 1):
            try:
                r = f.result()
            except Exception as exc:
                with _lock:
                    errors.append(str(exc)[:100])
                continue
            if r and r.get("file"):
                results.append(r)
            else:
                with _lock:
                    errors.append(str(r))
            if n % 20 == 0:
                print(f"progress {n}/{len(items)} ok={len(results)} err={len(errors)}", flush=True)
    results.sort(key=lambda x: x["idx"])
    (OUT / "_index.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("DONE ok=", len(results), "err=", len(errors), "secs=", round(time.time() - t0, 1), flush=True)
    print("ERRORS", errors[:5], flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())