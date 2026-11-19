from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import requests

from . import config

log = logging.getLogger("aq.auth")

RETRY_429 = 5
RETRY_5XX = 3


class AuthError(RuntimeError):
    pass


def load_credentials(path: Path | None = None) -> tuple[str, str]:
    p = Path(path or config.CRED_PATH)
    raw = p.read_text(encoding="utf-8").strip()
    if raw.startswith("["):
        data = json.loads(raw)
        if not isinstance(data, list) or len(data) < 2:
            raise AuthError("credentials JSON must be [user, password]")
        return str(data[0]), str(data[1])
    for sep in (":", "\t", ",", "|"):
        if sep in raw:
            user, pwd = raw.split(sep, 1)
            return user.strip().strip('"'), pwd.strip().strip('"')
    raise AuthError("unrecognized credential format")


COOKIE_PATH = config.STATE_DIR / "session.json"
PROBE_PATH = "/users/self/alphas?limit=1&offset=0"


class Brain:
    def __init__(self, cred_path: Path | None = None, timeout: int = 60, reuse_cookie: bool = True):
        self.user, self.password = load_credentials(cred_path)
        self.timeout = timeout
        self.s = requests.Session()
        self.s.auth = (self.user, self.password)
        self.s.headers.update({"Accept": "application/json"})
        self.authenticated = False
        self.captcha_blocked = False
        if reuse_cookie:
            self._load_cookie()

    def _load_cookie(self) -> None:
        try:
            if COOKIE_PATH.exists():
                data = json.loads(COOKIE_PATH.read_text(encoding="utf-8"))
                jar = requests.utils.cookiejar_from_dict(data.get("cookies", {}))
                self.s.cookies.update(jar)
        except Exception as exc:
            log.warning("cookie load skipped: %s", exc)

    def _save_cookie(self) -> None:
        try:
            data = {"cookies": requests.utils.dict_from_cookiejar(self.s.cookies)}
            tmp = COOKIE_PATH.with_suffix(".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            tmp.replace(COOKIE_PATH)
        except Exception as exc:
            log.warning("cookie save failed: %s", exc)

    def _sleep_for_429(self, attempt: int) -> None:
        time.sleep(min(20 + attempt * 3, 30))

    def _request(self, method: str, path: str, **kw) -> requests.Response:
        url = path if path.startswith("http") else config.API_BASE + path
        kw.setdefault("timeout", self.timeout)
        last = None
        n429 = 0
        n5xx = 0
        while True:
            try:
                r = self.s.request(method, url, **kw)
            except requests.RequestException as exc:
                last = exc
                n5xx += 1
                if n5xx > RETRY_5XX:
                    raise AuthError(f"network failure: {exc}") from exc
                time.sleep(2 ** n5xx)
                continue
            if r.status_code == 429:
                n429 += 1
                if n429 > RETRY_429:
                    return r
                self._sleep_for_429(n429)
                continue
            if 500 <= r.status_code < 600:
                n5xx += 1
                if n5xx > RETRY_5XX:
                    return r
                time.sleep(2 ** n5xx)
                continue
            return r

    def get(self, path: str, **kw) -> requests.Response:
        return self._request("GET", path, **kw)

    def post(self, path: str, **kw) -> requests.Response:
        return self._request("POST", path, **kw)

    def patch(self, path: str, **kw) -> requests.Response:
        return self._request("PATCH", path, **kw)

    def login(self) -> bool:
        probe = self.get(PROBE_PATH)
        if probe.status_code == 200:
            self.authenticated = True
            return True
        r = self.post("/authentication")
        if r.status_code == 201:
            self.authenticated = True
            self._save_cookie()
            return True
        body = (r.text or "")[:300]
        if "captcha" in body.lower():
            self.captcha_blocked = True
            raise AuthError("CAPTCHA required by platform; reuse cookie or wait before retry")
        log.error("login failed status=%s body=%s", r.status_code, body)
        self.authenticated = False
        return False

    def relogin(self) -> bool:
        self.s.auth = (self.user, self.password)
        return self.login()

    def get_json(self, path: str, **kw):
        r = self.get(path, **kw)
        if r.status_code != 200:
            return None
        try:
            return r.json()
        except ValueError:
            return None

    def poll(self, location: str, timeout: int | None = None, interval: int | None = None) -> dict:
        timeout = config.SIM_TIMEOUT if timeout is None else timeout
        interval = config.SIM_POLL_INTERVAL if interval is None else interval
        deadline = time.time() + timeout
        terminal_err = {"ERROR", "FAIL", "FAILED", "CANCELLED"}
        while time.time() < deadline:
            r = self.get(location)
            if r.status_code == 200:
                try:
                    body = r.json()
                except ValueError:
                    body = {}
                if isinstance(body, dict) and body:
                    if body.get("alpha"):
                        return body
                    status = str(body.get("status", "")).upper()
                    if status in terminal_err or status in {"COMPLETE", "COMPLETED"}:
                        return body
                    if "progress" in body or status == "RUNNING":
                        time.sleep(interval)
                        continue
                    return body
            elif r.status_code in (400, 401, 403, 404):
                return {"_http_status": r.status_code, "_body": r.text[:2000]}
            time.sleep(interval)
        return {"_timeout": True}


def main() -> int:
    b = Brain()
    ok = b.login()
    print("LOGIN_OK" if ok else "LOGIN_FAIL")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())