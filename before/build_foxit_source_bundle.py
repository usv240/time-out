"""Build the deterministic synthetic source bundle consumed by the Foxit MCP agent."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from before.build_evidence_pdf import OUTPUT as REFERENCE_PDF
from before.build_evidence_pdf import build as build_reference_pdf


ROOT = Path(__file__).resolve().parents[1]
SOURCE_DIR = ROOT / "output" / "pdf" / "foxit-source"
MANIFEST = SOURCE_DIR / "manifest.synthetic.json"
AGENT_PROMPT = "assemble the safety record for encounter SYN-ENC-BLOCKED-002"
SECTIONS = (
    ("01-encounter-and-boundary.pdf", "Encounter summary and human-signature boundary", 0),
    ("02-gate-and-rule-snapshot.pdf", "Deterministic Gate and frozen rule snapshot", 1),
    ("03-sources-and-attestation.pdf", "Sources, bounded receipt language, and attestation handoff", 2),
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build() -> Path:
    build_reference_pdf(REFERENCE_PDF)
    reader = PdfReader(str(REFERENCE_PDF))
    if len(reader.pages) != len(SECTIONS):
        raise RuntimeError(f"Expected {len(SECTIONS)} source pages, found {len(reader.pages)}.")
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    documents: list[dict[str, object]] = []
    for filename, title, page_index in SECTIONS:
        path = SOURCE_DIR / filename
        writer = PdfWriter()
        writer.add_page(reader.pages[page_index])
        writer.add_metadata(
            {
                "/Title": title,
                "/Author": "Time-Out synthetic demonstration",
                "/Subject": "Foxit MCP assembly input - synthetic only",
            }
        )
        with path.open("wb") as output:
            writer.write(output)
        documents.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256(path),
                "pages": 1,
                "section": title,
            }
        )
    payload = {
        "schema_version": 1,
        "synthetic": True,
        "contains_real_people_or_businesses": False,
        "contains_prohibited_identifiers": False,
        "agent_prompt": AGENT_PROMPT,
        "source_document": str(REFERENCE_PDF.relative_to(ROOT)).replace("\\", "/"),
        "source_document_sha256": sha256(REFERENCE_PDF),
        "documents": documents,
        "stop_condition": "MCP merge downloaded and awaiting Medical Director eSign handoff",
    }
    MANIFEST.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return MANIFEST


if __name__ == "__main__":
    print(build())
