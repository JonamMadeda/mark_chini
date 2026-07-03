import os
import re
import subprocess
import tempfile
import textwrap
import markdown


_HP = "\x00H\x00"
_LBR = "\x00LBR\x00"
_RBR = "\x00RBR\x00"


class MarkdownConverter:
    FONT_MAP = {
        "Serif": ("Times New Roman", "Georgia", "serif"),
        "Sans-Serif": ("Arial", "Helvetica", "Segoe UI", "sans-serif"),
        "Monospace": ("Consolas", "Courier New", "monospace"),
    }

    SIZE_MAP = {
        "Small": "11pt",
        "Medium": "12pt",
        "Large": "14pt",
    }

    MARGIN_MAP = {
        "Small": "1.5cm",
        "Medium": "2.5cm",
        "Large": "3.5cm",
    }

    TYPST_CLI = None

    @classmethod
    def findTypstCli(cls):
        if cls.TYPST_CLI:
            return cls.TYPST_CLI
        base = os.path.dirname(os.path.abspath(__file__))
        try:
            import sys
            if getattr(sys, 'frozen', False):
                base = sys._MEIPASS
        except Exception:
            pass
        candidates = [
            os.path.join(base, "typst.exe"),
            os.path.join(os.path.dirname(base), "typst.exe"),
            os.path.join(os.path.dirname(base), "app", "typst.exe"),
        ]
        for path in candidates:
            resolved = os.path.realpath(path)
            if os.path.isfile(resolved):
                cls.TYPST_CLI = resolved
                return resolved
        which = os.popen("where typst 2>nul").read().strip()
        if which and os.path.isfile(which):
            cls.TYPST_CLI = which
            return which
        raise FileNotFoundError(
            "Typst CLI not found. Please install Typst (https://typst.app) "
            "or place typst.exe next to the application."
        )

    @staticmethod
    def _mdToTypst(markdownText):
        text = markdownText
        text = re.sub(r"^(-{3,})\s*$", _HP + r"line(length: 100%)", text, flags=re.MULTILINE)
        text = re.sub(r"\\\*", "\x00ESC\x00", text)
        text = re.sub(r"\*\*\*(.+?)\*\*\*", lambda m: "\x00BI\x00" + m.group(1) + "\x00BI\x00", text)
        text = re.sub(r"\*\*(.+?)\*\*", lambda m: "\x00B\x00" + m.group(1) + "\x00B\x00", text)
        text = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*", lambda m: "\x00I\x00" + m.group(1) + "\x00I\x00", text)
        text = text.replace("\x00B\x00", "*")
        text = text.replace("\x00I\x00", "_")

        def restore_bi(m):
            return "_*" + m.group(1) + "*_"
        text = re.sub("\x00BI\x00(.+?)\x00BI\x00", restore_bi, text)
        text = text.replace("\x00BI\x00", "")
        text = text.replace("\x00ESC\x00", "*")
        text = re.sub(r"~~~(.+?)~~~", lambda m: _HP + "strike" + _LBR + m.group(1) + _RBR, text)
        text = re.sub(r"~~(.+?)~~", lambda m: _HP + "strike" + _LBR + m.group(1) + _RBR, text)
        text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", _HP + r'image("\2", alt: "\1")', text)
        text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m: _HP + f'link("{m.group(2)}")' + _LBR + m.group(1) + _RBR, text)
        text = re.sub(r"^(\d+)\. ", r"+ ", text, flags=re.MULTILINE)
        text = re.sub(
            r"^([ ]{0,3})>\s?(.*)",
            lambda m: f"{m.group(1)}{_HP}quote{_LBR}{m.group(2)}{_RBR}",
            text, flags=re.MULTILINE,
        )
        lines = []
        for line in text.split("\n"):
            stripped = line.lstrip()
            if stripped.startswith("###### "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}====== {stripped[7:]}")
            elif stripped.startswith("##### "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}===== {stripped[6:]}")
            elif stripped.startswith("#### "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}==== {stripped[5:]}")
            elif stripped.startswith("### "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}=== {stripped[4:]}")
            elif stripped.startswith("## "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}== {stripped[3:]}")
            elif stripped.startswith("# "):
                indent = line[: len(line) - len(stripped)]
                lines.append(f"{indent}= {stripped[2:]}")
            else:
                lines.append(line)
        text = "\n".join(lines)
        text = re.sub(r"(?<!\\)#", r"\\#", text)
        return text

    @staticmethod
    def _sanitizeTypst(text):
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = textwrap.dedent(text)
        text = text.replace("\\#", "\x00P_HASH\x00")
        text = text.replace("\u2014", "---")
        text = text.replace("\u2013", "--")
        text = text.replace("\\", "\\\\")
        text = text.replace("$", "\\$")
        text = text.replace("{", "\\{")
        text = text.replace("}", "\\}")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace("\x00P_HASH\x00", "\\#")
        text = text.replace(_HP, "#")
        text = text.replace(_LBR, "[")
        text = text.replace(_RBR, "]")
        text = text.rstrip() + "\n"
        return text

    @staticmethod
    def toTypstSource(markdownText, fontChoice="Sans-Serif", sizeChoice="Medium", marginChoice="Medium"):
        fonts = MarkdownConverter.FONT_MAP.get(fontChoice, MarkdownConverter.FONT_MAP["Sans-Serif"])
        font_list = ", ".join(f'"{f}"' for f in fonts)
        body = MarkdownConverter._mdToTypst(markdownText)
        body = MarkdownConverter._sanitizeTypst(body)
        return f"""#set page(
  paper: "a4",
  margin: (top: 2.5cm, bottom: 2.5cm, left: 3cm, right: 3cm),
  footer: context {{
    let pagenumber = counter(page).get().first()
    align(center, text(9pt, fill: gray)[#pagenumber])
  }}
)
#set text(font: ({font_list}), size: 11pt)
#set par(justify: true, leading: 0.8em, spacing: 2em)

#show heading.where(level: 1): it => text(size: 1.6em, weight: "bold", fill: rgb("#111111"))[#it.body]

#show heading.where(level: 2): set text(size: 1.3em, weight: "bold", fill: rgb("#333333"))

{body}
"""

    @staticmethod
    def toHtml(markdownText, fontChoice="Sans-Serif", sizeChoice="Medium", marginChoice="Medium", darkMode=False):
        md = markdown.markdown(
            markdownText,
            extensions=["extra", "tables", "fenced_code", "sane_lists"],
        )
        if darkMode:
            bg, fg, hc, bc, cc, cb, lnk, bq_b, bq_c = (
                "#0b0f19", "#f8fafc", "#F87171", "#1e293b",
                "#94a3b8", "#111827", "#EF4444", "#DC2626", "#94a3b8",
            )
        else:
            bg, fg, hc, bc, cc, cb, lnk, bq_b, bq_c = (
                "#ffffff", "#0f172a", "#DC2626", "#e2e8f0",
                "#475569", "#f1f5f9", "#DC2626", "#DC2626", "#475569",
            )
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<style>
body {{
    font-family: 'Segoe UI', 'Inter', 'Arial', sans-serif;
    font-size: 14px; line-height: 1.7;
    color: {fg}; background: {bg};
    padding: 16px; margin: 0;
}}
h1 {{ font-size: 26px; color: {hc}; border-bottom: 2px solid {bc}; padding-bottom: 8px; font-weight: 700; }}
h2 {{ font-size: 22px; color: {hc}; border-bottom: 1px solid {bc}; padding-bottom: 4px; font-weight: 600; }}
h3 {{ font-size: 18px; color: {hc}; font-weight: 600; }}
code {{ font-family: 'Consolas', 'Fira Code', monospace; background: {cb}; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: {fg}; }}
pre {{ background: {cb}; padding: 14px; border-radius: 6px; overflow-x: auto; border: 1px solid {bc}; }}
blockquote {{ border-left: 4px solid {bq_b}; margin: 12px 0; padding: 4px 16px; color: {bq_c}; }}
a {{ color: {lnk}; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid {bc}; padding: 8px 12px; text-align: left; }}
th {{ background: {cb}; font-weight: 600; }}
</style>
</head>
<body>
{md}
</body>
</html>"""

    @staticmethod
    def toPdf(markdownText, outputPath, fontChoice="Sans-Serif", sizeChoice="Medium", marginChoice="Medium"):
        typstSource = MarkdownConverter.toTypstSource(markdownText, fontChoice, sizeChoice, marginChoice)
        cli = MarkdownConverter.findTypstCli()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".typ", delete=False, encoding="utf-8") as f:
            f.write(typstSource)
            typPath = f.name
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            result = subprocess.run(
                [cli, "compile", typPath, outputPath],
                capture_output=True, text=True, timeout=60,
                startupinfo=startupinfo,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Typst compilation failed:\n{result.stderr}")
        finally:
            try:
                os.unlink(typPath)
            except OSError:
                pass
