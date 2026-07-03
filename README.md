# mark_chini

A desktop Markdown-to-PDF converter with live preview, built with PyQt6 and Typst.

## Features

- **Live Preview** – Split-pane editor with syntax-highlighted Markdown on the left and rendered HTML preview on the right
- **PDF Export** – High-quality PDF output via the Typst typesetting engine
- **Dark & Light Themes** – Toggle between a dark navy theme and a clean light theme
- **Markdown Support** – Headings, bold, italic, code blocks, tables, fenced code, lists, blockquotes, images, links, and more
- **Customizable** – Font family, font size, and margin settings

## Screenshot

![mark_chini](app/logo.png)

## Installation

### Option 1: Download the Installer (Recommended)

Download the latest installer from the [Releases page](https://github.com/JonamMadeda/mark_chini/releases/latest) and run it. The app will be installed with a start menu shortcut and desktop icon.

### Option 2: Portable EXE

Download `mark_chini.exe` from the [Releases page](https://github.com/JonamMadeda/mark_chini/releases/latest). No installation required.

### Option 3: Run from Source

**Requirements:** Python 3.10+

```bash
git clone https://github.com/JonamMadeda/mark_chini.git
cd mark_chini
pip install -r requirements.txt
python main.py
```

## Usage

1. Open the app
2. Type or paste Markdown in the left editor pane
3. See the live preview update on the right
4. Click **Export PDF** in the toolbar to generate a PDF

## Build

To build a standalone executable:

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "mark_chini" --add-data "app;app" --add-data "typst.exe;." --hidden-import markdown --hidden-import PyQt6 main.py
```

## Development

Run tests:

```bash
$env:QT_QPA_PLATFORM="offscreen"
pytest tests/
```

## License

MIT
