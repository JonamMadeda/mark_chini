# Coding Rules

## General
- No comments in code unless required for clarity
- No emojis in code or documentation
- Use concise variable/function names; avoid unnecessary verbosity
- Keep functions short; one responsibility per function

## Python Style
- Use type hints for function signatures where feasible
- Class methods that don't need instance state should be @staticmethod
- Use `os.path.join()` for path construction (cross-platform compatible)
- Use f-strings for string formatting (Python 3.6+)
- Use `re.MULTILINE` for `^`/`$` anchoring in multi-line regex

## PyQt6 Conventions
- Enums use scoped access: `Qt.Orientation.Horizontal`, `QPageLayout.Orientation.Portrait`
- Never use shorthand enum values (no `Qt.AlignLeft`, use `Qt.AlignmentFlag.AlignLeft`)
- Import from specific submodules: `from PyQt6.QtCore import Qt`, not `from PyQt6 import QtCore`
- Use objectName for stylesheet targeting: `widget.setObjectName("paneLabel")`
- Always call `super().__init__()` in __init__

## Converter (Converter.py)
- `_HP = "\x00H\x00"` is the placeholder for Typst's `#` prefix
- `_mdToTypst()` produces Typst source with injected commands (prefix = _HP)
- `_sanitizeTypst()` escapes user content while protecting injected commands
- Sanitization order matters: protect → escape → restore
- NEVER use `\xHH` in regex replacement strings (Python 3.14+ strict parser rejects it); use lambda replacements instead
- `toPdf()` must always clean up temp files in `finally` block
- `subprocess.run()` must use `startupinfo` with `SW_HIDE` for hidden window
- The typst binary path discovery uses fallback chain: frozen → app dir → parent dir → PATH

## MainWindow (MainWindow.py)
- Theme stylesheets are module-level constants (DARK_THEME, LIGHT_THEME)
- Theme toggle changes both QMainWindow stylesheet and preview HTML
- Preview uses 300ms debounce timer (`_previewTimer`, single-shot)
- Export disables the button and shows "Exporting..." to prevent double-clicks
- File dialog filters must include both the targeted extension and "All Files"

## Templates
- Typst template body goes inside `[...]` content block for isolation
- Font size is hardcoded 11pt (Size combo does not affect template)
- Margins are hardcoded (Margin combo does not affect template)
- Font choice is the only dynamic template parameter

## Tests
- Test classes grouped by component (TestMdToTypst, TestToTypstSource, etc.)
- Mock `subprocess.run` via `@patch("app.Converter.subprocess.run")`
- Use `qtbot.waitSignal` for async Qt signal testing
- Stress tests maintain realistic content sizes (50k+ words, 50 exports)
- Always verify via assertions, not print statements

## Build
- typst.exe must be copied before each build: `Copy-Item -Path "..." -Destination ".\typst.exe" -Force`
- Remove `build/` and `*.spec` after successful build to save disk space
- icon_path uses `sys._MEIPASS` when `sys.frozen` is True
- Hidden imports: `markdown`, `PyQt6`
