from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPalette
from PyQt6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout, QLabel

from app.Highlighter import MarkdownHighlighter


class MarkdownEditor(QWidget):
    textChanged = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buildUI()
        self._highlighter = MarkdownHighlighter(self._editor.document())
        self._editor.textChanged.connect(self._onTextChanged)

    def _buildUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel("EDITOR")
        label.setObjectName("paneLabel")
        label.setContentsMargins(12, 6, 0, 4)
        layout.addWidget(label)

        self._editor = QPlainTextEdit()
        self._editor.setPlaceholderText("Type or paste Markdown here...")
        self._editor.setObjectName("markdownEditor")
        self._editor.setTabStopDistance(
            self._editor.fontMetrics().horizontalAdvance(" ") * 4
        )
        self._editor.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        layout.addWidget(self._editor)

    def _onTextChanged(self):
        self.textChanged.emit(self._editor.toPlainText())

    def toPlainText(self):
        return self._editor.toPlainText()

    def setPlainText(self, text):
        self._editor.setPlainText(text)

    def clear(self):
        self._editor.clear()

    def insertTextAtCursor(self, text):
        cursor = self._editor.textCursor()
        cursor.insertText(text)

    def editorWidget(self):
        return self._editor

    def setDarkMode(self, darkMode):
        self._highlighter.setDarkMode(darkMode)
