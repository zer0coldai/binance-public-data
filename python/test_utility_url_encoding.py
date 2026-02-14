"""Tests for URL encoding behavior in downloader utility."""

import json
from pathlib import Path
import urllib.error
import sys
from urllib.parse import quote
from urllib.error import HTTPError


sys.path.insert(0, str(Path(__file__).resolve().parent))
import utility  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def getheader(self, name: str):
        if name.lower() == "content-length":
            return str(len(self._payload))
        return None

    def read(self, size: int) -> bytes:
        if self._offset >= len(self._payload):
            return b""
        chunk = self._payload[self._offset : self._offset + size]
        self._offset += len(chunk)
        return chunk


def test_download_file_encodes_url_but_preserves_local_filename(tmp_path, monkeypatch) -> None:
    base_path = "data/futures/um/monthly/klines/币安人生USDT/1m/"
    file_name = "币安人生USDT-1m-2026-01.zip"
    captured = {}

    def _fake_urlopen(url, timeout=None):
        captured["url"] = url
        captured["timeout"] = timeout
        return _FakeResponse(b"ok")

    monkeypatch.setattr(utility.urllib.request, "urlopen", _fake_urlopen)

    utility.download_file(base_path, file_name, folder=str(tmp_path))

    expected_url = utility.BASE_URL + quote(base_path, safe="/") + quote(file_name, safe=".-_")
    assert captured["url"] == expected_url
    assert captured["timeout"] is not None
    assert (tmp_path / base_path / file_name).exists()


def test_download_file_retries_then_succeeds(tmp_path, monkeypatch) -> None:
    calls = {"count": 0}

    def _flaky_urlopen(url, timeout=None):
        calls["count"] += 1
        if calls["count"] < 3:
            raise urllib.error.URLError("temporary failure")
        return _FakeResponse(b"ok")

    monkeypatch.setattr(utility.urllib.request, "urlopen", _flaky_urlopen)
    monkeypatch.setattr(utility.time_module, "sleep", lambda _: None)

    utility.download_file("data/spot/monthly/klines/BTCUSDT/1m/", "BTCUSDT-1m-2026-01.zip", folder=str(tmp_path))

    assert calls["count"] == 3


def test_get_all_symbols_retries_then_succeeds(monkeypatch) -> None:
    payload = json.dumps({"symbols": [{"symbol": "BTCUSDT"}, {"symbol": "ETHUSDT"}]}).encode("utf-8")
    calls = {"count": 0}

    class _ExchangeInfoResponse:
        def __init__(self, body: bytes) -> None:
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return self._body

    def _flaky_urlopen(url, timeout=None):
        calls["count"] += 1
        if calls["count"] < 2:
            raise urllib.error.URLError("temporary failure")
        return _ExchangeInfoResponse(payload)

    monkeypatch.setattr(utility.urllib.request, "urlopen", _flaky_urlopen)
    monkeypatch.setattr(utility.time_module, "sleep", lambda _: None)

    symbols = utility.get_all_symbols("spot")

    assert symbols == ["BTCUSDT", "ETHUSDT"]
    assert calls["count"] == 2


def test_download_file_does_not_retry_http_error(tmp_path, monkeypatch) -> None:
    calls = {"count": 0}

    def _http_404(url, timeout=None):
        calls["count"] += 1
        raise HTTPError(url=url, code=404, msg="Not Found", hdrs=None, fp=None)

    sleep_calls = {"count": 0}

    monkeypatch.setattr(utility.urllib.request, "urlopen", _http_404)
    monkeypatch.setattr(utility.time_module, "sleep", lambda _: sleep_calls.__setitem__("count", sleep_calls["count"] + 1))

    utility.download_file("data/spot/monthly/klines/BTCUSDT/1m/", "BTCUSDT-1m-3026-01.zip", folder=str(tmp_path))

    assert calls["count"] == 1
    assert sleep_calls["count"] == 0
