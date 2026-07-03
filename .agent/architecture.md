# Architecture

## Overview
mark_chini is a PyQt6 desktop app that converts Markdown to PDF using the Typst CLI. It provides a split-pane editor with live HTML preview and one-click PDF export.

## Component Diagram

```
main.py
  └── QApplication
        └── MainWindow (QMainWindow)
              ├── QToolBar
              │     ├── [Open] [Save] [Export PDF]
              │     ├── [Theme Toggle] [Insert Image]
              │     └── Font/Size/Margin combos
              ├── QSplitter (50/50 horizontal)
              │     ├── MarkdownEditor (left pane)
              │     │     ├── "EDITOR" label
              │     │     ├── QPlainTextEdit
              │     │     └── MarkdownHighlighter (QSyntaxHighlighter)
              │     └── PreviewPanel (right pane)
              │           ├── "PREVIEW" label
              │           └── QTextBrowser
              └── QStatusBar
                    ├── File name (left)
                    └── Word count (right)
```

## Data Flow

### PDF Export (Background Thread)
```
Editor text → MainWindow._onExportPdf()
  → PdfExportWorker (QThread)
    → MarkdownConverter.toPdf()
      → toTypstSource()
        → _mdToTypst()     : Markdown → Typst syntax (placeholder tokens)
        → _sanitizeTypst()  : Escape Typst special chars, protect commands
        → f-string template : Wrap in #set page, show rules, etc.
      → Write .typ temp file
      → subprocess.run("typst.exe compile")
      → Cleanup temp file
  → Signal finished(bool, str) back to MainWindow
```

### Live Preview (Debounced)
```
Editor textChanged → QTimer (300ms single-shot)
  → MarkdownConverter.toHtml(text, darkMode)
    → markdown.markdown(text, extensions=[...])
    → Wrap in HTML + inline CSS (theme-aware colors)
  → PreviewPanel.setHtml(html)
```

## Key Patterns
- **QThread for export**: UI never blocks during PDF compilation
- **Debounced preview**: 300ms timer prevents re-render on every keystroke
- **Placeholder token sanitization**: Two-phase approach protects injected Typst commands while escaping user content
- **Static stylesheets**: DARK_THEME/LIGHT_THEME as module-level constants, swapped via setStyleSheet()
- **Dual-mode paths**: sys._MEIPASS for frozen builds, filesystem paths for development
