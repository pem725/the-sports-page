#!/usr/bin/env python3
"""Build the Order #3480 annotated proof and one-page production sheet."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Image as RLImage,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "merch" / "previews" / "WHITE ON DARK EMBROIDERY ONE COLOR.jpeg"
OUT_DIR = ROOT / "merch" / "order-3480"
PDF_DIR = ROOT / "output" / "pdf"
ANNOTATED = OUT_DIR / "revised-proof-annotated.png"
ANNOTATED_JPEG = OUT_DIR / "revised-proof-annotated-for-pdf.jpg"
PDF_PATH = PDF_DIR / "order-3480-production-spec.pdf"

NAVY = "#051954"
CREAM = "#f9f2de"
RUST = "#b83a1e"
GREEN = "#18794e"
AMBER = "#9a6700"
INK = "#1a1208"
PAPER = "#f5f0e8"


def font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size=size)
    return ImageFont.load_default()


def rounded_label(draw, box, lines, fill, outline, target, title_color="white"):
    x1, y1, x2, y2 = box
    draw.rounded_rectangle(box, radius=28, fill=fill, outline=outline, width=8)
    title_font = font(58, bold=True)
    body_font = font(48)
    y = y1 + 34
    for idx, line in enumerate(lines):
        draw.text((x1 + 34, y), line, fill=title_color, font=title_font if idx == 0 else body_font)
        y += 72 if idx == 0 else 62
    start = ((x1 + x2) // 2, y2)
    draw.line([start, target], fill=outline, width=16)
    tx, ty = target
    draw.ellipse((tx - 32, ty - 32, tx + 32, ty + 32), outline=outline, width=14)


def build_annotated_image():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    image = ImageOps.exif_transpose(Image.open(SOURCE)).convert("RGBA")
    w, h = image.size
    overlay = Image.new("RGBA", image.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle((0, 0, w, 265), fill=(5, 25, 84, 235))
    draw.text((110, 45), "ORDER #3480 - REVISED DARK-GARMENT SEW-OUT", fill="white", font=font(76, True))
    draw.text((112, 145), "Correct one-color construction; two items still need confirmation", fill=CREAM, font=font(48))

    rounded_label(
        draw,
        (80, 1000, 1160, 1325),
        ["CORRECT", "One cream thread", "for badge and curve"],
        (24, 121, 78, 225),
        GREEN,
        (1250, 1700),
    )
    rounded_label(
        draw,
        (1840, 1680, 2940, 2055),
        ["CORRECT", "Dark fabric shows", "through the halo gap"],
        (24, 121, 78, 225),
        GREEN,
        (1530, 2160),
    )
    rounded_label(
        draw,
        (1780, 2920, 2940, 3320),
        ["CONFIRM", "Domain must read", "THESPORTSPAGE.NET", "with no added spaces"],
        (154, 103, 0, 230),
        AMBER,
        (1510, 2630),
    )

    draw.rounded_rectangle((80, h - 245, w - 80, h - 65), radius=24, fill=(26, 18, 8, 220))
    draw.text(
        (120, h - 207),
        "Still required: matching White-polo sew-out in navy thread, same open-fabric halo, 82 mm wide.",
        fill="white",
        font=font(48, True),
    )

    composed = Image.alpha_composite(image, overlay).convert("RGB")
    composed.save(ANNOTATED, quality=94)
    pdf_image = composed.copy()
    pdf_image.thumbnail((900, 1200))
    pdf_image.save(ANNOTATED_JPEG, quality=84, optimize=True)


def p(text, style):
    return Paragraph(text, style)


def build_pdf():
    PDF_DIR.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        leftMargin=0.42 * inch,
        rightMargin=0.42 * inch,
        topMargin=0.35 * inch,
        bottomMargin=0.34 * inch,
        title="Order #3480 Production Specification",
        author="The Sports Page",
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=16, leading=18, textColor=colors.HexColor(NAVY), alignment=TA_LEFT, spaceAfter=5)
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontName="Helvetica", fontSize=7.8, leading=9.3, textColor=colors.HexColor(INK))
    small_bold = ParagraphStyle("SmallBold", parent=small, fontName="Helvetica-Bold")
    section = ParagraphStyle("Section", parent=small_bold, fontSize=9.2, leading=10.5, textColor=colors.HexColor(NAVY), spaceBefore=4, spaceAfter=2)
    status = ParagraphStyle("Status", parent=small_bold, fontSize=9.5, leading=11.5, alignment=TA_CENTER, textColor=colors.white)

    story = [p("ORDER #3480 - EMBROIDERY PRODUCTION SPECIFICATION", title)]
    story.append(Table([[p("HOLD FOR FINAL CONFIRMATION - revised dark sew-out is correct; White sew-out remains unverified", status)]], colWidths=[7.66 * inch], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(AMBER)),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor(INK)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])))
    story.append(Spacer(1, 6))

    proof = RLImage(str(ANNOTATED_JPEG), width=4.2 * inch, height=5.6 * inch)
    proof.hAlign = "CENTER"
    story.append(proof)
    story.append(Spacer(1, 5))

    left = [
        p("GARMENT AND THREAD MAP", section),
        p("<b>White MM1000 polos:</b> 1 M, 2 L, 2 XL, 1 2XL. Use one navy thread only.", small),
        p("<b>Night Navy MM1000 polos:</b> 1 M, 2 L, 2 XL, 1 2XL. Use one cream thread only.", small),
        p("<b>Total:</b> 12 polos. Left-chest embroidery only; no back decoration.", small),
        p("<b>Artwork:</b> complete badge plus THESPORTSPAGE.NET. No www and no protocol.", small),
        p("<b>Finished width:</b> 82 mm (3.25 inches). Do not shrink below 76 mm.", small),
    ]
    right = [
        p("APPROVAL CHECKLIST", section),
        p("[ ] Same digitized geometry on both garment colors", small),
        p("[ ] One thread color per garment; no second-color outline", small),
        p("[ ] Halo remains unstitched garment fabric", small),
        p("[ ] Domain has no inserted spaces around the period", small),
        p("[ ] Final width confirmed at 82 mm", small),
        p("[ ] Revised White-polo sew-out supplied in navy thread", small),
    ]
    columns = Table([[left, right]], colWidths=[3.78 * inch, 3.78 * inch], style=TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(PAPER)),
        ("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#c8bea8")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#c8bea8")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(KeepTogether(columns))
    story.append(Spacer(1, 5))
    story.append(p("PRODUCTION AUTHORIZATION: Do not begin production until the revised White sew-out and the five construction confirmations above are accepted in writing.", ParagraphStyle("Footer", parent=small_bold, fontSize=8.2, leading=9.8, textColor=colors.HexColor(RUST), alignment=TA_CENTER)))

    doc.build(story)


if __name__ == "__main__":
    build_annotated_image()
    build_pdf()
    print(ANNOTATED)
    print(PDF_PATH)
