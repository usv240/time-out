# Phase 2 — BEFORE core (Aug 20–28)

Read `AGENTS.md` first. Phase 1 must be done. Both builders on this.

## Goal
The hero path runs end to end, offline, by **Aug 28**. Ugly is fine.

## The hero path
Texas · neurotoxin · one synthetic encounter.
Booked with aesthetician → **BLOCKED** → reassigned to qualified RN → documents
extracted (one goes to human review) → live alert check → consent compiled →
patient comprehension check → skin baseline → evidence record assembled →
medical director attests → patient scans QR and verifies.

## Tasks in order

### Aug 20–21 · Xano backend
Encounter state machine, approvals, audit events. Every transition writes an
`AuditEvent`. This is the spine — make it visible in the demo.

### Aug 21–22 · Gate wired
`POST /encounters/:id/evaluate` → persist `GateDecision` with frozen snapshot.
UI shows the three-state verdict, failed facts, citation, and remedy.

### Aug 22–23 · Nutrient DWS
- Data Extraction on credential / intake / product documents → typed fields,
  confidence, page coordinates
- **Low confidence routes to the DWS Viewer for human sign-off.** That routing is
  the point, not a nice-to-have. It must fire on the demo path.
- Semantic redaction of PHI before anything leaves the vault
- Product lot number → `ProductLot`

### Aug 23–24 · SerpApi
Detect fresh FDA warning letters and state board actions. A new alert can put an
encounter or a lot **on hold** — moving the verdict to `REVIEW`.

**Hard boundary: SerpApi never decides the law.** It proposes a rule change or
raises a hold; a human confirms. Cache everything to `.cache/serpapi/`; implement
`--offline`.

### Aug 24–25 · Doctavian
One template branching on `procedure × credential × patient_flags`, looping over
required risk disclosures, calculating dosing limits and cooling-off periods.
Collects **treatment-party signatures**: patient + injector.
(Doctavian signs the consent. Foxit handles the director attestation — do not overlap.)

### Aug 25–26 · Comprehension gate  ⭐ the differentiator
Short interactive teach-back before consent counts: risks, alternatives, expected
outcome. Patient answers in their own words or via visual selection — not a checkbox.
Failing items are re-explained and re-asked. Record to `Comprehension`.

**No passing comprehension record → no safety receipt.** Backed by systematic-review
evidence that interactive consent beats written consent for understanding.

### Aug 26–27 · Perfect Corp
JS Camera Kit for consistent capture geometry → Skin Analysis **SD** (14 concerns,
0–100, overlay) → `SkinBaseline`. VTO for expectation-setting during consent.
Stay inside 1,000 units; cache every response. **No image-to-video — cut.**

### Aug 27–28 · Foxit  (rewritten to match their published brief)
Their challenge: *an agent that starts from a plain prompt and ends with a signed
document*, using the **MCP server + PDF Services API**, with an explicit handoff to
human signing.

Build: agent takes a prompt ("assemble the safety record for encounter X"), performs
reversible document assembly through MCP, then **stops** and routes the medical
director's final attestation through direct eSign. The pause at the irreversible
boundary is the story.

## Done when
- [ ] Full hero path runs offline from cache
- [ ] A document routes to human review on the demo path
- [ ] A live alert visibly moves an encounter to REVIEW
- [ ] Comprehension failure blocks the receipt
- [ ] Medical director attestation is a human action, not automated
