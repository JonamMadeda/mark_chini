# mark_chini — Application Documentation

> Desktop Markdown-to-PDF converter with live preview, built with **PyQt6** and **Typst**.
> Repository: `https://github.com/JonamMadeda/mark_chini`
> Entry point: `main.py` | App package: `app/` | Tests: `tests/` | Installer: `installer.iss`

---

## Table of Contents

1. [Overview](#1-overview)
2. [Features](#2-features)
3. [Functionality / User Workflows](#3-functionality--user-workflows)
4. [Tech Stack & Dependencies](#4-tech-stack--dependencies)
5. [Project Structure](#5-project-structure)
6. [Architecture & Data Flow](#6-architecture--data-flow)
7. [Module Reference](#7-module-reference)
8. [Markdown Support Matrix](#8-markdown-support-matrix)
9. [Markdown → Typst Conversion Pipeline](#9-markdown--typst-conversion-pipeline)
10. [Markdown → HTML Live Preview Pipeline](#10-markdown--html-live-preview-pipeline)
11. [Theming System](#11-theming-system)
12. [PDF Export System](#12-pdf-export-system)
13. [UI Layout](#13-ui-layout)
14. [Configuration & Customization](#14-configuration--customization)
15. [Installation](#15-installation)
16. [Usage](#16-usage)
17. [Build, Packaging & Distribution](#17-build-packaging--distribution)
18. [Testing](#18-testing)
19. [Error Handling](#19-error-handling)
20. [Security & Performance Notes](#20-security--performance-notes)
21. [Limitations & Known Gaps](#21-limitations--known-gaps)
22. [Future Improvements](#22-future-improvements)
23. [License](#23-license)

---

## 1. Overview

**mark_chini** is a Windows desktop application for writing Markdown and exporting
publication-quality PDFs.

- **Left pane:** tab-aware `QPlainTextEdit`-based Markdown editor with custom
  `QSyntaxHighlighter` (`app/Highlighter.py`).
- **Right pane:** `QTextBrowser`-based live HTML preview, debounced at 300 ms
  (`app/Preview.py`, `app/Converter.py::toHtml`).
- **Export:** Markdown → Typst source → `typst.exe compile` → PDF, executed off
  the UI thread via `QThread` (`app/Converter.py::toPdf`, `app/PdfWorker.py`).
- **Shell:** `QMainWindow` with toolbar, status bar, file open/save, font/size/
  margin selectors, dark/light toggle, and image-insert helper
  (`app/MainWindow.py`).
- **Distribution:** PyInstaller single-file `mark_chini.exe` + Inno Setup
  installer (`mark_chini.spec`, `installer.iss`, bundled `typst.exe`).

Python requirement: **3.10+**. OS target: **Windows** (uses `subprocess.STARTUPINFO`,
`where typst`, Inno Setup, `.exe` bundling).

---

## 2. Features

### 2.1 Editor

- Split-pane editing with `EDITOR` / `PREVIEW` pane headers.
- Placeholder text: `Type or paste Markdown here...`.
- Monospace editing font (`Consolas`, `Fira Code`, `Cascadia Code`).
- 4-space tab stops, widget-width line wrap.
- Full syntax highlighting for headings H1–H6, bold, italic, bold+italic,
  inline code, fenced code blocks, links, images, unordered/ordered lists,
  blockquotes, horizontal rules, strikethrough.
- Live word count in status bar (`0 words`, `N words`).
- Insert-image helper (🖼 gallery button) inserts `![name](path)` at cursor.

### 2.2 Live Preview

- Debounced rendering (300 ms single-shot `QTimer`) so rapid typing does not
  re-render on every keystroke.
- Renders via Python-`markdown` with extensions:
  `extra`, `tables`, `fenced_code`, `sane_lists`.
- Theme-aware HTML shell (dark navy `#0b0f19` / light `#ffffff`) with styled
  headings, code, `pre`, blockquotes, links, tables.
- External links open in system browser (`setOpenExternalLinks(True)`).
- Re-renders on text change and on Font/Size/Margin combo change (if editor
  non-empty).

### 2.3 PDF Export

- High-quality typeset PDF via bundled Typst CLI.
- Non-blocking: `PdfExportWorker(QThread)` with `progress` and
  `finished(bool, str)` signals.
- Export button state management: disabled + `Exporting...` label + status
  `Exporting PDF...` during run; restored afterwards.
- Success → info dialog `PDF saved to <path>`; failure → critical dialog.
- Typst document: A4, fixed margins, centered gray page-number footer,
  justified paragraphs, custom heading styles, configurable font family/size.

### 2.4 Theming

- Dark mode (default, navy `#0b0f19` / `#111827`) and light mode
  (`#f8fafc` / `#ffffff`).
- Toggle button (☾) in toolbar, `checkable=True`, `checked=True` initially.
- Complete QSS stylesheets (`DARK_THEME`, `LIGHT_THEME` in `MainWindow.py`,
  ~200 lines each) covering main window, toolbar, buttons, combos, pane
  labels, editor, preview, status bar, splitter handle, scrollbars.
- Accent: blue gradient (`#3B82F6 → #2563EB`) for Export; hover/pressed states
  for all controls.
- Preview HTML palette flips with `darkMode` flag.

### 2.5 File Operations

- **Open:** `*.md *.markdown *.mdown` filter, UTF-8 read, sets `_currentFile`,
  updates status label to basename, refreshes preview, warns on error.
- **Save:** writes to `_currentFile` if set, else Save-As dialog
  (`*.md` filter), UTF-8 write, updates status label, warns on error.
- **Export PDF:** requires non-empty editor; Save dialog `*.pdf`; delegates to
  worker thread.

### 2.6 Customization

- Toolbar combos:
  - Font: `Serif` (Times New Roman/Georgia) | `Sans-Serif` (Arial/Helvetica/
    Segoe UI) | `Monospace` (Consolas/Courier New). Default: `Serif`.
  - Size: `Small` (11pt) | `Medium` (12pt) | `Large` (14pt). Default: `Medium`.
  - Margin: `Small` (1.5cm) | `Medium` (2.5cm) | `Large` (3.5cm).
    Default: `Medium`. Note: see §21 — margin map is currently defined but
    the Typst template uses fixed margins.
- Window starts maximized, minimum size 1100×700, initial size 1400×850.
- App icon from `app/logo.png` (also shown 28×28 in toolbar).

---

## 3. Functionality / User Workflows

### 3.1 Write → Preview

1. User types in left editor → `MarkdownEditor.textChanged(str)` emitted.
2. `MainWindow._onEditorChanged` updates word count (`len(text.split())`),
   restarts 300 ms `_previewTimer`.
3. On timeout → `_updatePreview()` reads editor text + combo values +
   `_darkMode`, calls `MarkdownConverter.toHtml(...)`, pushes to
   `PreviewPanel.setHtml()`.

### 3.2 Open File

`Open` → `QFileDialog.getOpenFileName` → UTF-8 read → `setPlainText` →
`_currentFile = path` → status = basename → `_updatePreview()`.

### 3.3 Save File

`Save` → if `_currentFile` reuse it, else `getSaveFileName` → UTF-8 write →
`_currentFile = path` → status = basename.

### 3.4 Insert Image

Gallery button → image file dialog
(`*.png *.jpg *.jpeg *.gif *.bmp *.svg`) → inserts
`![basename](fullpath)` at text cursor.

### 3.5 Export PDF

1. Guard: empty editor → `Nothing to export` info box, abort.
2. Save dialog for `.pdf` path.
3. Disable Export button, set `Exporting...`, status `Exporting PDF...`.
4. Spawn `PdfExportWorker(markdown, path, font, size, margin)`, connect
   `finished` → `_onPdfFinished`, `start()`.
5. Worker runs `MarkdownConverter.toPdf()` off UI thread.
6. On finish: re-enable button, restore label, show success/failure dialog,
   update status.

### 3.6 Toggle Theme

Theme button `toggled` → `_darkMode = checked` → `_applyTheme()` (set QSS) →
`_updatePreview()` (re-render HTML palette).

---

## 4. Tech Stack & Dependencies

| Layer | Technology |
|---|---|
| GUI | PyQt6 ≥ 6.5 (`QMainWindow`, `QToolBar`, `QSplitter`, `QPlainTextEdit`, `QTextBrowser`, `QThread`, `QSyntaxHighlighter`, `QTimer`) |
| Markdown → HTML | `markdown` ≥ 3.5 (`extra`, `tables`, `fenced_code`, `sane_lists`) |
| Markdown → PDF | Typst CLI (`typst.exe`, bundled in `app/` and project root) |
| Packaging | PyInstaller (`--onefile --windowed`), Inno Setup (`installer.iss`) |
| Testing | `pytest`, `pytest-qt` (`qtbot`, `waitSignal`), `unittest.mock` |
| Language | Python 3.10+ |
| OS | Windows (uses `STARTUPINFO/SW_HIDE`, `where typst`, `.exe`/`.iss`) |

`requirements.txt` contains only the two runtime deps:

```text
PyQt6>=6.5
markdown>=3.5
```

---

## 5. Project Structure

```text
mark_chini_II/
├── main.py              # QApplication bootstrap, icon setup, showMaximized
├── app/
│   ├── __init__.py      # Re-exports MainWindow, MarkdownEditor, PreviewPanel,
│   │                    #   MarkdownConverter, PdfExportWorker, MarkdownHighlighter
│   ├── MainWindow.py    # QMainWindow shell: toolbar, splitter, status bar,
│   │                    #   themes (DARK_THEME/LIGHT_THEME), file/export/theme slots (~687 lines)
│   ├── Editor.py        # MarkdownEditor QWidget wrapper around QPlainTextEdit (~53 lines)
│   ├── Highlighter.py   # MarkdownHighlighter(QSyntaxHighlighter) rules (~133 lines)
│   ├── Preview.py       # PreviewPanel QWidget wrapper around QTextBrowser (~31 lines)
│   ├── Converter.py     # MarkdownConverter: _mdToTypst, _sanitizeTypst,
│   │                    #   toTypstSource, toHtml, toPdf, findTypstCli (~230 lines)
│   ├── PdfWorker.py     # PdfExportWorker(QThread) async export (~34 lines)
│   ├── logo.png         # App icon + toolbar pixmap
│   └── typst.exe        # Bundled Typst compiler (also duplicated at root for dev)
├── tests/
│   └── test_app.py      # ~717-line suite: converter units, edge cases, Qt functional,
│                        #   stress (50k words, 50× exports), worker, preview integration
├── docs/
│   └── APPLICATION.md   # This file
├── typst.exe            # Root copy used in dev / fallback discovery
├── requirements.txt     # PyQt6, markdown
├── mark_chini.spec      # PyInstaller Analysis/EXE spec (datas, hiddenimports)
├── installer.iss        # Inno Setup script (AppName/Version, Files, Icons, Run)
├── README.md            # User-facing features/install/usage/build summary
└── .gitignore           # dist/, build/, *.spec, __pycache__, venv, IDE, OS
```

Line counts are approximate and intended as a navigation aid.

Data-file notes:

- `mark_chini.spec` bundles `('app','app')` and `('typst.exe','.')` with
  `hiddenimports=['markdown','PyQt6']`, output `name='mark_chini'`,
  `console=False`, `upx=True`.
- `installer.iss`: `AppName=mark_chini`, `AppVersion=1.0`,
  `DefaultDirName={autopf}\mark_chini`, installs `dist\mark_chini.exe`,
  creates Start Menu + auto-programs + desktop icons, optional post-install
  launch. Requires admin privileges.

---

## 6. Architecture & Data Flow

```text
                    +------------------+
                    |   main.py        |
                    | QApplication     |
                    +--------+---------+
                             |
                    +--------v---------+
                    | MainWindow       |
                    | (QMainWindow)    |
                    +--+-----+----+---+
                       |     |    |
        +--------------+     |    +--------------+
        |                    |                   |
+-------v------+   +---------v--------+  +-------v--------+
| MarkdownEditor|  | PreviewPanel     |  | PdfExportWorker|
| QPlainTextEdit|  | QTextBrowser     |  | QThread        |
| +Highlighter  |  | setHtml(html)    |  | -> toPdf()     |
+-------+------+   +---------^--------+  +-------+--------+
        | textChanged(300ms) | toHtml()          | compile
        +------------------->+                   v
        |              MarkdownConverter    typst.exe compile
        |              _mdToTypst / toTypstSource / toHtml / toPdf
        +-----------------------------------> temp .typ -> .pdf
```

Key design decisions:

- **Separation of concerns:** UI (`MainWindow`, `Editor`, `Preview`),
  highlighting (`Highlighter`), conversion (`Converter`), async I/O
  (`PdfWorker`) are independent modules.
- **Debounced preview:** single-shot 300 ms `QTimer` prevents re-render
  storms during fast typing.
- **Background export:** `QThread` keeps the editor responsive during
  `typst compile` (up to 60 s timeout).
- **Dual rendering backends:** Python-`markdown` for fast HTML preview;
  custom regex translator for Typst (print-quality) output.
- **Frozen-aware paths:** both `main.py` and `MainWindow`/`Converter` resolve
  `sys._MEIPASS` when `sys.frozen` is true so the PyInstaller bundle finds
  `app/logo.png` and `typst.exe`.

---

## 7. Module Reference

### 7.1 `main.py` (26 lines)

- Creates `QApplication`, sets `ApplicationName="mark_chini"`.
- Resolves icon: `<base>/app/logo.png` (`base=sys._MEIPASS` if frozen, else
  script dir); sets `WindowIcon` if file exists.
- Instantiates `MainWindow`, `showMaximized()`, `app.exec()`.

### 7.2 `app/MainWindow.py` (687 lines)

- **State:** `_currentFile=None`, `_darkMode=True`, `_previewTimer` (300 ms,
  single-shot), `_pdfWorker=None`.
- ** `_buildUI`:** title `mark_chini`, app icon, min 1100×700, resize
  1400×850; calls `_buildToolbar`, `_buildCentralArea`, `_buildStatusBar`.
- **`_iconPath()` (static):** frozen → `<MEIPASS>/app/logo.png`; else
  `<app_dir>/logo.png`. Note asymmetry with `main.py` (see §21).
- **`_buildToolbar`:** non-movable `QToolBar`; 28 px logo pixmap +
  `mark_chini` title; `Open`/`Save`/`Export PDF` buttons; vertical separator;
  theme toggle (☾ `U+263E`, checkable, checked); gallery (🖼 `U+1F5BC`);
  expanding spacer; Font/Size/Margin labels + combos.
- **`_buildCentralArea`:** zero-margin `QVBoxLayout`; horizontal `QSplitter`
  (handle 3 px, non-collapsible); `MarkdownEditor` + `PreviewPanel` with
  stretch 1:1.
- **`_buildStatusBar`:** file label (`No file open` initially) + permanent
  word-count label (`0 words`).
- **Signals:** buttons → `_onOpen/_onSave/_onExportPdf/_onToggleTheme/
  _onInsertImage`; combos → `_onSettingChanged`; editor → `_onEditorChanged`.
- **Slots:** word-count + timer restart; conditional preview restart on
  settings; `_updatePreview`; open/save dialogs with `QMessageBox` errors;
  threaded export with button disabling; theme apply; image-link insertion.
- **Themes:** `DARK_THEME` / `LIGHT_THEME` QSS string constants (~197 lines
  each).

### 7.3 `app/Editor.py` (53 lines)

- `MarkdownEditor(QWidget)` with `textChanged(str)` signal.
- Layout: `paneLabel` (`EDITOR`) + `QPlainTextEdit#markdownEditor`
  (placeholder, 4-space tabs, `WidgetWidth` wrap).
- Attaches `MarkdownHighlighter(document)`; forwards inner `textChanged`.
- API: `toPlainText()`, `setPlainText(text)`, `clear()`,
  `insertTextAtCursor(text)`, `editorWidget()`.

### 7.4 `app/Highlighter.py` (133 lines)

- `MarkdownHighlighter(QSyntaxHighlighter)` with `_rules: list[(regex, fmt)]`.
- `_makeFormat(color, bold, italic, sizeDelta)` helper.
- Rules: H1–H6 (indigo/violet/blue palette, bold, growing size delta),
  bold-italic (`***`/`___`), bold (`**`/`__`), italic (single `*`/`_`),
  inline code (backticks, light-blue on dark bg, Consolas stack),
  links (indigo underline), images (gray underline), unordered (`- * +`)
  and ordered (`\d+.`) lists (amber `#FBBF24`), blockquotes (gray italic),
  HR (dark gray), strikethrough (`~~`, gray + strikeout).
- `highlightBlock`: stateful fenced-code tracking (`previousBlockState`/
  `setCurrentBlockState`, `1` = inside ```` ``` ````); code lines get
  distinct foreground/background and early-return; otherwise applies all
  regex rules via `globalMatch`.

### 7.5 `app/Preview.py` (31 lines)

- `PreviewPanel(QWidget)`: `paneLabel` (`PREVIEW`) + `QTextBrowser#previewBrowser`
  with `setOpenExternalLinks(True)`.
- API: `setHtml(html)`, `clear()`, `toHtml()`.

### 7.6 `app/Converter.py` (230 lines)

- Constants: `_HP=\x00H\x00`, `_LBR`, `_RBR` placeholders; `FONT_MAP`,
  `SIZE_MAP` (11/12/14pt), `MARGIN_MAP` (1.5/2.5/3.5cm), `TYPST_CLI=None`
  cache.
- `findTypstCli()` — checks `<base>/typst.exe`, `<parent>/typst.exe`,
  `<parent>/app/typst.exe` (frozen-aware), then `where typst`; caches result;
  raises `FileNotFoundError` with install hint if missing.
- `_mdToTypst(text)` — regex translator: `---` → `#line(length: 100%)`;
  `\*` escaping; `***`→`_*_*`, `**`→`*`, `*`→`_`; `~~~`/`~~`→`#strike[]`;
  `![alt](src)`→`#image`, `[t](u)`→`#link`; `1.`→`+`; `>`→`#quote[]`;
  `#…######`→`=…======`; lone `#`→`\#`. Uses placeholder tokens so
  converter-inserted `#`/`[`/`]` survive sanitization.
- `_sanitizeTypst(text)` — normalizes newlines, `dedent`, protects `\#`,
  converts em/en dashes, escapes `\ $ { } [ ]`, restores placeholders,
  ensures trailing newline.
- `toTypstSource(md, font, size, margin)` — builds full `.typ` doc: A4 page,
  fixed margins (top 2.5/bottom 2.5/left 3/right 3cm), centered gray footer
  page number via `context`, `set text(font,size)`, justified par
  (`leading 0.8em, spacing 2em`), H1/H2 `show` rules, then sanitized body.
- `toHtml(md, font, size, margin, darkMode)` — `markdown.markdown(...)` +
  theme-aware `<style>` shell; `font/size/margin` params accepted but only
  `darkMode` affects output (fixed 14 px body).
- `toPdf(md, out, font, size, margin)` — writes temp `.typ` (UTF-8,
  `delete=False`), runs `[cli, compile, typ, out]` hidden (`STARTUPINFO`,
  `SW_HIDE`), 60 s timeout, `capture_output`; non-zero → `RuntimeError`
  with stderr; always unlinks temp file.

### 7.7 `app/PdfWorker.py` (34 lines)

- `PdfExportWorker(QThread)` signals: `progress(str)`, `finished(bool,str)`.
- `__init__(markdownText, outputPath, fontChoice, sizeChoice, marginChoice)`.
- `run()`: emit progress → `MarkdownConverter.toPdf(...)` → emit
  `(True, PDF saved to ...)`; `FileNotFoundError` → `(False, Typst CLI not
  found: ...)`; `RuntimeError` → `(False, str(e))`; generic →
  `(False, Export failed: ...)`.

### 7.8 `app/__init__.py` (15 lines)

Re-exports the six public classes and defines `__all__`.

---

## 8. Markdown Support Matrix

| Construct | Editor highlight | HTML preview | Typst/PDF |
|---|---|---|---|
| H1–H6 (`#`) | Yes (per-level color/size) | Yes (via `markdown`) | Yes (`=`…`======`) |
| Bold (`**`) | Yes | Yes | Yes (`*…*`) |
| Italic (`*`/`_`) | Yes | Yes | Yes (`_…_`) |
| Bold+italic (`***`) | Yes | Yes | Yes (`_*…*_`) |
| Inline code (`` ` ``) | Yes | Yes | Pass-through |
| Fenced code (```` ``` ````) | Yes (block state) | Yes (`fenced_code`) | Pass-through (no special Typst `raw`) |
| Links `[t](u)` | Yes | Yes | Yes (`#link("u")[t]`) |
| Images `![a](s)` | Yes | Yes | Yes (`#image("s", alt:"a")`) |
| Unordered lists (`- * +`) | Yes | Yes | Pass-through (Typst `-` compatible) |
| Ordered lists (`1.`) | Yes | Yes | Normalized to `+` (auto-number) |
| Blockquotes (`>`) | Yes | Yes | Yes (`#quote[]`, nesting flattened) |
| HR (`---`) | Yes | Yes | Yes (`#line(length:100%)`) |
| Strikethrough (`~~`, `~~~`) | Yes (`~~` only) | Via `extra` | Yes (`#strike[]`) |
| Tables | No dedicated rule | Yes (`tables`, `extra`) | Pass-through (Markdown table syntax, not native Typst table) |
| `#hashtag` escaping | N/A | N/A | Yes (`\#`, converter tags exempt) |
| Escaped `\*` | N/A | N/A | Yes (placeholder round-trip) |
| Unicode/emoji | Pass-through | Pass-through | Pass-through (dashes normalized) |

---

## 9. Markdown → Typst Conversion Pipeline

1. **HR:** `^(-{3,})\s*$` → `\x00H\x00line(length: 100%)`.
2. **Escapes:** `\*` → `\x00ESC\x00` stash.
3. **Emphasis:** `***x` → BI tokens → `_*x*_`; `**x` → B tokens → `*x*`;
   `*x` → I tokens → `_x_`.
4. **Strike:** `~~~x~~~` / `~~x~~` → `#strike[x]` (via placeholders).
5. **Media:** `![a](s)` → `#image("s", alt:"a")`; `[t](u)` →
   `#link("u")[t]` (via placeholders).
6. **Lists:** `^\d+\.` → `+ `.
7. **Quotes:** `^ {0,3}>` → `#quote[…]` (via placeholders).
8. **Headings:** `#…` → `=…` preserving indent.
9. **Hash escape:** remaining `(?<!\\)#` → `\#`.
10. **Sanitize:** dedent, stash `\#`, normalize dashes, escape
    `\ $ { } [ ]`, restore `# [ ]`, trailing newline.
11. **Template:** inject into A4 page + font/size + par + heading-rules
    Typst preamble.

Placeholder design (`\x00H\x00` etc.) guarantees converter-generated Typst
commands are not mangled by the generic escaper.

---

## 10. Markdown → HTML Live Preview Pipeline

1. `markdown.markdown(text, extensions=[extra, tables, fenced_code, sane_lists])`.
2. Select palette by `darkMode` (dark: bg `#0b0f19`/fg `#f8fafc`/headings
   `#60A5FA`; light: bg `#ffffff`/fg `#0f172a`/headings `#2563EB`).
3. Wrap in `<!DOCTYPE html>` shell with inline `<style>` for `body, h1-h3,
   code, pre, blockquote, a, table/th/td`.
4. `PreviewPanel.setHtml()` → `QTextBrowser.setHtml()`.

Fixed preview body: `Segoe UI/Inter/Arial`, 14 px, 1.7 line-height, 16 px
padding. Font/Size/Margin combos are accepted as args but do not yet alter
preview CSS.

---

## 11. Theming System

- Two monolithic QSS strings in `MainWindow.py`: `DARK_THEME`, `LIGHT_THEME`.
- Selectors: `QMainWindow/QWidget`, `QMenuBar`, `QToolBar`, `QPushButton`
  (`#openBtn/#saveBtn/#exportBtn/#themeBtn/#galleryBtn` + hover/pressed/
  checked), `QComboBox` (+ drop-down + item view), `QLabel`
  (`#paneLabel/#titleLabel/#labelDim/#statusLabel`), `#markdownEditor`,
  `#previewBrowser`, `QStatusBar`, `QSplitter::handle`, `#toolbarSeparator`,
  vertical/horizontal `QScrollBar`.
- Dark: navy基 `#0b0f19`, panel `#111827`, borders `#1e293b/#374151`,
  text `#f8fafc`, dim `#94a3b8/#64748b`, accent `#3B82F6/#2563EB`.
- Light: bg `#f8fafc`, panel `#ffffff`, borders `#e2e8f0/#cbd5e1`, text
  `#0f172a`, dim `#475569`, accent `#2563EB/#1D4ED8`.
- Applied via `setStyleSheet(...)` in `_applyTheme()`; preview re-rendered
  to match.

---

## 12. PDF Export System

- **Discovery:** `findTypstCli()` with frozen-aware candidates + `where`
  fallback + caching (`TYPST_CLI` class attr).
- **Source gen:** `toTypstSource()` (see §9).
- **Compile:** temp `.typ` → `typst compile <tmp> <out.pdf>` hidden window,
  60 s timeout, captured output.
- **Threading:** `PdfExportWorker` ensures UI stays live; only `finished`
  touches UI (dialog + button + status).
- **Typst template highlights:**
  - `#set page(paper:"a4", margin:(top:2.5cm,bottom:2.5cm,left:3cm,right:3cm), footer: context{...pagenumber...})`
  - `#set text(font:(...), size: 11/12/14pt)`
  - `#set par(justify:true, leading:0.8em, spacing:2em)`
  - `#show heading.where(level:1): ... 1.6em bold #111111`
  - `#show heading.where(level:2): ... 1.3em bold #333333`

---

## 13. UI Layout

```text
+------------------------------------------------------------------+
| [logo] mark_chini | Open | Save | Export PDF | ☾ | 🖼 || Font:[]  |
|                                              Size:[]  Margin:[]  |
+------------------------------------------------------------------+
| EDITOR                              | PREVIEW                    |
|                                     |                            |
|  (QPlainTextEdit,                    |  (QTextBrowser,            |
|   syntax highlighted)                |   rendered HTML)           |
|                                     |                            |
+------------------------------------------------------------------+
| basename / No file open                              N words     |
+------------------------------------------------------------------+
```

- Toolbar: `TopToolBarArea`, `setMovable(False)`, 6–12 px padding, 8 px
  spacing.
- Splitter: horizontal, 3 px handle (blue on hover), non-collapsible,
  equal stretch.
- Status bar: left file label, right permanent word count.

---

## 14. Configuration & Customization

| Setting | Options | Effect |
|---|---|---|
| Font combo | Serif / Sans-Serif / Monospace | Typst `font:` list (preview fixed) |
| Size combo | Small / Medium / Large | Typst `size:` 11/12/14pt (preview fixed) |
| Margin combo | Small / Medium / Large | Defined in `MARGIN_MAP` but template currently fixed (see §21) |
| Theme button | Checked = dark / unchecked = light | QSS + preview palette |
| Window | Maximized, min 1100×700 | Set in `_buildUI` |
| Debounce | 300 ms | `_previewTimer` interval |
| Export timeout | 60 s | `subprocess.run(timeout=60)` |

No external config file; all settings are in-memory UI state.

---

## 15. Installation

### Option 1 — Installer (recommended)

Download from `Releases` page → run `mark_chini_setup.exe` (admin required)
→ Start Menu + desktop shortcuts.

### Option 2 — Portable EXE

Download `mark_chini.exe` from `Releases` → run directly, no install.

### Option 3 — From source

Requires Python 3.10+:

```bash
git clone https://github.com/JonamMadeda/mark_chini.git
cd mark_chini
pip install -r requirements.txt
python main.py
```

---

## 16. Usage

1. Launch app (maximized window).
2. Type/paste Markdown left; watch live preview right.
3. `Open` / `Save` for `.md` files; word count tracks input.
4. Adjust Font/Size/Margin combos as needed.
5. Toggle ☾ for dark/light; 🖼 to insert image link.
6. `Export PDF` → choose `.pdf` path → wait for `Export Complete`.

---

## 17. Build, Packaging & Distribution

Standalone EXE:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "mark_chini" \
  --add-data "app;app" --add-data "typst.exe;." \
  --hidden-import markdown --hidden-import PyQt6 main.py
```

Checked-in `mark_chini.spec` encodes the same: `datas=[('app','app'),
('typst.exe','.')]`, `hiddenimports=['markdown','PyQt6']`, `console=False`,
`upx=True`, `name='mark_chini'`.

Windows installer: build EXE to `dist\`, then compile `installer.iss` with
Inno Setup → `dist\mark_chini_setup.exe`.

---

## 18. Testing

Run:

```bash
$env:QT_QPA_PLATFORM="offscreen"
pytest tests/
```

Targeted:

```bash
python -m pytest tests/test_app.py -v --tb=short
python -m pytest tests/test_app.py::TestConverter -v
python -m pytest tests/test_app.py -v -k "not Qt"   # skip GUI
```

Coverage in `tests/test_app.py` (~717 lines, 10 sections):

1. `_mdToTypst` — headings H1–H6, bold/italic/both, links, images, inline
   code, blockquotes, HR, ordered lists, strikethrough, `#` escaping.
2. `toTypstSource` — string type, page setup, A4, margins, fonts, par
   justification, heading rules, footer, empty input.
3. `toHtml` — doctype, dark/light backgrounds, bold conversion, empty.
4. `findTypstCli` — `FileNotFoundError` when undiscoverable (mocked).
5. `toPdf` (mocked `subprocess.run`) — success, failure→`RuntimeError`,
   hashtag/special-char docs compile.
6. Edge cases — empty/whitespace/tabs, unicode/emoji, 100k-char line,
   nested quotes, code-block heading immunity, hashtag+emoji.
7. Functional Qt (`qtbot`) — launch/title, typing, word count 5/0, combo
   defaults + change, theme button exists/flips, status label, save/export
   dialogs (auto-closed via `QTimer.singleShot`).
8. Stress — 50k-word Typst + large HTML, 500-char / 100-line rapid typing,
   50× consecutive exports (fixed + varied, mocked), 500-hashtag docs,
   100k-char growth check.
9. `PdfExportWorker` — success/failure/empty signals via `waitSignal`.
10. Preview integration — text→preview, bold→preview, dark-bg render
    (500 ms waits for debounce).

---

## 19. Error Handling

| Location | Handling |
|---|---|
| Open/Save | `try/except` → `QMessageBox.warning(Could not open/save file)` |
| Export empty | `QMessageBox.information(Nothing to export)` + early return |
| Typst missing | `FileNotFoundError` → worker emits `(False, Typst CLI not found: …)` → critical dialog |
| Compile fail | `RuntimeError(stderr)` → `(False, …)` → critical dialog |
| Generic export | `Exception` → `(False, Export failed: …)` |
| Temp file | `finally: os.unlink(typPath)` guarded by `OSError` |
| Dialog cancel | Empty path → silent return |

---

## 20. Security & Performance Notes

- Typst invocation uses arg list (no shell), hidden window, 60 s timeout,
  captured output — no shell-injection surface.
- Temp `.typ` uses `NamedTemporaryFile(delete=False)` + explicit unlink;
  content is user Markdown transformed to Typst with escaping of
  `\ $ { } [ ] #`.
- `findTypstCli` caches path; uses `os.path.realpath` + `isfile` checks.
- Preview debounce (300 ms) + background `QThread` export keep UI fluid;
  stress-tested to 50k words / 300k+ char sources / 50 consecutive exports.
- Windows-only calls (`STARTUPINFO`, `where`) limit portability.

---

## 21. Limitations & Known Gaps

1. **Margin combo inert:** `MARGIN_MAP` defined but `toTypstSource` hard-codes
   `top:2.5/bottom:2.5/left:3/right:3cm`; Small/Large have no effect.
2. **Font/Size inert in preview:** `toHtml` ignores `font/size/margin`
   (fixed 14 px `Segoe UI` stack).
3. **Template gaps:** code blocks pass through as Markdown fences (no Typst
   `raw` block); tables pass through as Markdown (no native Typst `table`);
   unordered lists rely on `-` compatibility; nested quotes flattened.
4. **Icon path asymmetry:** `main.py` uses `<base>/app/logo.png` while
   `MainWindow._iconPath` uses `<app_dir>/logo.png` when not frozen
   (both work only because `base` differs); frozen path also branches
   inconsistently.
5. **Duplicate `import os`** at top of `MainWindow.py`.
6. **Windows-only:** `subprocess.STARTUPINFO`, `where typst`, bundled
   `typst.exe`, Inno Setup — macOS/Linux need porting.
7. **No persistence:** theme/font/size/margin/file history not saved between
   runs; no auto-save/recovery.
8. **Large binary in repo:** `typst.exe` committed twice (`app/` + root).
9. **`os.popen("where typst")`** without `shutil.which` fallback; PATH with
   spaces/newlines not robustly parsed.

---

## 22. Future Improvements

- Wire `MARGIN_MAP` into Typst `#set page(margin:…)`; wire font/size into
  preview CSS.
- Native Typst `raw` code blocks, `table` grids, `-`/`+` list fidelity,
  nested `quote` blocks.
- Persist settings via `QSettings`; recent-files menu; auto-save/dirty-dot.
- Cross-platform Typst discovery (`shutil.which`) + Linux/macOS packaging.
- Deduplicate `typst.exe` (single source + build copy); unify icon-path
  helper.
- Export progress bar, cancel button, page-count feedback.
- Find/replace, word-wrap toggle, zoom, print, HTML export.
- README badging, changelog, version bumping in `installer.iss`.

---

## 23. License

MIT — see `README.md`.
