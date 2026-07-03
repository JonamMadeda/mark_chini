# File Reference

## Source Files

| File | Lines | Purpose |
|------|-------|---------|
| `main.py` | 26 | Entry point: creates QApplication, sets icon, opens MainWindow maximized |
| `app/MainWindow.py` | 655 | Main window, toolbar, splitter, status bar, signal wiring, theme constants |
| `app/Converter.py` | 249 | MarkdownConverter: toTypstSource, toHtml, toPdf, _mdToTypst, _sanitizeTypst |
| `app/Editor.py` | 53 | MarkdownEditor widget wrapping QPlainTextEdit with highlighter |
| `app/Preview.py` | 31 | PreviewPanel wrapping QTextBrowser for HTML preview |
| `app/Highlighter.py` | 132 | MarkdownHighlighter (QSyntaxHighlighter) for Markdown syntax coloring |
| `app/PdfWorker.py` | 34 | PdfExportWorker QThread for non-blocking PDF export |
| `app/__init__.py` | 15 | Package init, re-exports all classes |

## Test Files

| File | Lines | Tests | Purpose |
|------|-------|-------|---------|
| `tests/test_app.py` | 708 | 78 | Unit, functional, stress, and integration tests across 10 classes |

## Build Artifacts

| File | Purpose |
|------|---------|
| `dist/mark_chini.exe` | Frozen single-file executable |
| `typst.exe` | Typst CLI v0.15.0 binary (bundled in exe) |

## Application Data

| File | Purpose |
|------|---------|
| `app/logo.png` | 256px app icon (stylized "mc" on dark rounded square with blue accent) |

## Test Classes

| Class | Tests | Area |
|-------|-------|------|
| `TestMdToTypst` | 18 | Markdown → Typst conversion (headings, bold, italic, links, images, blockquotes, lists, strikethrough, hashtags) |
| `TestToTypstSource` | 10 | Full Typst template output (page setup, margins, fonts, heading rules, header/footer) |
| `TestToHtml` | 5 | HTML preview generation (structure, dark/light mode, basic conversion) |
| `TestFindTypstCli` | 1 | Typst binary discovery error handling |
| `TestToPdf` | 5 | PDF export (success, failure, edge cases), all mocked |
| `TestEdgeCases` | 7 | Edge cases (empty, whitespace, unicode, long lines, nested blockquotes, code blocks, hashtags+emoji) |
| `TestFunctionalQt` | 13 | UI functional tests (visibility, editor, combos, theme toggle, status bar, dialogs) |
| `TestStress` | 10 | Stress tests (50k words, rapid typing, 50 exports, 500 hashtags, 100k char output) |
| `TestPdfWorker` | 3 | QThread integration (success/failure signals, empty input) |
| `TestPreviewIntegration` | 3 | Preview panel HTML rendering (text changes, bold, dark mode) |
