"""In-app update checking against GitHub Releases.

Uses only the standard library (no new dependencies) and runs all network
I/O on QThreads so the UI never blocks.
"""

import json
import re
import urllib.request

from PyQt6.QtCore import QThread, pyqtSignal

# NOTE: keep in sync with AppVersion in installer.iss
APP_VERSION = "1.4.0"

GITHUB_OWNER = "JonamMadeda"
GITHUB_REPO = "mark_chini"
RELEASES_API_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
SETUP_ASSET_NAME = "mark_chini_setup.exe"

_USER_AGENT = {"User-Agent": "mark_chini-updater", "Accept": "application/vnd.github+json"}


def parse_version(text):
    """Parse a version tag like 'v1.3.0' into a comparable int tuple."""
    text = str(text).strip()
    if text[:1] in ("v", "V"):
        text = text[1:]
    match = re.match(r"(\d+(?:\.\d+)*)", text)
    if not match:
        return (0,)
    return tuple(int(part) for part in match.group(1).split("."))


def _padded(a, b):
    width = max(len(a), len(b))
    return a + (0,) * (width - len(a)), b + (0,) * (width - len(b))


def is_newer(latest_tag, current_version=APP_VERSION):
    """Return True if latest_tag describes a version newer than current."""
    latest, current = _padded(parse_version(latest_tag), parse_version(current_version))
    return latest > current


def fetch_latest_release(timeout=15):
    """Query the GitHub API for the latest release. Returns a dict."""
    request = urllib.request.Request(RELEASES_API_URL, headers=_USER_AGENT)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    tag = str(data.get("tag_name", "")).strip()
    page_url = str(
        data.get("html_url", f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest")
    )
    asset_url = None
    for asset in data.get("assets", []) or []:
        if asset.get("name") == SETUP_ASSET_NAME:
            asset_url = asset.get("browser_download_url")
            break
    return {
        "update": bool(tag) and is_newer(tag),
        "tag": tag,
        "page_url": page_url,
        "asset_url": asset_url,
        "error": None,
    }


class UpdateCheckWorker(QThread):
    """Background worker that checks GitHub for a newer release."""

    result = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

    def run(self):
        try:
            self.result.emit(fetch_latest_release())
        except Exception as e:  # offline, rate-limited, API changed, ...
            self.result.emit(
                {
                    "update": False,
                    "tag": "",
                    "page_url": (
                        f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
                    ),
                    "asset_url": None,
                    "error": str(e),
                }
            )


class UpdateDownloadWorker(QThread):
    """Background worker that downloads the setup installer with progress."""

    progress = pyqtSignal(int, int)  # bytes_downloaded, bytes_total (0 if unknown)
    finished = pyqtSignal(bool, str)  # ok, dest_path or error message

    def __init__(self, url, dest_path, parent=None):
        super().__init__(parent)
        self._url = url
        self._dest_path = dest_path

    def run(self):
        try:
            request = urllib.request.Request(self._url, headers=_USER_AGENT)
            with urllib.request.urlopen(request, timeout=30) as response:
                try:
                    total = int(response.getheader("Content-Length") or 0)
                except (TypeError, ValueError):
                    total = 0
                downloaded = 0
                with open(self._dest_path, "wb") as f:
                    while True:
                        if self.isInterruptionRequested():
                            raise InterruptedError("cancelled")
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        self.progress.emit(downloaded, total)
            self.finished.emit(True, self._dest_path)
        except InterruptedError:
            self._remove_partial()
            self.finished.emit(False, "cancelled")
        except Exception as e:
            self._remove_partial()
            self.finished.emit(False, str(e))

    def _remove_partial(self):
        try:
            import os

            if os.path.isfile(self._dest_path):
                os.remove(self._dest_path)
        except OSError:
            pass
