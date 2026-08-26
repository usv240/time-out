"""Build the synthetic product-packaging document used for Nutrient extraction.

The lot line is intentionally low contrast and lightly obscured so a real DWS
parse can demonstrate confidence-based human review. Nothing in this artifact
identifies a real patient, provider, clinic, product, licence, or lot.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "synthetic-product-packaging-low-confidence.pdf"


def build(output: Path = OUTPUT) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    page = canvas.Canvas(str(output), pagesize=letter, invariant=1)
    page.setTitle("Synthetic neurotoxin product packaging")
    page.setAuthor("Time-Out synthetic demonstration")
    width, height = letter

    page.setFillColor(colors.HexColor("#0F1A21"))
    page.setFont("Helvetica-Bold", 24)
    page.drawString(0.8 * inch, height - 1.0 * inch, "EXAMPLETOX")
    page.setFont("Helvetica-Bold", 10)
    page.setFillColor(colors.HexColor("#0B6E77"))
    page.drawString(0.8 * inch, height - 1.25 * inch, "SYNTHETIC PRODUCT - NOT FOR CLINICAL USE")

    page.setStrokeColor(colors.HexColor("#D5DEE2"))
    page.roundRect(0.75 * inch, height - 4.45 * inch, width - 1.5 * inch, 2.75 * inch, 10, stroke=1, fill=0)
    page.setFillColor(colors.HexColor("#0F1A21"))
    page.setFont("Helvetica", 12)
    page.drawString(1.0 * inch, height - 2.15 * inch, "MANUFACTURER: Fictional Therapeutics")
    page.drawString(1.0 * inch, height - 2.55 * inch, "PRODUCT: EXAMPLETOX - NOT A REAL PRODUCT")
    page.drawString(1.0 * inch, height - 3.35 * inch, "EXPIRES: 2027-10-31")

    # Deliberately uncertain OCR target: the value remains readable to a human,
    # but the low contrast and crossing hatch should lower machine confidence.
    page.setFillColor(colors.HexColor("#AEB8BC"))
    page.setFont("Courier", 11)
    page.drawString(1.0 * inch, height - 2.95 * inch, "LOT: INVENTED-LOT-0007")
    page.setStrokeColor(colors.HexColor("#D9DFE2"))
    for offset in (0.00, 0.035, 0.07):
        page.line(0.96 * inch, height - (2.91 + offset) * inch, 3.45 * inch, height - (3.02 + offset) * inch)

    page.setFillColor(colors.HexColor("#64777F"))
    page.setFont("Helvetica", 9)
    page.drawString(0.8 * inch, 0.7 * inch, "Fixture SYN-PACKAGE-001 / Texas neurotoxin hero path")
    page.drawRightString(width - 0.8 * inch, 0.7 * inch, "SYNTHETIC ONLY")
    page.showPage()
    page.save()
    manifest = {
        "schema_version": 1,
        "synthetic": True,
        "contains_real_people_or_businesses": False,
        "contains_prohibited_identifiers": False,
        "artifact_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
        "purpose": "Nutrient DWS low-confidence product-packaging demo",
    }
    output.with_name(output.name + ".synthetic.json").write_text(
        json.dumps(manifest, indent=2) + "\n",
        encoding="utf-8",
    )
    return output


def main() -> None:
    print(build())


if __name__ == "__main__":
    main()
