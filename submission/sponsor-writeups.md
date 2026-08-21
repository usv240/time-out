# Sponsor submission drafts

Replace `[LIVE URL]`, `[REPO URL]`, and `[VIDEO URL]` only after they work. These
drafts deliberately distinguish the passing offline reference from unactivated live calls.

## Xano

Xano is the intended production system for BEFORE's state machine, approval gates,
append-only decisions, audit trail, auth, and REST API. We replaced the paper-and-PDF
pre-procedure checklist clinics keep in binders with a cited, reproducible encounter
hold reviewed before production. Claude Code and Codex helped implement and test the
reference contract; deployment remains pending Xano workspace activation.

## SerpApi

SerpApi supplies FDA and Texas-board alert candidates that can move a prepared
encounter back to human review. The boundary is explicit: search changes workflow,
but never confirms authenticity, discipline, or law. A named Medical Director
confirms or dismisses every candidate, and the decision is audited.

## Perfect Corp

Perfect Corp YouCam provides an SD standardized skin baseline with fourteen concern
outputs and a VTO expectation-setting aid. BEFORE uses this as documentation and
communication support, never diagnosis or medical-results interpretation. Production
activation remains subject to written confirmation of this framing and required consent.

## name.com

name.com CORE sandbox covers domain search, availability, sandbox registration, TXT
creation, and API read-back of the receipt hash. Sandbox DNS does not propagate to
public resolvers, and the owner can mutate the record; it is a verification channel,
not an immutable notary.

## Nutrient

Nutrient DWS makes extraction deterministic, auditable, and human-in-the-loop:
credential, intake, and product fields carry confidence and page coordinates. A
low-confidence required lot field routes to the Medical Director before the encounter
can advance. The open-source reference implementation includes semantic redaction
before egress.

## Doctavian

Doctavian branches on procedure, authority pathway, and verified patient flags; loops
over cited disclosures; and calculates only the non-clinical disclosure count. Patient
and injector sign the treatment consent. No uncited cooling-off period or clinical dose
enters the document, and Medical Director attestation remains outside this document.

## Foxit

The Foxit agent starts from “assemble the safety record for encounter X,” performs
reversible assembly, generates the evidence PDF, and stops at the irreversible boundary.
A Medical Director then completes the separate human eSign attestation. The verified
offline artifact is `output/pdf/synthetic-safety-evidence-record.pdf`.

Links for every submission: [LIVE URL] / [REPO URL] / [VIDEO URL]
