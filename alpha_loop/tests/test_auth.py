from __future__ import annotations

from alpha_loop.auth import Brain, load_credentials


class FakeResp:
    def __init__(self, status_code, body):
        self.status_code = status_code
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


def test_load_credentials_json_list():
    user, pwd = load_credentials()
    assert "@" in user and len(pwd) > 0


def test_poll_waits_until_alpha(monkeypatch):
    b = Brain(reuse_cookie=False)
    seq = iter([{"progress": 0.1}, {"progress": 0.6}, {"alpha": "A1"}])
    calls = {"n": 0}

    def fake_get(path, **kw):
        calls["n"] += 1
        return FakeResp(200, next(seq))

    monkeypatch.setattr(b, "get", fake_get)
    out = b.poll("http://x/sim/1", timeout=5, interval=0)
    assert out == {"alpha": "A1"}
    assert calls["n"] == 3


def test_poll_returns_terminal_error(monkeypatch):
    b = Brain(reuse_cookie=False)
    monkeypatch.setattr(b, "get", lambda p, **k: FakeResp(200, {"status": "ERROR", "message": "x"}))
    out = b.poll("http://x/sim/2", timeout=5, interval=0)
    assert out["status"] == "ERROR"


def test_poll_timeout(monkeypatch):
    b = Brain(reuse_cookie=False)
    monkeypatch.setattr(b, "get", lambda p, **k: FakeResp(200, {"progress": 0.0}))
    out = b.poll("http://x/sim/3", timeout=0.2, interval=0.05)
    assert out.get("_timeout") is True