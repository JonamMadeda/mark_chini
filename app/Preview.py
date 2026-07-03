from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTextBrowser


class PreviewPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._buildUI()

    def _buildUI(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        label = QLabel("PREVIEW")
        label.setObjectName("paneLabel")
        label.setContentsMargins(12, 6, 0, 4)
        layout.addWidget(label)

        self._browser = QTextBrowser()
        self._browser.setObjectName("previewBrowser")
        self._browser.setOpenExternalLinks(True)
        layout.addWidget(self._browser)

    def setHtml(self, html):
        self._browser.setHtml(html)

    def clear(self):
        self._browser.clear()

    def toHtml(self):
        return self._browser.toHtml()
