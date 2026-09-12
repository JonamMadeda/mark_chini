"""Tests for app.Updater — version parsing, release checks, downloads."""

import io
import json
import sys
import urllib.error

import pytest

from app import Updater
from app.Updater import (
    UpdateCheckWorker,
    UpdateDownloadWorker,
    fetch_latest_release,
    is_newer,
    parse_version,
)

_MAINWINDOW_MODULE = sys.modules.get("app.MainWindow")


def _patch_messagebox(monkeypatch, fake):
    """Patch QMessageBox in the app.MainWindow *module* (not the class)."""
    module = sys.modules.get("app.MainWindow") or _MAINWINDOW_MODULE
    assert module is not None, "app.MainWindow module not loaded yet"
    monkeypatch.setattr(module, "QMessageBox", fake)


def _release_payload(tag="v9.9.0", with_setup_asset=True):
    assets = [{"name": "mark_chini.exe", "browser_download_url": "https://x/y.exe"}]
    if with_setup_asset:
        assets.append(
            {
                "name": "mark_chini_setup.exe",
                "browser_download_url": "https://example.com/mark_chini_setup.exe",
            }
        )
    return {
        "tag_name": tag,
        "html_url": "https://github.com/JonamMadeda/mark_chini/releases/tag/v9.9.0",
        "assets": assets,
    }


class _FakeResponse:
    def __init__(self, payload_bytes, content_length=None):
        self._stream = io.BytesIO(payload_bytes)
        self._content_length = content_length

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, size=-1):
        return self._stream.read(size)

    def getheader(self, name, default=None):
        if name.lower() == "content-length":
            return self._content_length
        return default


class TestParseVersion:
    @pytest.mark.parametrize(
        "tag, expected",
        [
            ("v1.3", (1, 3)),
            ("1.3.0", (1, 3, 0)),
            ("V2.0.1", (2, 0, 1)),
            ("v1.10.0", (1, 10, 0)),
            ("  v1.3.0  ", (1, 3, 0)),
            ("not-a-version", (0,)),
            ("", (0,)),
        ],
    )
    def test_parse(self, tag, expected):
        assert parse_version(tag) == expected


class TestIsNewer:
    @pytest.mark.parametrize(
        "latest, current, expected",
        [
            ("v1.4.0", "1.3.0", True),
            ("v1.3.1", "1.3.0", True),
            ("v2.0", "1.9.9", True),
            ("v1.3.0", "1.3.0", False),
            ("v1.3", "1.3.0", False),  # equal after zero-padding
            ("v1.2", "1.3.0", False),
            ("v1.3.0", "1.4.0", False),
            ("garbage", "1.3.0", False),
        ],
    )
    def test_compare(self, latest, current, expected):
        assert is_newer(latest, current) is expected


class TestFetchLatestRelease:
    def test_update_available_picks_setup_asset(self, monkeypatch):
        payload = json.dumps(_release_payload("v9.9.0")).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=15: _FakeResponse(payload)
        )
        res = fetch_latest_release()
        assert res["update"] is True
        assert res["tag"] == "v9.9.0"
        assert res["asset_url"] == "https://example.com/mark_chini_setup.exe"
        assert res["error"] is None

    def test_no_update_when_current(self, monkeypatch):
        payload = json.dumps(_release_payload("v1.3.0")).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=15: _FakeResponse(payload)
        )
        res = fetch_latest_release()
        assert res["update"] is False
        assert res["error"] is None

    def test_missing_setup_asset_gives_none(self, monkeypatch):
        payload = json.dumps(
            _release_payload("v9.9.0", with_setup_asset=False)
        ).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=15: _FakeResponse(payload)
        )
        res = fetch_latest_release()
        assert res["update"] is True
        assert res["asset_url"] is None


class TestUpdateCheckWorker:
    def test_emits_result(self, monkeypatch):
        payload = json.dumps(_release_payload("v9.9.0")).encode()
        monkeypatch.setattr(
            "urllib.request.urlopen", lambda req, timeout=15: _FakeResponse(payload)
        )
        received = []
        worker = UpdateCheckWorker()
        worker.result.connect(received.append)
        worker.run()  # synchronous: no thread needed for the test
        assert len(received) == 1
        assert received[0]["update"] is True
        assert received[0]["tag"] == "v9.9.0"

    def test_network_error_reports_cleanly(self, monkeypatch):
        def _raise(req, timeout=15):
            raise urllib.error.URLError("offline")

        monkeypatch.setattr("urllib.request.urlopen", _raise)
        received = []
        worker = UpdateCheckWorker()
        worker.result.connect(received.append)
        worker.run()
        assert len(received) == 1
        assert received[0]["update"] is False
        assert "offline" in received[0]["error"]


class TestUpdateDownloadWorker:
    def test_downloads_file_with_progress(self, monkeypatch, tmp_path):
        data = b"x" * (3 * 1024 * 1024 + 123)
        monkeypatch.setattr(
            "urllib.request.urlopen",
            lambda req, timeout=30: _FakeResponse(data, content_length=str(len(data))),
        )
        dest = str(tmp_path / "mark_chini_setup.exe")
        progress, finished = [], []
        worker = UpdateDownloadWorker("https://example.com/setup.exe", dest)
        worker.progress.connect(lambda d, t: progress.append((d, t)))
        worker.finished.connect(lambda ok, msg: finished.append((ok, msg)))
        worker.run()
        assert finished == [(True, dest)]
        assert progress, "expected progress signals"
        assert progress[-1] == (len(data), len(data))
        with open(dest, "rb") as f:
            assert f.read() == data

    def test_failed_download_reports_error(self, monkeypatch, tmp_path):
        def _raise(req, timeout=30):
            raise urllib.error.URLError("connection reset")

        monkeypatch.setattr("urllib.request.urlopen", _raise)
        dest = str(tmp_path / "mark_chini_setup.exe")
        finished = []
        worker = UpdateDownloadWorker("https://example.com/setup.exe", dest)
        worker.finished.connect(lambda ok, msg: finished.append((ok, msg)))
        worker.run()
        assert len(finished) == 1 and finished[0][0] is False
        assert "connection reset" in finished[0][1]
        assert not tmp_path.joinpath("mark_chini_setup.exe").exists()


class _FakeMessageBox:
    """Stand-in for QMessageBox covering both static calls and instances."""

    instances = []
    calls = []

    class ButtonRole:
        AcceptRole = 0
        RejectRole = 1
        ActionRole = 2

    def __init__(self, parent=None):
        self.text = ""
        self._later = object()
        type(self).instances.append(self)

    def setWindowTitle(self, title):
        pass

    def setText(self, text):
        self.text = text

    def setInformativeText(self, text):
        pass

    def addButton(self, label, role):
        button = object()
        if role == self.ButtonRole.RejectRole:
            self._later = button
        return button

    def exec(self):
        return 0

    def clickedButton(self):
        return self._later  # simulate clicking "Later"

    @classmethod
    def information(cls, *args, **kwargs):
        cls.calls.append(("info", args, kwargs))

    @classmethod
    def warning(cls, *args, **kwargs):
        cls.calls.append(("warn", args, kwargs))

    @classmethod
    def reset(cls):
        cls.instances = []
        cls.calls = []


class TestUpdateUI:
    @pytest.fixture
    def update_window(self, qapp, qtbot):
        from app.MainWindow import MainWindow

        _FakeMessageBox.reset()
        win = MainWindow()
        win.show()
        qtbot.addWidget(win)
        yield win
        win.close()

    def test_update_button_exists(self, update_window):
        assert update_window._updateBtn.text() == "\u21BB"
        assert update_window._updateBtn.toolTip() == "Check for updates"

    def test_manual_check_up_to_date(self, update_window, qtbot, monkeypatch):
        monkeypatch.setattr(
            Updater,
            "fetch_latest_release",
            lambda timeout=15: {
                "update": False,
                "tag": Updater.APP_VERSION,
                "page_url": "https://example.com/r",
                "asset_url": None,
                "error": None,
            },
        )
        _patch_messagebox(monkeypatch, _FakeMessageBox)
        update_window._checkForUpdates(silent=False)
        assert update_window._fileStatusLabel.text() == "Checking for updates..."
        qtbot.waitUntil(
            lambda: any(c[0] == "info" for c in _FakeMessageBox.calls), timeout=10000
        )
        assert update_window._fileStatusLabel.text() == "No file open"

    def test_update_available_prompts_user(self, update_window, qtbot, monkeypatch):
        monkeypatch.setattr(
            Updater,
            "fetch_latest_release",
            lambda timeout=15: {
                "update": True,
                "tag": "v9.9.0",
                "page_url": "https://example.com/r",
                "asset_url": "https://example.com/setup.exe",
                "error": None,
            },
        )
        _patch_messagebox(monkeypatch, _FakeMessageBox)
        update_window._checkForUpdates(silent=False)
        qtbot.waitUntil(lambda: len(_FakeMessageBox.instances) == 1, timeout=10000)
        assert "v9.9.0" in _FakeMessageBox.instances[0].text
        qtbot.waitUntil(
            lambda: update_window._fileStatusLabel.text() == "No file open",
            timeout=10000,
        )

    def test_check_error_silent_by_default(self, update_window, qtbot, monkeypatch):
        def _raise(timeout=15):
            raise urllib.error.URLError("offline")

        monkeypatch.setattr(Updater, "fetch_latest_release", _raise)
        _patch_messagebox(monkeypatch, _FakeMessageBox)
        update_window._checkForUpdates(silent=True)
        qtbot.waitUntil(
            lambda: update_window._fileStatusLabel.text() == "No file open",
            timeout=10000,
        )
        assert _FakeMessageBox.calls == []

