# Specification

## App Identity
- **Name**: mark_chini
- **Window title**: "mark_chini"
- **Icon**: 256px stylized "mc" logo (generated via QPainter, stored as `app/logo.png`)

## UI Layout
- **Toolbar**: Logo icon + "mark_chini" title (left), Open/Save/Export PDF + theme toggle + gallery (center), Font/Size/Margin combos (right)
- **Editor**: Monospace font (Consolas/Courier New), 14px, 4-space tab stops, widget-width line wrap
- **Preview**: Renders HTML via QTextBrowser with external links enabled
- **Splitter**: 50/50 with 3px handle, not collapsible, stretch factor 1:1
- **Status bar**: File name (left), word count (right)

## Themes
- **Dark** (#0d1117 bg, #161b22 surfaces, #30363d borders, #e6edf3 text) — GitHub-dark inspired
- **Light** (#ffffff bg, #f6f8fa surfaces, #d0d7de borders, #24292f text) — GitHub-light inspired
- Toggle via ☾ button with checked state; preview HTML also theme-aware

## PDF Export (Typst)

### Page Setup
```
#set page(paper: "a4", margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm))
```

### Header/Footer
- Header: "Chapter 1 – Foundations of Womanhood" (right-aligned, 8pt gray)
- Footer: Page number via `locate(loc => counter(page).at(loc).first())` (centered, 9pt gray)

### Typography
- Font: Times New Roman, Georgia, serif (hardcoded Serif)
- Size: 11pt (hardcoded, not controlled by Size combo)
- Paragraph: justified, 0.8em leading, 2em spacing
- Hyphenation: disabled

### Heading Show Rules
- H1: 1.6em bold, horizontal rule underline (0.5pt gray), 1.5em below spacing
- H2: 1.3em bold, no underline, 1em below spacing

### Content Block
- Body wrapped in `[...]` content block to isolate from outer layout macros

## Sanitization Pipeline

### _mdToTypst() — Markdown-to-Typst conversion
1. Horizontal rules → `#line(length: 100%)`
2. Bold/italic/strikethrough → Typst equivalents
3. Links → `#link("url")[text]`
4. Images → `#image("url", alt: "...")`
5. Blockquotes → `#quote[...]`
6. Headings H1-H6 → `= ` through `====== `
7. Ordered lists → `+ ` prefix
8. Remaining `#` → `\#` (escape for user content)

### _sanitizeTypst() — Escape user content, protect commands
1. Normalize line endings + dedent
2. Protect injected commands (`#link`, `#strike`, `#image`, `#quote`, `#line`) with sentinel placeholders
3. Escape `\`, `$`, `{`, `}`, `[`, `]` in user content
4. Restore protected commands from placeholders
5. Strip trailing whitespace, ensure trailing newline

## Syntax Highlighting (MarkdownHighlighter)
- **Headings**: H1-H6 with distinct colors (#ff7b72 → #a5d6ff), decreasing size delta
- **Bold/Italic/Bold-Italic**: Separate formats
- **Inline code**: Blue (#79c0ff) on dark background (#252d3d), Consolas font
- **Links**: Blue (#58a6ff) with underline
- **Images**: Gray (#8b949e) with underline
- **Lists**: Green (#7ee787)
- **Blockquotes**: Gray (#8b949e) with italic
- **Strikethrough**: Gray with strikethrough enabled
- **Code blocks** (```): Full-line blue-on-dark, state machine tracking

## Build (PyInstaller)
```
pyinstaller --onefile --windowed --name "mark_chini" ^
  --add-data "app;app" --add-data "typst.exe;." ^
  --hidden-import markdown --hidden-import PyQt6 main.py
```

## Tests
- 78 tests across 10 classes
- Run: `pytest tests/test_app.py -v`
- Headless: `$env:QT_QPA_PLATFORM="offscreen"`
