from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._rules = []
        self._setupRules()

    def _makeFormat(self, color, bold=False, italic=False, sizeDelta=0):
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        if bold:
            fmt.setFontWeight(QFont.Weight.Bold)
        if italic:
            fmt.setFontItalic(True)
        if sizeDelta:
            fmt.setFontPointSize(self.document().defaultFont().pointSize() + sizeDelta)
        return fmt

    def _setupRules(self):
        headingColors = {
            1: "#818cf8", 2: "#a78bfa", 3: "#c4b5fd",
            4: "#93c5fd", 5: "#93c5fd", 6: "#93c5fd",
        }
        for level in range(1, 7):
            pattern = QRegularExpression(
                f"^[ ]{{0,3}}\\#{{{level}}}(?!\\#).*$",
                QRegularExpression.PatternOption.MultilineOption,
            )
            fmt = self._makeFormat(headingColors[level], bold=True, sizeDelta=6 - level)
            self._rules.append((pattern, fmt))

        boldItalic = QRegularExpression(r"(\*{3}|_{3})([^\*_]+?)\1")
        fmtBI = self._makeFormat("#f8fafc", bold=True, italic=True)
        self._rules.append((boldItalic, fmtBI))

        boldPat = QRegularExpression(r"(\*{2}|_{2})([^\*_]+?)\1")
        fmtB = self._makeFormat("#f8fafc", bold=True)
        self._rules.append((boldPat, fmtB))

        italicPat = QRegularExpression(r"(?<!\*)(\*|_)(?!\*)([^\*_\s][^\*_]*?)\1(?!\*)")
        fmtI = self._makeFormat("#f8fafc", italic=True)
        self._rules.append((italicPat, fmtI))

        inlineCode = QRegularExpression(r"(`+)([^`]+?)\1")
        fmtCode = QTextCharFormat()
        fmtCode.setForeground(QColor("#7dd3fc"))
        fmtCode.setFontFamilies(["Consolas", "Fira Code", "Cascadia Code", "monospace"])
        fmtCode.setBackground(QColor("#1e293b"))
        self._rules.append((inlineCode, fmtCode))

        linkPat = QRegularExpression(r"\[([^\]]+)\]\(([^)]+)\)")
        fmtLink = self._makeFormat("#818cf8")
        fmtLink.setFontUnderline(True)
        self._rules.append((linkPat, fmtLink))

        imgPat = QRegularExpression(r"!\[([^\]]*)\]\(([^)]+)\)")
        fmtImg = self._makeFormat("#94a3b8")
        fmtImg.setFontUnderline(True)
        self._rules.append((imgPat, fmtImg))

        ulPat = QRegularExpression(
            r"^[ ]{0,3}[-*+][ ].*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtUl = self._makeFormat("#34d399")
        self._rules.append((ulPat, fmtUl))

        olPat = QRegularExpression(
            r"^[ ]{0,3}\d+\.[ ].*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtOl = self._makeFormat("#34d399")
        self._rules.append((olPat, fmtOl))

        quotePat = QRegularExpression(
            r"^[ ]{0,3}>.*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtQuote = self._makeFormat("#94a3b8", italic=True)
        self._rules.append((quotePat, fmtQuote))

        hrPat = QRegularExpression(
            r"^[ ]{0,3}([-*_])[ ]*(\1[ ]*){2,}$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtHr = self._makeFormat("#374151")
        self._rules.append((hrPat, fmtHr))

        strikePat = QRegularExpression(r"~~([^~]+?)~~")
        fmtStrike = self._makeFormat("#64748b")
        fmtStrike.setFontStrikeOut(True)
        self._rules.append((strikePat, fmtStrike))

    def highlightBlock(self, text):
        cbStart = QRegularExpression(r"^```")
        cbEnd = QRegularExpression(r"^```")

        prevState = self.previousBlockState()
        inCodeBlock = True if prevState == 1 else False

        if inCodeBlock:
            endMatch = cbEnd.match(text)
            if endMatch.hasMatch():
                self.setCurrentBlockState(0)
            else:
                self.setCurrentBlockState(1)
            fmt = QTextCharFormat()
            fmt.setForeground(QColor("#7dd3fc"))
            fmt.setBackground(QColor("#0f172a"))
            self.setFormat(0, len(text), fmt)
            return
        else:
            startMatch = cbStart.match(text)
            if startMatch.hasMatch():
                self.setCurrentBlockState(1)
                fmt = QTextCharFormat()
                fmt.setForeground(QColor("#79c0ff"))
                fmt.setBackground(QColor("#161b22"))
                self.setFormat(0, len(text), fmt)
                return
            else:
                self.setCurrentBlockState(0)

        for pattern, fmt in self._rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                start = match.capturedStart()
                length = match.capturedLength()
                self.setFormat(start, length, fmt)
