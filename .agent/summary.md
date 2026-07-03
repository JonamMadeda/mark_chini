# Session Summary

## Current State
- **App**: Markdown-to-PDF desktop converter using PyQt6 + Typst CLI v0.15.0
- **Status**: Working — 78 tests pass, exe builds and launches
- **Python**: 3.14.4
- **PyQt6**: 6.11.0
- **PyInstaller**: 6.21.0

## Completed
- Default font changed to Serif
- Page numbering via locate/counter
- Dark/Light themes with theme-aware preview HTML
- Maximized launch (showMaximized)
- Hidden subprocess console (STARTUPINFO/SW_HIDE)
- App renamed from MarkChini to mark_chini
- Logo generated and set as window/toolbar icon
- _sanitizeTypst() with two-phase placeholder protection
- Background export via PdfExportWorker (QThread)
- 78 tests covering unit, functional, stress, integration
- Python 3.14 regex compatibility fix (lambda replacement for \xHH)

## Notable Decisions
- Body wrapped in `[...]` content block for Typst isolation
- App launches maximized
- Font size hardcoded at 11pt (Size combo is decorative)
- Margins hardcoded (Margin combo is decorative)
- typst.exe bundled and searched via fallback chain
- No print/export setup uses QPageLayout — all page config is in Typst template
