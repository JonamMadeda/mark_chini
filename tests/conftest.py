"""Shared test configuration.

The MainWindow schedules a background update check ~2.5 s after construction.
That check hits the live GitHub API, which GUI tests must never depend on, so
it is disabled for the whole suite. Update logic itself is covered by
tests/test_updater.py with mocked networking.
"""

import os

os.environ.setdefault("MARK_CHINI_SKIP_UPDATE_CHECK", "1")
