"""Theme contrast guards (WCAG 2.1 AA: 4.5:1 for text, 3:1 for large/UI).

Covers the syntax-highlighter palettes, the HTML preview pairs, and the key
QSS editor/preview rules so white-on-white text can never regress.
"""

import re

import pytest

from app.Highlighter import DARK_PALETTE, LIGHT_PALETTE
from app.MainWindow import LIGHT_THEME


def _luminance(hex_color):
    hex_color = hex_color.lstrip("#")
    rgb = [int(hex_color[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    rgb = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def contrast(fg, bg):
    hi, lo = max(_luminance(fg), _luminance(bg)), min(
        _luminance(fg), _luminance(bg)
    )
    return (hi + 0.05) / (lo + 0.05)


def _block_colors(stylesheet, selector):
    """Extract (foreground, background) hex colors from a QSS selector block."""
    match = re.search(
        re.escape(selector) + r"\s*\{([^}]*)\}", stylesheet, re.DOTALL
    )
    assert match, f"selector not found: {selector}"
    block = match.group(1)
    fg = re.search(r"(?<![\w-])color\s*:\s*(#[0-9a-fA-F]{6})", block)
    bg = re.search(r"background(?:-color)?\s*:\s*(#[0-9a-fA-F]{6})", block)
    assert fg and bg, f"colors not found in block: {selector}"
    return fg.group(1), bg.group(1)


TEXT_KEYS = (
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "emphasis",
    "code_fg",
    "block_fg",
    "fence_fg",
    "link",
    "image",
    "list",
    "quote",
    "strike",
)


class TestHighlighterContrast:
    @pytest.mark.parametrize("key", TEXT_KEYS)
    def test_light_palette_on_white(self, key):
        assert contrast(LIGHT_PALETTE[key], "#ffffff") >= 4.5, key

    @pytest.mark.parametrize("key", TEXT_KEYS)
    def test_dark_palette_on_dark_bg(self, key):
        assert contrast(DARK_PALETTE[key], "#0b0f19") >= 4.5, key

    def test_hr_visible_in_both_themes(self):
        # decorative rule: 3:1 minimum so it is actually visible
        assert contrast(LIGHT_PALETTE["hr"], "#ffffff") >= 3.0
        assert contrast(DARK_PALETTE["hr"], "#0b0f19") >= 3.0

    def test_inline_code_chip_readable(self):
        assert contrast(LIGHT_PALETTE["code_fg"], LIGHT_PALETTE["code_bg"]) >= 4.5
        assert contrast(DARK_PALETTE["code_fg"], DARK_PALETTE["code_bg"]) >= 4.5

    def test_code_block_readable(self):
        assert contrast(LIGHT_PALETTE["block_fg"], LIGHT_PALETTE["block_bg"]) >= 4.5
        assert contrast(DARK_PALETTE["block_fg"], DARK_PALETTE["block_bg"]) >= 4.5


class TestPreviewContrast:
    def test_light_preview(self):
        from app.Converter import MarkdownConverter

        html = MarkdownConverter.toHtml("hello", darkMode=False)
        assert "#0f172a" in html and "#ffffff" in html
        assert contrast("#0f172a", "#ffffff") >= 4.5

    def test_dark_preview(self):
        from app.Converter import MarkdownConverter

        html = MarkdownConverter.toHtml("hello", darkMode=True)
        assert contrast("#f8fafc", "#0b0f19") >= 4.5


class TestStylesheetContrast:
    @pytest.mark.parametrize(
        "selector",
        ["QPlainTextEdit#markdownEditor", "QTextBrowser#previewBrowser"],
    )
    def test_editor_surfaces_have_readable_text(self, selector):
        fg, bg = _block_colors(LIGHT_THEME, selector)
        assert contrast(fg, bg) >= 4.5, f"{selector}: {fg} on {bg}"

    def test_no_white_text_on_light_surfaces(self):
        for selector in (
            "QPlainTextEdit#markdownEditor",
            "QTextBrowser#previewBrowser",
            "QLabel#paneLabel",
        ):
            fg, bg = _block_colors(LIGHT_THEME, selector)
            assert _luminance(bg) < 0.9 or _luminance(fg) < 0.5, selector


class TestThemeSwitch:
    def test_highlighter_follows_theme(self, qapp):
        from PyQt6.QtGui import QTextDocument

        from app.Highlighter import MarkdownHighlighter

        doc = QTextDocument()
        hl = MarkdownHighlighter(doc, darkMode=True)
        dark_rules = [f.foreground().color().name() for _, f in hl._rules]
        assert "#f8fafc" in dark_rules
        hl.setDarkMode(False)
        light_rules = [f.foreground().color().name() for _, f in hl._rules]
        assert "#f8fafc" not in light_rules
        assert "#0f172a" in light_rules
        hl.setDarkMode(True)
        assert "#f8fafc" in [f.foreground().color().name() for _, f in hl._rules]
