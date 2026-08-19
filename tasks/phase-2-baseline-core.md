# Phase 2 — Baseline core (Aug 20–26)

Read `AGENTS.md` first. Phase 1 must be done.

## Goal
End-to-end walkthrough working. **Ugly is fine. It must run start to finish by Aug 26.**
That date is a hard checkpoint — if this slips, Recon is cancelled.

## Tasks in order

### Aug 20–21 · Xano backend
Encounters, providers, procedures, consent state machine, audit log, auth.
Every state transition writes an `AuditEvent`.

### Aug 21–22 · Wire the Gate
Expose `POST /encounters/:id/evaluate`. Persist `GateDecision` with frozen snapshot.
UI shows verdict, reasons with citations, and remedies.

### Aug 22–23 · SerpApi
Live state scope-of-practice rules, FDA warnings/counterfeit lot alerts, board actions.
**Cache every response to `.cache/serpapi/`.** Implement `--offline`.
Live results refresh `JurisdictionRule.verified_at`; they never bypass the Gate.

### Aug 23–24 · Nutrient DWS
- Data Extraction on intake docs → typed fields + confidence + page coords
- Confidence below threshold → route to **DWS Viewer** for medical director sign-off
- **Semantic** redaction of PHI before anything leaves the vault
- Extract lot numbers from product packaging → feed `ProductLot`

### Aug 24–25 · Doctavian
One template, branching on `state × procedure_category × quad_a_tier × patient_flags`.
Loops over required risk disclosures. Calculates dosing limits and cooling-off periods.
Then three-signer flow: patient → injector → supervising physician. Sealed audit trail.

### Aug 25–26 · Perfect Corp
- JS **Camera Kit** for consistent capture geometry
- **Skin Analysis (SD)** → 14 concerns scored 0–100 + overlay → `SkinBaseline`
- **VTO** for expectation-setting during consent
- Stay inside the 1,000-unit budget; cache every response

## Done when
- [ ] Book → Gate BLOCKS → reassign → Gate CLEARS → intake parsed → consent generated
      and branching visibly → baseline captured → three signatures → record sealed
- [ ] Whole flow runs offline from cache
- [ ] At least one document routes to human review on the demo path
