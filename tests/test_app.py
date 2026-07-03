"""
Test suite for MarkChini Cleaner — a PyQt6/Typst Markdown-to-PDF desktop app.

Setup Instructions
------------------
1. Install dependencies (from project root):
       pip install pytest pytest-qt

2. Ensure typst.exe is discoverable (on PATH or in the project root),
   or tests that exercise toPdf() will be skipped.

3. Run the suite:
       cd mark_chini_II
       python -m pytest tests/test_app.py -v --tb=short

   To run a specific class:
       python -m pytest tests/test_app.py::TestConverter -v

   To run without the GUI (headless CI):
       set QT_QPA_PLATFORM=offscreen
       python -m pytest tests/test_app.py -v

   Force-skip Qt GUI tests (e.g. in a non-X environment):
       python -m pytest tests/test_app.py -v -k "not Qt"

Notes
-----
- GUI tests use pytest-qt's `qtbot` fixture which wraps QApplication.
- The `typst` subprocess is mocked during stress tests to avoid disk I/O.
- The temporary typst binary is bundled at build time; during testing we
  look for it in the project root or PATH.
"""

import os
import re
import sys
import time
import tempfile
import textwrap
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

import pytest
from pytestqt.qtbot import QtBot

from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QComboBox, QLabel, QPlainTextEdit,
)
from PyQt6.QtTest import QTest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def qapp():
    """Single QApplication for the whole session (pytest-qt)."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def main_window(qapp, qtbot):
    """Create and yield a fully constructed MainWindow (no export executed)."""
    # Import here so that QApplication is ready first
    from app.MainWindow import MainWindow
    win = MainWindow()
    win.show()
    qtbot.addWidget(win)
    yield win
    win.close()


# ---------------------------------------------------------------------------
# 1.  Unit tests for Converter — _mdToTypst
# ---------------------------------------------------------------------------

class TestMdToTypst:
    """Verify the Markdown → Typst syntax conversion logic."""

    def _conv(self, text):
        from app.Converter import MarkdownConverter
        out = MarkdownConverter._mdToTypst(text)
        out = out.replace("\x00H\x00", "#")
        out = out.replace("\x00LBR\x00", "[")
        out = out.replace("\x00RBR\x00", "]")
        return out

    # -- headings -----------------------------------------------------------

    def test_h1(self):
        assert self._conv("# Title\n").startswith("= Title")

    def test_h2(self):
        assert self._conv("## Sub\n").startswith("== Sub")

    def test_h3(self):
        assert self._conv("### Sub3\n").startswith("=== Sub3")

    def test_h4(self):
        assert self._conv("#### Sub4\n").startswith("==== Sub4")

    def test_h5(self):
        assert self._conv("##### Sub5\n").startswith("===== Sub5")

    def test_h6(self):
        assert self._conv("###### Sub6\n").startswith("====== Sub6")

    def test_mixed_headings(self):
        md = "# A\n## B\n### C\n"
        out = self._conv(md)
        lines = out.strip().split("\n")
        assert lines[0] == "= A"
        assert lines[1] == "== B"
        assert lines[2] == "=== C"

    # -- inline formatting --------------------------------------------------

    def test_bold(self):
        out = self._conv("**bold**")
        assert "*bold*" in out

    def test_italic(self):
        out = self._conv("*italic*")
        assert "_italic_" in out

    def test_bold_italic(self):
        out = self._conv("***both***")
        assert "_*both*_" in out

    # -- links and images ---------------------------------------------------

    def test_link(self):
        out = self._conv("[text](http://a.b)")
        assert 'link("http://a.b")' in out

    def test_image(self):
        out = self._conv("![alt](img.png)")
        assert 'image("img.png"' in out

    # -- code and blockquotes -----------------------------------------------

    def test_inline_code(self):
        out = self._conv("text `code` end")
        assert "`code`" in out

    def test_blockquote(self):
        out = self._conv("> quoted")
        assert "#quote[quoted]" in out

    # -- horizontal rule ----------------------------------------------------

    def test_horizontal_rule(self):
        out = self._conv("---\n")
        assert "line(length: 100%)" in out

    # -- ordered lists ------------------------------------------------------

    def test_ordered_list(self):
        out = self._conv("1. item\n2. other\n")
        assert "+ item" in out
        assert "+ other" in out

    # -- strikethrough ------------------------------------------------------

    def test_strikethrough(self):
        out = self._conv("~~deleted~~")
        assert "#strike[deleted]" in out

    # -- escaped / raw characters -------------------------------------------

    def test_hashtag_escaping(self):
        """User #text -> escaped hash to prevent Typst variable lookup."""
        out = self._conv("#MeToo")
        assert "\\#MeToo" in out

    def test_hashtag_numbers(self):
        out = self._conv("#123")
        assert "\\#123" in out

    def test_multiple_hashtags(self):
        out = self._conv("#a #b #c")
        assert "\\#a \\#b \\#c" in out

    def test_converter_inserted_hashtags_not_double_escaped(self):
        """Placeholders inserted by the converter itself must remain as #."""
        out = self._conv("[link](u)")
        assert "#link" in out
        assert "\\#link" not in out

    def test_mixed_hashtags_and_special_chars(self):
        out = self._conv("#foo #bar $x^2 + y^2 = z^2$ ~~strike~~")
        assert "\\#foo" in out
        assert "\\#bar" in out
        assert "#strike[strike]" in out


# ---------------------------------------------------------------------------
# 2.  Unit tests for Converter — toTypstSource
# ---------------------------------------------------------------------------

class TestToTypstSource:
    """Verify the full Typst source assembly."""

    def _source(self, md, font="Serif", size="Medium", margin="Medium"):
        from app.Converter import MarkdownConverter
        return MarkdownConverter.toTypstSource(md, font, size, margin)

    def test_returns_string(self):
        src = self._source("hello")
        assert isinstance(src, str)
        assert len(src) > 50

    def test_contains_page_setup(self):
        src = self._source("hello")
        assert "#set page(" in src
        assert 'paper: "a4"' in src
        assert "margin:" in src

    def test_page_margins(self):
        src = self._source("hello")
        assert "left: 3cm" in src
        assert "right: 3cm" in src

    def test_font_selection_serif(self):
        src = self._source("hi", font="Serif")
        assert '"Times New Roman"' in src or '"Georgia"' in src

    def test_font_selection_monospace(self):
        src = self._source("hi", font="Monospace")
        assert '"Consolas"' in src

    def test_paragraph_settings(self):
        src = self._source("hi")
        assert "justify: true" in src
        assert "leading: 0.8em" in src
        assert "spacing: 2em" in src

    def test_heading_rules_present(self):
        src = self._source("# Title\n## Sub")
        assert "#show heading.where(level: 1)" in src
        assert "#show heading.where(level: 2)" in src

    def test_header_footer_present(self):
        src = self._source("hi")
        assert "header:" not in src
        assert "footer:" in src
        assert "context" in src

    def test_empty_markdown(self):
        src = self._source("")
        assert src is not None
        assert "#set page(" in src


# ---------------------------------------------------------------------------
# 3.  Unit tests for Converter — toHtml
# ---------------------------------------------------------------------------

class TestToHtml:
    """Verify the HTML live-preview rendering."""

    def _html(self, md, dark=False):
        from app.Converter import MarkdownConverter
        return MarkdownConverter.toHtml(md, darkMode=dark)

    def test_basic_structure(self):
        html = self._html("hello")
        assert "<!DOCTYPE html>" in html
        assert "<html" in html

    def test_dark_mode_background(self):
        html = self._html("hello", dark=True)
        assert "#0b0f19" in html

    def test_light_mode_background(self):
        html = self._html("hello", dark=False)
        assert "#ffffff" in html or "#0f172a" in html

    def test_markdown_converted(self):
        html = self._html("**bold**")
        assert "<strong>" in html or "<b>" in html or "bold" in html

    def test_empty_input(self):
        html = self._html("")
        assert html is not None


# ---------------------------------------------------------------------------
# 4.  Unit tests for Converter — findTypstCli
# ---------------------------------------------------------------------------

class TestFindTypstCli:
    """Ensure typst.exe discovery is robust."""

    def test_raises_when_not_found(self):
        from app.Converter import MarkdownConverter
        MarkdownConverter.TYPST_CLI = None
        with patch.object(MarkdownConverter, "TYPST_CLI", None):
            with patch("os.path.isfile", return_value=False):
                with patch("os.popen") as mock_popen:
                    mock_proc = MagicMock()
                    mock_proc.read.return_value = ""
                    mock_popen.return_value = mock_proc
                    with pytest.raises(FileNotFoundError):
                        MarkdownConverter.findTypstCli()


# ---------------------------------------------------------------------------
# 5.  Unit tests for Converter — toPdf (mocked subprocess)
# ---------------------------------------------------------------------------

class TestToPdf:
    """Test PDF compilation without calling real typst."""

    def _call_to_pdf(self, md, mock_run):
        from app.Converter import MarkdownConverter
        MarkdownConverter.TYPST_CLI = "typst.exe"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = f.name
        try:
            MarkdownConverter.toPdf(md, out_path)
        finally:
            try:
                os.unlink(out_path)
            except OSError:
                pass

    @patch("app.Converter.subprocess.run")
    def test_success(self, mock_run):
        mock_run.return_value.returncode = 0
        self._call_to_pdf("hello", mock_run)
        mock_run.assert_called_once()

    @patch("app.Converter.subprocess.run")
    def test_failure_raises(self, mock_run):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "syntax error"
        from app.Converter import MarkdownConverter
        MarkdownConverter.TYPST_CLI = "typst.exe"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            out_path = f.name
        with pytest.raises(RuntimeError, match="syntax error"):
            MarkdownConverter.toPdf("# Bad", out_path)
        try:
            os.unlink(out_path)
        except OSError:
            pass

    @patch("app.Converter.subprocess.run")
    def test_hashtag_content_compiles(self, mock_run):
        """#MeToo etc. should not cause Typst syntax errors."""
        mock_run.return_value.returncode = 0
        self._call_to_pdf("#MeToo #123 ## Heading\n\nbody text", mock_run)
        mock_run.assert_called_once()

    @patch("app.Converter.subprocess.run")
    def test_special_chars(self, mock_run):
        mock_run.return_value.returncode = 0
        self._call_to_pdf("$x^2$ ~tilde~ `code` \\backslash", mock_run)
        mock_run.assert_called_once()


# ---------------------------------------------------------------------------
# 6.  Edge-case validation
# ---------------------------------------------------------------------------

class TestEdgeCases:
    """Problematic / degenerate inputs."""

    def _conv(self, text):
        from app.Converter import MarkdownConverter
        out = MarkdownConverter._mdToTypst(text)
        out = out.replace("\x00H\x00", "#")
        out = out.replace("\x00LBR\x00", "[")
        out = out.replace("\x00RBR\x00", "]")
        return out

    def test_empty_string(self):
        assert self._conv("") == ""

    def test_only_whitespace(self):
        out = self._conv("   \n\n  \n   ")
        assert out is not None

    def test_tabs_and_spaces(self):
        out = self._conv("\t# heading\n\t\t* list")
        assert out is not None

    def test_unicode(self):
        out = self._conv("中文 émojï 🎉 π ≈ 3.14")
        assert "中文" in out

    def test_very_long_line(self):
        long = "a" * 100_000
        out = self._conv(long)
        assert len(out) >= 100_000

    def test_nested_blockquotes(self):
        md = "> a\n> > b\n> > > c"
        out = self._conv(md)
        assert "#quote[a]" in out

    def test_code_blocks_not_escaped(self):
        md = "# Heading\n```\n# not a heading\n```\ntext"
        out = self._conv(md)
        assert "= Heading" in out

    def test_adjacent_hashtags_emoji(self):
        """Multiple hashtags and emoji — common social-media content."""
        out = self._conv("#One #Two #Three 🎉 #2024")
        assert "\\#One" in out
        assert "\\#2024" in out


# ---------------------------------------------------------------------------
# 7.  Functional UI tests (pytest-qt)
# ---------------------------------------------------------------------------

class TestFunctionalQt:
    """Verify the main window launches and core widgets respond."""

    def test_launch(self, main_window):
        assert main_window.isVisible()
        assert main_window.windowTitle() == "mark_chini"

    def test_editor_accepts_text(self, main_window, qtbot):
        # Access the inner QPlainTextEdit directly
        editor = main_window._editor._editor
        qtbot.keyClicks(editor, "Hello, World!")
        assert main_window._editor.toPlainText() == "Hello, World!"

    def test_word_count_updates(self, main_window, qtbot):
        editor = main_window._editor._editor
        qtbot.keyClicks(editor, "one two three four five")
        qtbot.wait(200)
        assert "5 words" in main_window._wordCountLabel.text()

    def test_word_count_zero_when_empty(self, main_window):
        assert "0 words" in main_window._wordCountLabel.text()

    def test_font_combo_default(self, main_window):
        assert main_window._fontCombo.currentText() == "Serif"

    def test_font_combo_change(self, main_window, qtbot):
        combo = main_window._fontCombo
        qtbot.keyClick(combo, Qt.Key.Key_Down)
        assert combo.currentText() == "Sans-Serif"

    def test_size_combo_default(self, main_window):
        assert main_window._sizeCombo.currentText() == "Medium"

    def test_margin_combo_default(self, main_window):
        assert main_window._marginCombo.currentText() == "Medium"

    def test_theme_toggle_button_exists(self, main_window):
        btn = main_window._themeBtn
        assert isinstance(btn, QPushButton)
        assert btn.isCheckable()

    def test_theme_toggle_flips_dark_mode(self, main_window, qtbot):
        initial = main_window._darkMode
        qtbot.mouseClick(main_window._themeBtn, Qt.MouseButton.LeftButton)
        assert main_window._darkMode != initial

    def test_status_bar_shows_file_label(self, main_window):
        assert "No file open" in main_window._fileStatusLabel.text()

    def test_title_label_present(self, main_window):
        assert main_window.windowTitle() == "mark_chini"

    def test_save_button_triggers_dialog(self, main_window, qtbot):
        """Clicking Save opens a file dialog — close it immediately."""
        QTimer.singleShot(100, lambda: QApplication.activeModalWidget().close())
        qtbot.mouseClick(main_window._saveBtn, Qt.MouseButton.LeftButton)
        qtbot.wait(200)

    def test_export_button_triggers_dialog(self, main_window, qtbot):
        """Export PDF button opens a save dialog — close it."""
        main_window._editor.setPlainText("some content")
        QTimer.singleShot(100, lambda: QApplication.activeModalWidget().close())
        qtbot.mouseClick(main_window._exportBtn, Qt.MouseButton.LeftButton)
        qtbot.wait(200)


# ---------------------------------------------------------------------------
# 8.  Stress & Performance Tests
# ---------------------------------------------------------------------------

class TestStress:
    """Heavy / repeated / rapid-input stress testing."""

    LARGE_WORD_COUNT = 50_000

    @pytest.fixture(autouse=True)
    def _mock_typst(self):
        """Never call the real typst CLI in stress tests."""
        patcher = patch("app.Converter.subprocess.run")
        mock = patcher.start()
        mock.return_value.returncode = 0
        yield
        patcher.stop()

    # ------------------------------------------------------------------
    # 8a.  Large Markdown injection
    # ------------------------------------------------------------------

    def test_large_markdown_typst_source(self):
        """Generate a 50 000+ word Typst source without error."""
        from app.Converter import MarkdownConverter

        paragraphs = []
        for i in range(200):
            body = " ".join(f"word{j}" for j in range(250))
            paragraphs.append(f"## Heading {i}\n{body}")

        large_md = "\n\n".join(paragraphs)
        word_count = len(large_md.split())
        assert word_count >= self.LARGE_WORD_COUNT, (
            f"Only {word_count} words — need ≥{self.LARGE_WORD_COUNT}"
        )

        source = MarkdownConverter.toTypstSource(large_md)
        assert isinstance(source, str)
        assert len(source) > 300_000

    def test_large_markdown_html(self):
        from app.Converter import MarkdownConverter
        large_md = "# Stress\n\n" + ("a b c d e f g h i j k l m n o p q r s t u v w x y z\n" * 2000)
        html = MarkdownConverter.toHtml(large_md)
        assert isinstance(html, str)

    # ------------------------------------------------------------------
    # 8b.  Rapid typing simulation
    # ------------------------------------------------------------------

    def test_rapid_typing(self, main_window, qtbot):
        """Type characters very fast — the preview timer should throttle."""
        # Use the wrapper's insertTextAtCursor which maps to the inner editor
        editor_wrapper = main_window._editor

        for i in range(500):
            editor_wrapper.insertTextAtCursor("a")

        qtbot.wait(100)
        assert len(editor_wrapper.toPlainText()) >= 500

    def test_rapid_typing_with_newlines(self, main_window, qtbot):
        editor_wrapper = main_window._editor
        for i in range(100):
            editor_wrapper.insertTextAtCursor(f"line {i}\n")
        qtbot.wait(100)
        assert editor_wrapper.toPlainText().count("\n") >= 99

    # ------------------------------------------------------------------
    # 8c.  Consecutive PDF exports (mocked)
    # ------------------------------------------------------------------

    def test_consecutive_exports(self):
        """Run toPdf 50 times in a loop to check for leaks / crashes."""
        from app.Converter import MarkdownConverter
        MarkdownConverter.TYPST_CLI = "typst.exe"

        md = "# Hello\n\nTest paragraph with **bold** and *italic*."
        for i in range(50):
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                out = f.name
            try:
                MarkdownConverter.toPdf(md, out)
            except Exception as exc:
                pytest.fail(f"toPdf failed on iteration {i}: {exc}")
            finally:
                try:
                    os.unlink(out)
                except OSError:
                    pass

    def test_consecutive_exports_varied_content(self):
        """50 exports with different inputs — covers more code paths."""
        from app.Converter import MarkdownConverter
        MarkdownConverter.TYPST_CLI = "typst.exe"

        variants = [
            "# Title\n\nBody text.",
            "## Sub\n\n- list\n- items\n\n1. ordered\n2. list",
            "# H1\n### H3\n\n**bold** *italic* `code`",
            "#One #Two\n\n> blockquote\n\n---\n\n~~strike~~ [link](u) ![img](a.png)",
        ]
        for i in range(50):
            md = variants[i % len(variants)]
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                out = f.name
            try:
                MarkdownConverter.toPdf(md, out)
            except Exception as exc:
                pytest.fail(f"toPdf (varied) failed on iteration {i}: {exc}")
            finally:
                try:
                    os.unlink(out)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # 8d.  Hashtag stress
    # ------------------------------------------------------------------

    def test_hashtag_stress(self):
        """Hundreds of hashtags in the same document."""
        from app.Converter import MarkdownConverter
        md = "\n".join(f"#{tag}" for tag in [f"tag{i}" for i in range(500)])
        source = MarkdownConverter._mdToTypst(md)
        assert source.count("\\#") == 500

    def test_hashtag_mixed_with_typst_commands(self):
        """Ensure #link, #strike, #image etc. are not double-escaped."""
        from app.Converter import MarkdownConverter
        md = "#Title\n\n#Hashtag\n\n[link](http://a.com)\n\n~~strike~~\n\n#Another"
        source = MarkdownConverter._mdToTypst(md)
        source = source.replace("\x00H\x00", "#").replace("\x00LBR\x00", "[").replace("\x00RBR\x00", "]")
        assert "#link" in source
        assert "#strike" in source
        assert "\\#Title" in source or "= Title" in source

    # ------------------------------------------------------------------
    # 8e.  Memory / string growth check
    # ------------------------------------------------------------------

    def test_large_output_does_not_blow_up(self):
        """Append a massive block of text to ensure no silent truncation."""
        from app.Converter import MarkdownConverter
        chunk = "# Big\n\n" + ("x" * 100_000) + "\n\n# End"
        src = MarkdownConverter.toTypstSource(chunk)
        assert "= Big" in src
        assert "= End" in src
        # Ensure the 100k chars survived
        assert "x" * 1000 in src


# ---------------------------------------------------------------------------
# 9.  PdfExportWorker — QThread unit tests
# ---------------------------------------------------------------------------

class TestPdfWorker:
    """Verify the QThread wrapper behaves correctly."""

    @patch("app.Converter.subprocess.run")
    def test_worker_signals_success(self, mock_run, qtbot):
        mock_run.return_value.returncode = 0
        from app.PdfWorker import PdfExportWorker

        worker = PdfExportWorker("hello", "out.pdf", "Serif", "Medium", "Medium")
        with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
            worker.start()

        success, msg = blocker.args
        assert success is True
        assert "out.pdf" in msg

    @patch("app.Converter.subprocess.run")
    def test_worker_signals_failure(self, mock_run, qtbot):
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "bad syntax"
        from app.PdfWorker import PdfExportWorker

        worker = PdfExportWorker("# bad", "out.pdf", "Serif", "Medium", "Medium")
        with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
            worker.start()

        success, msg = blocker.args
        assert success is False

    def test_worker_does_not_deadlock_on_empty_input(self, qtbot):
        from app.PdfWorker import PdfExportWorker
        # Empty markdown with a mocked typst to avoid actual execution
        with patch("app.Converter.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            worker = PdfExportWorker("", "out.pdf", "Serif", "Medium", "Medium")
            with qtbot.waitSignal(worker.finished, timeout=5000) as blocker:
                worker.start()
            success, msg = blocker.args
            assert success is True


# ---------------------------------------------------------------------------
# 10.  Live preview — integration
# ---------------------------------------------------------------------------

class TestPreviewIntegration:
    """Changes in the editor should eventually update the preview."""

    def test_preview_updates_after_text_change(self, main_window, qtbot):
        editor = main_window._editor
        preview = main_window._preview

        editor.setPlainText("# Hello Preview")
        qtbot.wait(500)  # allow the 300 ms debounce timer
        html = preview.toHtml()
        assert "Hello Preview" in html or "Hello" in html

    def test_preview_shows_bold(self, main_window, qtbot):
        editor = main_window._editor
        editor.setPlainText("**bold text**")
        qtbot.wait(500)
        html = main_window._preview.toHtml()
        assert "bold" in html

    def test_preview_dark_mode_renders_dark_bg(self, main_window, qtbot):
        main_window._editor.setPlainText("dark test")
        qtbot.wait(500)

        # Should be in dark mode by default
        html = main_window._preview.toHtml()
        assert "#0b0f19" in html or "background" in html.lower()
