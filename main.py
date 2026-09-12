import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.MainWindow import MainWindow


def _find_app_icon():
    base = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
        candidates = [
            os.path.join(base, "app", "icon.ico"),
            os.path.join(base, "app", "icon.png"),
            os.path.join(base, "app", "logo.png"),
        ]
    else:
        candidates = [
            os.path.join(base, "app", "icon.ico"),
            os.path.join(base, "app", "icon.png"),
            os.path.join(base, "app", "logo.png"),
        ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    return None


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("mark_chini")

    icon_path = _find_app_icon()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
