# Commands

## Run
```powershell
python main.py
```

## Build (PyInstaller)
```powershell
# Step 1: Copy typst binary (required before each build)
Copy-Item -Path "C:\Users\Me\AppData\Local\Temp\typst-cli\typst-x86_64-pc-windows-msvc\typst.exe" -Destination ".\typst.exe" -Force

# Step 2: Build
pyinstaller --onefile --windowed --name "mark_chini" --add-data "app;app" --add-data "typst.exe;." --hidden-import markdown --hidden-import PyQt6 main.py

# Step 3: Clean up
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "*.spec" -Force -ErrorAction SilentlyContinue
```

## Tests
```powershell
# All tests
pytest tests/test_app.py -v

# With Qt offscreen (headless)
$env:QT_QPA_PLATFORM="offscreen"; pytest tests/test_app.py -v

# Specific class
pytest tests/test_app.py::TestConverter -v

# Skip Qt-dependent tests
pytest tests/test_app.py -v -k "not Qt"
```

## Launch Built Exe
```powershell
.\dist\mark_chini.exe
```
