"""Generate the synthetic Foxit-style evidence record used by the offline demo."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "synthetic-safety-evidence-record.pdf"
TEAL = colors.HexColor("#0B6E77")
INK = colors.HexColor("#0F1A21")
MUTED = colors.HexColor("#64777F")
RULE = colors.HexColor("#D5DEE2")
WASH = colors.HexColor("#EDF2F4")


def footer(canvas, document) -> None:
    canvas.saveState()
    canvas.setStrokeColor(RULE)
    canvas.line(0.7 * inch, 0.55 * inch, 7.8 * inch, 0.55 * inch)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(0.7 * inch, 0.35 * inch, "SYNTHETIC HACKATHON DATA - NOT FOR CLINICAL USE")
    canvas.drawRightString(7.8 * inch, 0.35 * inch, f"Page {document.page}")
    canvas.restoreState()


def build(output: Path = OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Eyebrow", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8, leading=11, textColor=TEAL, spaceAfter=8))
    styles.add(ParagraphStyle(name="TitleLarge", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=28, leading=32, textColor=INK, alignment=TA_CENTER, spaceAfter=14))
    styles.add(ParagraphStyle(name="Lead", parent=styles["BodyText"], fontSize=11, leading=17, textColor=MUTED, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name="SectionTitle", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=17, leading=21, textColor=INK, spaceBefore=6, spaceAfter=12))
    styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontSize=9, leading=14, textColor=INK))
    styles.add(ParagraphStyle(name="Mono", parent=styles["BodyText"], fontName="Courier", fontSize=7.5, leading=11, textColor=INK, wordWrap="CJK"))
    styles.add(ParagraphStyle(name="Boundary", parent=styles["BodyText"], fontSize=9, leading=14, textColor=INK, borderColor=RULE, borderWidth=1, borderPadding=12, backColor=WASH))

    doc = SimpleDocTemplate(str(output), pagesize=letter, rightMargin=0.7 * inch, leftMargin=0.7 * inch, topMargin=0.65 * inch, bottomMargin=0.75 * inch, title="Synthetic Time-Out Safety Evidence Record", author="Time-Out synthetic demonstration", invariant=1)
    story = [
        Spacer(1, 0.55 * inch),
        Paragraph("Time-Out / EVIDENCE RECORD", styles["Eyebrow"]),
        Paragraph("Pre-procedure safety evidence record", styles["TitleLarge"]),
        Paragraph("Encounter SYN-ENC-BLOCKED-002 / Texas / neurotoxin / 20 Aug 2026", styles["Lead"]),
    ]
    summary = [
        # True before and after signing. "AWAITING HUMAN ATTESTATION" stopped
        # being true the moment a Medical Director signed page 3, and eSign
        # overlays a signature rather than rewriting the body, so the signed copy
        # carried a first page that contradicted its own signature page.
        ["Record status", "ASSEMBLED BY AGENT / SEE PAGE 3 FOR ATTESTATION"],
        ["Gate verdict", "CLEAR after documented remediation"],
        ["Determination scope", "Pre-procedure safety determination for human review"],
        ["Patient", "SYN-PATIENT-001 / fictional"],
        ["Performer", "SYN-PROV-RN-002 / documented delegated pathway"],
    ]
    table = Table(summary, colWidths=[1.55 * inch, 5.05 * inch], hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), WASH), ("TEXTCOLOR", (0, 0), (-1, -1), INK),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTNAME", (1, 0), (1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 8), ("LEADING", (0, 0), (-1, -1), 12),
        ("GRID", (0, 0), (-1, -1), 0.5, RULE), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
    ]))
    story.extend([table, Spacer(1, 24), Paragraph("Human-signature boundary", styles["SectionTitle"]), Paragraph("The assembly agent completed reversible document composition and stopped. A Medical Director must review this record and complete the attestation through a human eSign action.", styles["Boundary"]), Spacer(1, 16), Paragraph("This record is synthetic. It contains no real patient, clinic, licence, lot, or signature.", styles["BodySmall"]), PageBreak()])

    story.extend([Paragraph("GATE / SEVEN INDEPENDENT FINDINGS", styles["Eyebrow"]), Paragraph("Deterministic decision after remediation", styles["SectionTitle"])])
    checks = [
        ["Check ID", "Status", "Recorded fact"],
        ["provider_license", "PASS", "TX / ACTIVE / unexpired / HIGH confidence"],
        ["authority_pathway", "PASS", "Delegated-performer training documented"],
        ["delegation_and_supervision", "PASS", "Order, protocol, BLS, and availability documented"],
        ["preprocedure_assessment", "PASS", "Relationship, record, and performer disclosure present"],
        ["product_lot", "PASS", "Lot captured; no captured alert; not authenticity certification"],
        ["comprehension", "PASS", "Teach-back 2/2 on attempt 2; HIGH confidence"],
        ["disciplinary_status", "PASS", "Captured status CLEAR"],
    ]
    checks_table = Table(checks, colWidths=[1.85 * inch, 0.65 * inch, 4.1 * inch], repeatRows=1)
    checks_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), TEAL), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (0, 1), (1, -1), "Courier"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5), ("LEADING", (0, 0), (-1, -1), 11),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, WASH]), ("GRID", (0, 0), (-1, -1), 0.5, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.extend([checks_table, Spacer(1, 24), Paragraph("Frozen rule snapshot", styles["SectionTitle"]), Paragraph("447e16e6986870fd7ccf59a13e76d7c01cb8458019bf8f2567398290ace58cf4", styles["Mono"]), Spacer(1, 14), Paragraph("The exact canonical rule JSON is stored with the Gate decision. Reproduction reruns the same evidence against that snapshot and compares the complete deterministic payload.", styles["BodySmall"]), PageBreak()])

    story.extend([Paragraph("SOURCES / BOUNDED ATTESTATION", styles["Eyebrow"]), Paragraph("Primary sources and record limits", styles["SectionTitle"])])
    sources = [
        "22 TAC Chapter 169 - Texas Register, adopted rules, 9 Jan 2025",
        "Texas Occupations Code Chapter 157 - delegation authority",
        "Texas Board of Nursing cosmetic-procedure practice guidance",
        "FDA Warning Letter 723267 - 1 Apr 2026",
        "AHRQ informed-choice and teach-back guidance",
    ]
    for source in sources:
        story.extend([Paragraph(f"- {source}", styles["BodySmall"]), Spacer(1, 4)])
    story.extend([Spacer(1, 18), Paragraph("Bounded receipt language", styles["SectionTitle"]), Paragraph("This record proves which checks, evidence, sources, and rule snapshot were captured before the procedure. It does not certify legality, safety, product authenticity, provider quality, or outcome.", styles["Boundary"]), Spacer(1, 30)])
    signature = Table([["MEDICAL DIRECTOR ATTESTATION", ""], ["Status", "NOT ATTESTED UNLESS SIGNED BELOW"], ["Synthetic attestation ID", "SYN-ATTEST-SYN-ENC-BLOCKED-002"], ["Signature", "________________________________"]], colWidths=[2.15 * inch, 4.45 * inch])
    signature.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, RULE), ("BACKGROUND", (0, 0), (-1, 0), WASH), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTNAME", (1, 1), (1, -1), "Courier"), ("FONTSIZE", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10)]))
    story.append(signature)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    return output


def main() -> None:
    print(build())


if __name__ == "__main__":
    main()
