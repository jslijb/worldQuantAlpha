from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright

BASE = "https://support.worldquantbrain.com"
URL = (BASE + "/hc/en-us/community/posts/19273239621399--Alpha%E7%81%B5%E6%84%9F%E5%90%AF%E7%A4%BA%E5%BD%95-"
       "%E5%90%88%E9%9B%86-%E6%8C%81%E7%BB%AD%E6%9B%B4%E6%96%B0%E6%94%B6%E5%BD%95%E4%B8%AD")
OUT = Path("docs/forum/alpha_inspiration")
PROFILE = Path("alpha_loop/state/pw_profile2")
OUT.mkdir(parents=True, exist_ok=True)


def looks_logged_in(page) -> bool:
    url = (page.url or "").lower()
    if "sign-in" in url or "/login" in url or "signin" in url:
        return False
    try:
        text = page.inner_text("body")
    except Exception:
        return False
    if "community/posts/" in url and len(text) > 1500:
        return True
    low = text.lower()
    return "sign out" in low or "log out" in low or "my profile" in low


def main() -> int:
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            str(PROFILE), headless=False, viewport={"width": 1440, "height": 900},
            args=["--disable-blink-features=AutomationControlled", "--start-maximized"])
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        page.bring_to_front()
        time.sleep(3)
        print("OPENED", page.url, flush=True)
        deadline = time.time() + 1800
        n = 0
        while time.time() < deadline:
            logged = looks_logged_in(page)
            try:
                page.screenshot(path=str(OUT / "_shot.png"))
            except Exception:
                pass
            print(f"TICK {n} logged={logged} url={page.url[:110]}", flush=True)
            n += 1
            if logged:
                break
            time.sleep(10)
        else:
            print("LOGIN_TIMEOUT", flush=True)
            ctx.close()
            return 2
        time.sleep(2)
        page.goto(URL, wait_until="domcontentloaded", timeout=90000)
        time.sleep(3)
        (OUT / "_page.html").write_text(page.content(), encoding="utf-8")
        (OUT / "_page.txt").write_text(page.inner_text("body"), encoding="utf-8")
        print("TITLE", page.title(), flush=True)
        links = []
        for a in page.query_selector_all("a[href*='/community/posts/']"):
            href = a.get_attribute("href") or ""
            full = urljoin(BASE, href).split("?")[0]
            if "/community/posts/" not in full:
                continue
            if full == URL.split("?")[0]:
                continue
            links.append({"url": full, "title": (a.inner_text() or "").strip()})
        uniq = {L["url"]: L for L in links}
        links = list(uniq.values())
        (OUT / "_links.json").write_text(json.dumps(links, ensure_ascii=False, indent=2), encoding="utf-8")
        print("LINKS", len(links), flush=True)
        ctx.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())