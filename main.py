import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QIcon
from app.MainWindow import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("mark_chini")

    base = os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    icon_path = os.path.join(base, "app", "logo.png")
    if os.path.isfile(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
