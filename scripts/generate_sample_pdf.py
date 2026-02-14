"""
Generate a sample PDF from a policy Markdown file for the corpus.
Run from project root: python scripts/generate_sample_pdf.py
"""

import re
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


def _sanitize(s: str) -> str:
    """Replace chars that may cause ReportLab issues."""
    s = s.replace("**", "")
    for a, b in [("–", "-"), ("—", "-"), ("'", "'"), ("'", "'"), (""", '"'), (""", '"')]:
        s = s.replace(a, b)
    # Escape XML entities for ReportLab Paragraph
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return s


def md_to_lines(text: str) -> list[tuple[str, str]]:
    """Convert markdown to (line, kind) tuples. kind: 'heading' | 'bullet' | 'numbered' | 'body'."""
    result = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            line = _sanitize(line.lstrip("#").strip())
            result.append((line, "heading"))
        elif re.match(r"^\|[\s\-:|]+\|$", line):
            continue  # Skip table separator lines
        elif line.startswith("|"):
            line = _sanitize(line.replace("|", " ").strip())
            result.append((line, "body"))
        elif line.startswith("- ") or line.startswith("* "):
            line = _sanitize(line[2:])
            result.append((line, "bullet"))
        elif re.match(r"^\d+\.\s", line):
            line = _sanitize(line)
            result.append((line, "numbered"))
        else:
            result.append((_sanitize(line), "body"))
    return result


def main() -> None:
    base = Path(__file__).resolve().parent.parent
    src = base / "data" / "policies" / "expenses_policy.md"
    out = base / "data" / "policies" / "expenses_policy.pdf"
    out_new = base / "data" / "policies" / "expenses_policy_new.pdf"

    text = src.read_text(encoding="utf-8")
    lines = md_to_lines(text)

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=inch * 0.75,
        rightMargin=inch * 0.75,
        topMargin=inch * 0.75,
        bottomMargin=inch * 0.75,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "PolicyTitle",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "PolicyHeading",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=6,
    )
    body_style = ParagraphStyle(
        "PolicyBody",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "PolicyBullet",
        parent=styles["Normal"],
        fontSize=10,
        leftIndent=20,
        spaceAfter=4,
    )

    story = []
    for i, (line, kind) in enumerate(lines):
        if kind == "heading":
            style = title_style if i == 0 else heading_style
            story.append(Paragraph(line, style))
        elif kind == "bullet":
            story.append(Paragraph(f"&bull; {line}", bullet_style))
        else:
            story.append(Paragraph(line, body_style))

    try:
        doc.build(story)
        print(f"Generated {out}")
    except PermissionError:
        doc = SimpleDocTemplate(
            str(out_new), pagesize=A4,
            leftMargin=inch * 0.75, rightMargin=inch * 0.75,
            topMargin=inch * 0.75, bottomMargin=inch * 0.75,
        )
        doc.build(story)
        print(f"Generated {out_new} (close expenses_policy.pdf in your viewer, then run again to replace)")


if __name__ == "__main__":
    main()
