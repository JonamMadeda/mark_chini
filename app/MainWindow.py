import os

import os
import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QSplitter,
    QPushButton, QComboBox, QLabel, QStatusBar, QToolBar,
    QFileDialog, QMessageBox, QFrame, QSizePolicy,
)

from app.Editor import MarkdownEditor
from app.Preview import PreviewPanel
from app.Converter import MarkdownConverter
from app.PdfWorker import PdfExportWorker


DARK_THEME = """
QMainWindow, QWidget {
    background-color: #0b0f19;
    color: #f8fafc;
}
QMenuBar {
    background-color: #111827;
    color: #f8fafc;
    border-bottom: 1px solid #1e293b;
}
QMenuBar::item:selected {
    background-color: #1f2937;
}
QToolBar {
    background-color: #111827;
    border: none;
    border-bottom: 1px solid #1e293b;
    padding: 6px 12px;
    spacing: 8px;
}
QPushButton {
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    min-height: 28px;
    padding: 4px 12px;
}
QPushButton#openBtn, QPushButton#saveBtn {
    background-color: #1f2937;
    color: #f3f4f6;
    border: 1px solid #374151;
}
QPushButton#openBtn:hover, QPushButton#saveBtn:hover {
    background-color: #374151;
    border-color: #3B82F6;
}
QPushButton#openBtn:pressed, QPushButton#saveBtn:pressed {
    background-color: #111827;
}
QPushButton#exportBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
    color: #ffffff;
    border: none;
    font-weight: bold;
}
QPushButton#exportBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60A5FA, stop:1 #3B82F6);
}
QPushButton#exportBtn:pressed {
    background: #1D4ED8;
}
QPushButton#themeBtn, QPushButton#galleryBtn {
    background: transparent;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 4px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #f8fafc;
}
QPushButton#themeBtn:hover, QPushButton#galleryBtn:hover {
    background-color: #1f2937;
    border-color: #3B82F6;
}
QPushButton#themeBtn:checked {
    background-color: #1E3A8A;
    border-color: #3B82F6;
}
QComboBox {
    background-color: #1f2937;
    color: #f8fafc;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 4px 28px 4px 12px;
    font-size: 13px;
    min-width: 100px;
    min-height: 28px;
}
QComboBox:hover {
    border-color: #3B82F6;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #111827;
    color: #f8fafc;
    border: 1px solid #374151;
    border-radius: 4px;
    padding: 4px 0;
    selection-background-color: #2563EB;
    selection-color: #ffffff;
    outline: none;
}
QLabel#paneLabel {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #94a3b8;
    background-color: #111827;
    border-bottom: 1px solid #1e293b;
    padding: 8px 12px;
}
QPlainTextEdit#markdownEditor {
    background-color: #0b0f19;
    color: #f8fafc;
    border: none;
    font-family: 'Consolas', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 14px;
    padding: 16px;
    selection-background-color: #1E3A8A;
}
QTextBrowser#previewBrowser {
    background-color: #0b0f19;
    color: #f8fafc;
    border: none;
    padding: 16px;
    selection-background-color: #1E3A8A;
}
QStatusBar {
    background-color: #111827;
    color: #94a3b8;
    border-top: 1px solid #1e293b;
    font-size: 12px;
    padding: 4px 8px;
}
QStatusBar::item {
    border: none;
}
QSplitter::handle {
    background-color: #1e293b;
    width: 3px;
}
QSplitter::handle:hover {
    background-color: #3B82F6;
}
QFrame#toolbarSeparator {
    color: #374151;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: 800;
    color: #3B82F6;
    padding: 0 8px 0 0;
}
QLabel#labelDim {
    color: #64748b;
    font-size: 12px;
    padding: 0 4px;
    font-weight: bold;
}
QLabel#statusLabel {
    color: #94a3b8;
    padding: 0 8px;
}
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #1e293b;
    border-radius: 5px;
    min-height: 30px;
    margin: 1px;
}
QScrollBar::handle:vertical:hover {
    background-color: #2563EB;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #1e293b;
    border-radius: 5px;
    min-width: 30px;
    margin: 1px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #2563EB;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""

LIGHT_THEME = """
QMainWindow, QWidget {
    background-color: #f8fafc;
    color: #0f172a;
}
QMenuBar {
    background-color: #ffffff;
    color: #0f172a;
    border-bottom: 1px solid #e2e8f0;
}
QMenuBar::item:selected {
    background-color: #f1f5f9;
}
QToolBar {
    background-color: #ffffff;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    padding: 6px 12px;
    spacing: 8px;
}
QPushButton {
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    min-height: 28px;
    padding: 4px 12px;
}
QPushButton#openBtn, QPushButton#saveBtn {
    background-color: #ffffff;
    color: #334155;
    border: 1px solid #cbd5e1;
}
QPushButton#openBtn:hover, QPushButton#saveBtn:hover {
    background-color: #f8fafc;
    border-color: #2563EB;
    color: #2563EB;
}
QPushButton#openBtn:pressed, QPushButton#saveBtn:pressed {
    background-color: #f1f5f9;
}
QPushButton#exportBtn {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #2563EB, stop:1 #1D4ED8);
    color: #ffffff;
    border: none;
    font-weight: bold;
}
QPushButton#exportBtn:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3B82F6, stop:1 #2563EB);
}
QPushButton#exportBtn:pressed {
    background: #1D4ED8;
}
QPushButton#themeBtn, QPushButton#galleryBtn {
    background: transparent;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px;
    min-width: 32px;
    min-height: 32px;
    font-size: 16px;
    color: #0f172a;
}
QPushButton#themeBtn:hover, QPushButton#galleryBtn:hover {
    background-color: #f8fafc;
    border-color: #2563EB;
}
QPushButton#themeBtn:checked {
    background-color: #DBEAFE;
    border-color: #2563EB;
}
QComboBox {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 4px 28px 4px 12px;
    font-size: 13px;
    min-width: 100px;
    min-height: 28px;
}
QComboBox:hover {
    border-color: #2563EB;
}
QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border: none;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    border-radius: 4px;
    padding: 4px 0;
    selection-background-color: #2563EB;
    selection-color: #ffffff;
    outline: none;
}
QLabel#paneLabel {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: #475569;
    background-color: #ffffff;
    border-bottom: 1px solid #e2e8f0;
    padding: 8px 12px;
}
QPlainTextEdit#markdownEditor {
    background-color: #ffffff;
    color: #0f172a;
    border: none;
    font-family: 'Consolas', 'Fira Code', 'Cascadia Code', monospace;
    font-size: 14px;
    padding: 16px;
    selection-background-color: #DBEAFE;
}
QTextBrowser#previewBrowser {
    background-color: #ffffff;
    color: #0f172a;
    border: none;
    padding: 16px;
    selection-background-color: #DBEAFE;
}
QStatusBar {
    background-color: #ffffff;
    color: #475569;
    border-top: 1px solid #e2e8f0;
    font-size: 12px;
    padding: 4px 8px;
}
QStatusBar::item {
    border: none;
}
QSplitter::handle {
    background-color: #cbd5e1;
    width: 3px;
}
QSplitter::handle:hover {
    background-color: #2563EB;
}
QFrame#toolbarSeparator {
    color: #e2e8f0;
}
QLabel#titleLabel {
    font-size: 18px;
    font-weight: 800;
    color: #2563EB;
    padding: 0 8px 0 0;
}
QLabel#labelDim {
    color: #475569;
    font-size: 12px;
    padding: 0 4px;
    font-weight: bold;
}
QLabel#statusLabel {
    color: #475569;
    padding: 0 8px;
}
QScrollBar:vertical {
    background-color: transparent;
    width: 10px;
    border: none;
}
QScrollBar::handle:vertical {
    background-color: #cbd5e1;
    border-radius: 5px;
    min-height: 30px;
    margin: 1px;
}
QScrollBar::handle:vertical:hover {
    background-color: #2563EB;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background-color: transparent;
    height: 10px;
    border: none;
}
QScrollBar::handle:horizontal {
    background-color: #cbd5e1;
    border-radius: 5px;
    min-width: 30px;
    margin: 1px;
}
QScrollBar::handle:horizontal:hover {
    background-color: #2563EB;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical,
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._currentFile = None
        self._darkMode = True
        self._previewTimer = QTimer()
        self._previewTimer.setSingleShot(True)
        self._previewTimer.setInterval(300)
        self._previewTimer.timeout.connect(self._updatePreview)

        self._pdfWorker = None
        self._buildUI()
        self._connectSignals()
        self._applyTheme()

    def _buildUI(self):
        self.setWindowTitle("mark_chini")
        self._setAppIcon()
        self.setMinimumSize(1100, 700)
        self.resize(1400, 850)

        self._buildToolbar()
        self._buildCentralArea()
        self._buildStatusBar()

    @staticmethod
    def _iconPath():
        base = os.path.dirname(os.path.abspath(__file__))
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
            candidates = [
                os.path.join(base, "app", "logo.png"),
                os.path.join(base, "app", "icon.png"),
                os.path.join(base, "app", "icon.ico"),
            ]
        else:
            candidates = [
                os.path.join(base, "logo.png"),
                os.path.join(base, "icon.png"),
                os.path.join(base, "icon.ico"),
            ]
        for path in candidates:
            if os.path.isfile(path):
                return path
        return candidates[0]

    def _setAppIcon(self):
        path = self._iconPath()
        if os.path.isfile(path):
            self.setWindowIcon(QIcon(path))

    def _buildToolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

        titleIcon = QLabel()
        icon_path = self._iconPath()
        if os.path.isfile(icon_path):
            titleIcon.setPixmap(QPixmap(icon_path).scaled(28, 28, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        titleIcon.setObjectName("titleIcon")
        toolbar.addWidget(titleIcon)

        titleLabel = QLabel("mark_chini")
        titleLabel.setObjectName("titleLabel")
        toolbar.addWidget(titleLabel)

        toolbar.addSeparator()

        self._openBtn = QPushButton("Open")
        self._openBtn.setObjectName("openBtn")
        toolbar.addWidget(self._openBtn)

        self._saveBtn = QPushButton("Save")
        self._saveBtn.setObjectName("saveBtn")
        toolbar.addWidget(self._saveBtn)

        self._exportBtn = QPushButton("Export PDF")
        self._exportBtn.setObjectName("exportBtn")
        toolbar.addWidget(self._exportBtn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setObjectName("toolbarSeparator")
        sep.setFixedWidth(1)
        sep.setStyleSheet("margin: 4px 4px;")
        toolbar.addWidget(sep)

        self._themeBtn = QPushButton()
        self._themeBtn.setObjectName("themeBtn")
        self._themeBtn.setCheckable(True)
        self._themeBtn.setChecked(True)
        self._themeBtn.setText("\u263E")
        self._themeBtn.setToolTip("Toggle dark/light mode")
        toolbar.addWidget(self._themeBtn)

        self._galleryBtn = QPushButton()
        self._galleryBtn.setObjectName("galleryBtn")
        self._galleryBtn.setText("\U0001F5BC")
        self._galleryBtn.setToolTip("Insert image")
        toolbar.addWidget(self._galleryBtn)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        toolbar.addWidget(spacer)

        fontLabel = QLabel("Font")
        fontLabel.setObjectName("labelDim")
        toolbar.addWidget(fontLabel)

        self._fontCombo = QComboBox()
        self._fontCombo.addItems(["Serif", "Sans-Serif", "Monospace"])
        self._fontCombo.setCurrentText("Serif")
        toolbar.addWidget(self._fontCombo)

        sizeLabel = QLabel("Size")
        sizeLabel.setObjectName("labelDim")
        toolbar.addWidget(sizeLabel)

        self._sizeCombo = QComboBox()
        self._sizeCombo.addItems(["Small", "Medium", "Large"])
        self._sizeCombo.setCurrentText("Medium")
        toolbar.addWidget(self._sizeCombo)

        marginLabel = QLabel("Margin")
        marginLabel.setObjectName("labelDim")
        toolbar.addWidget(marginLabel)

        self._marginCombo = QComboBox()
        self._marginCombo.addItems(["Small", "Medium", "Large"])
        self._marginCombo.setCurrentText("Medium")
        toolbar.addWidget(self._marginCombo)

    def _buildCentralArea(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setHandleWidth(3)
        self._splitter.setChildrenCollapsible(False)

        self._editor = MarkdownEditor()
        self._preview = PreviewPanel()

        self._splitter.addWidget(self._editor)
        self._splitter.addWidget(self._preview)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 1)

        layout.addWidget(self._splitter)

    def _buildStatusBar(self):
        self._statusBar = QStatusBar()
        self.setStatusBar(self._statusBar)

        self._fileStatusLabel = QLabel("No file open")
        self._fileStatusLabel.setObjectName("statusLabel")
        self._statusBar.addWidget(self._fileStatusLabel)

        self._wordCountLabel = QLabel("0 words")
        self._wordCountLabel.setObjectName("statusLabel")
        self._statusBar.addPermanentWidget(self._wordCountLabel)

    def _connectSignals(self):
        self._openBtn.clicked.connect(self._onOpen)
        self._saveBtn.clicked.connect(self._onSave)
        self._exportBtn.clicked.connect(self._onExportPdf)
        self._themeBtn.toggled.connect(self._onToggleTheme)
        self._galleryBtn.clicked.connect(self._onInsertImage)

        self._fontCombo.currentTextChanged.connect(self._onSettingChanged)
        self._sizeCombo.currentTextChanged.connect(self._onSettingChanged)
        self._marginCombo.currentTextChanged.connect(self._onSettingChanged)

        self._editor.textChanged.connect(self._onEditorChanged)

    def _onEditorChanged(self, text):
        wordCount = len(text.split()) if text.strip() else 0
        self._wordCountLabel.setText(f"{wordCount} words")
        self._previewTimer.start()

    def _onSettingChanged(self):
        if hasattr(self, "_editor") and self._editor.toPlainText().strip():
            self._previewTimer.start()

    def _updatePreview(self):
        text = self._editor.toPlainText()
        fontChoice = self._fontCombo.currentText()
        sizeChoice = self._sizeCombo.currentText()
        marginChoice = self._marginCombo.currentText()
        html = MarkdownConverter.toHtml(text, fontChoice, sizeChoice, marginChoice, self._darkMode)
        self._preview.setHtml(html)

    def _onOpen(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Markdown File", "",
            "Markdown Files (*.md *.markdown *.mdown);;All Files (*.*)",
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            self._editor.setPlainText(content)
            self._currentFile = path
            self._fileStatusLabel.setText(os.path.basename(path))
            self._updatePreview()
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open file:\n{e}")

    def _onSave(self):
        if self._currentFile:
            path = self._currentFile
        else:
            path, _ = QFileDialog.getSaveFileName(
                self, "Save Markdown File", "",
                "Markdown Files (*.md);;All Files (*.*)",
            )
            if not path:
                return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self._editor.toPlainText())
            self._currentFile = path
            self._fileStatusLabel.setText(os.path.basename(path))
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not save file:\n{e}")

    def _onExportPdf(self):
        if not self._editor.toPlainText().strip():
            QMessageBox.information(self, "Info", "Nothing to export. Write some Markdown first.")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Export PDF", "",
            "PDF Files (*.pdf);;All Files (*.*)",
        )
        if not path:
            return

        self._exportBtn.setEnabled(False)
        self._exportBtn.setText("Exporting...")
        self._fileStatusLabel.setText("Exporting PDF...")

        self._pdfWorker = PdfExportWorker(
            self._editor.toPlainText(),
            path,
            self._fontCombo.currentText(),
            self._sizeCombo.currentText(),
            self._marginCombo.currentText(),
        )
        self._pdfWorker.finished.connect(self._onPdfFinished)
        self._pdfWorker.start()

    def _onPdfFinished(self, success, message):
        self._exportBtn.setEnabled(True)
        self._exportBtn.setText("Export PDF")
        if success:
            self._fileStatusLabel.setText(message)
            QMessageBox.information(self, "Export Complete", message)
        else:
            self._fileStatusLabel.setText("Export failed")
            QMessageBox.critical(self, "Export Failed", message)

    def _onToggleTheme(self, checked):
        self._darkMode = checked
        self._applyTheme()
        self._updatePreview()

    def _applyTheme(self):
        self.setStyleSheet(DARK_THEME if self._darkMode else LIGHT_THEME)

    def _onInsertImage(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Image", "",
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.svg);;All Files (*.*)",
        )
        if path:
            mdLink = f"![{os.path.basename(path)}]({path})"
            self._editor.insertTextAtCursor(mdLink)
