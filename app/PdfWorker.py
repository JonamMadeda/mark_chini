from PyQt6.QtCore import QThread, pyqtSignal

from app.Converter import MarkdownConverter


class PdfExportWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, markdownText, outputPath, fontChoice, sizeChoice, marginChoice, parent=None):
        super().__init__(parent)
        self._markdownText = markdownText
        self._outputPath = outputPath
        self._fontChoice = fontChoice
        self._sizeChoice = sizeChoice
        self._marginChoice = marginChoice

    def run(self):
        try:
            self.progress.emit("Rendering PDF with Typst...")
            MarkdownConverter.toPdf(
                self._markdownText,
                self._outputPath,
                self._fontChoice,
                self._sizeChoice,
                self._marginChoice,
            )
            self.finished.emit(True, f"PDF saved to {self._outputPath}")
        except FileNotFoundError as e:
            self.finished.emit(False, f"Typst CLI not found: {e}")
        except RuntimeError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            self.finished.emit(False, f"Export failed: {e}")
