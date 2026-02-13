"""Tests for URL encoding behavior in downloader utility."""

from pathlib import Path
import sys
from urllib.parse import quote


sys.path.insert(0, str(Path(__file__).resolve().parent))
import utility  # noqa: E402


class _FakeResponse:
    def __init__(self, payload: bytes) -> None:
        self._payload = payload
        self._offset = 0

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

    def _fake_urlopen(url):
        captured["url"] = url
        return _FakeResponse(b"ok")

    monkeypatch.setattr(utility.urllib.request, "urlopen", _fake_urlopen)

    utility.download_file(base_path, file_name, folder=str(tmp_path))

    expected_url = utility.BASE_URL + quote(base_path, safe="/") + quote(file_name, safe=".-_")
    assert captured["url"] == expected_url
    assert (tmp_path / base_path / file_name).exists()
