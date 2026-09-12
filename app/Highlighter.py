from PyQt6.QtCore import QRegularExpression
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QFont, QColor


# Syntax colors per theme. Every foreground must keep >= 4.5:1 contrast
# against its editor background (dark: #0b0f19, light: #ffffff), except the
# horizontal rule which is decorative (needs >= 3:1 so it stays visible).
DARK_PALETTE = {
    "h1": "#818cf8",
    "h2": "#a78bfa",
    "h3": "#c4b5fd",
    "h4": "#93c5fd",
    "h5": "#93c5fd",
    "h6": "#93c5fd",
    "emphasis": "#f8fafc",
    "code_fg": "#7dd3fc",
    "code_bg": "#1e293b",
    "block_fg": "#7dd3fc",
    "block_bg": "#0f172a",
    "fence_fg": "#79c0ff",
    "fence_bg": "#161b22",
    "link": "#818cf8",
    "image": "#94a3b8",
    "list": "#FBBF24",
    "quote": "#94a3b8",
    "hr": "#64748b",
    "strike": "#94a3b8",
}

LIGHT_PALETTE = {
    "h1": "#3730A3",
    "h2": "#5B21B6",
    "h3": "#6D28D9",
    "h4": "#1D4ED8",
    "h5": "#075985",
    "h6": "#075985",
    "emphasis": "#0f172a",
    "code_fg": "#1E40AF",
    "code_bg": "#DBEAFE",
    "block_fg": "#1E293B",
    "block_bg": "#F1F5F9",
    "fence_fg": "#1E293B",
    "fence_bg": "#E2E8F0",
    "link": "#1D4ED8",
    "image": "#475569",
    "list": "#B45309",
    "quote": "#475569",
    "hr": "#64748b",
    "strike": "#64748b",
}


class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None, darkMode=True):
        super().__init__(parent)
        self._darkMode = darkMode
        self._rules = []
        self._setupRules()

    def setDarkMode(self, darkMode):
        if darkMode != self._darkMode:
            self._darkMode = darkMode
            self._setupRules()
            self.rehighlight()

    def _palette(self):
        return DARK_PALETTE if self._darkMode else LIGHT_PALETTE

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
        pal = self._palette()
        self._rules = []
        headingColors = {
            1: pal["h1"], 2: pal["h2"], 3: pal["h3"],
            4: pal["h4"], 5: pal["h5"], 6: pal["h6"],
        }
        for level in range(1, 7):
            pattern = QRegularExpression(
                f"^[ ]{{0,3}}\\#{{{level}}}(?!\\#).*$",
                QRegularExpression.PatternOption.MultilineOption,
            )
            fmt = self._makeFormat(headingColors[level], bold=True, sizeDelta=6 - level)
            self._rules.append((pattern, fmt))

        boldItalic = QRegularExpression(r"(\*{3}|_{3})([^\*_]+?)\1")
        fmtBI = self._makeFormat(pal["emphasis"], bold=True, italic=True)
        self._rules.append((boldItalic, fmtBI))

        boldPat = QRegularExpression(r"(\*{2}|_{2})([^\*_]+?)\1")
        fmtB = self._makeFormat(pal["emphasis"], bold=True)
        self._rules.append((boldPat, fmtB))

        italicPat = QRegularExpression(r"(?<!\*)(\*|_)(?!\*)([^\*_\s][^\*_]*?)\1(?!\*)")
        fmtI = self._makeFormat(pal["emphasis"], italic=True)
        self._rules.append((italicPat, fmtI))

        inlineCode = QRegularExpression(r"(`+)([^`]+?)\1")
        fmtCode = QTextCharFormat()
        fmtCode.setForeground(QColor(pal["code_fg"]))
        fmtCode.setFontFamilies(["Consolas", "Fira Code", "Cascadia Code", "monospace"])
        fmtCode.setBackground(QColor(pal["code_bg"]))
        self._rules.append((inlineCode, fmtCode))

        linkPat = QRegularExpression(r"\[([^\]]+)\]\(([^)]+)\)")
        fmtLink = self._makeFormat(pal["link"])
        fmtLink.setFontUnderline(True)
        self._rules.append((linkPat, fmtLink))

        imgPat = QRegularExpression(r"!\[([^\]]*)\]\(([^)]+)\)")
        fmtImg = self._makeFormat(pal["image"])
        fmtImg.setFontUnderline(True)
        self._rules.append((imgPat, fmtImg))

        ulPat = QRegularExpression(
            r"^[ ]{0,3}[-*+][ ].*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtUl = self._makeFormat(pal["list"])
        self._rules.append((ulPat, fmtUl))

        olPat = QRegularExpression(
            r"^[ ]{0,3}\d+\.[ ].*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtOl = self._makeFormat(pal["list"])
        self._rules.append((olPat, fmtOl))

        quotePat = QRegularExpression(
            r"^[ ]{0,3}>.*$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtQuote = self._makeFormat(pal["quote"], italic=True)
        self._rules.append((quotePat, fmtQuote))

        hrPat = QRegularExpression(
            r"^[ ]{0,3}([-*_])[ ]*(\1[ ]*){2,}$",
            QRegularExpression.PatternOption.MultilineOption,
        )
        fmtHr = self._makeFormat(pal["hr"])
        self._rules.append((hrPat, fmtHr))

        strikePat = QRegularExpression(r"~~([^~]+?)~~")
        fmtStrike = self._makeFormat(pal["strike"])
        fmtStrike.setFontStrikeOut(True)
        self._rules.append((strikePat, fmtStrike))

    def highlightBlock(self, text):
        pal = self._palette()
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
            fmt.setForeground(QColor(pal["block_fg"]))
            fmt.setBackground(QColor(pal["block_bg"]))
            self.setFormat(0, len(text), fmt)
            return
        else:
            startMatch = cbStart.match(text)
            if startMatch.hasMatch():
                self.setCurrentBlockState(1)
                fmt = QTextCharFormat()
                fmt.setForeground(QColor(pal["fence_fg"]))
                fmt.setBackground(QColor(pal["fence_bg"]))
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
