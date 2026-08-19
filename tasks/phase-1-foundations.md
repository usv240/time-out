# Phase 1 — Foundations (Aug 17–19)

Read `AGENTS.md` first. Do not read `PLAN.md` for instructions.

## Goal
A running skeleton with a seeded rules table and a synthetic corpus. No sponsor
integrations yet beyond Xano. By the end of this phase the Gate must return a
verdict for a hardcoded encounter.

## Tasks

### 1. Repo structure
```
/baseline      clinic + patient app
/recon         expense app (Builder B, starts Aug 27)
/shared        rules engine, types, API clients
/fixtures      synthetic corpus (committed)
/bruno         .bru collections
/tasks         these briefs
```

### 2. Xano data model
Create tables exactly as specified in PLAN.md §1.5. Entities:
`Clinic · Provider · Procedure · JurisdictionRule · Encounter · GateDecision ·
IntakeDoc · SkinBaseline · ConsentRecord · EvidenceBundle · AuditEvent · ProductLot`

Enable CLI push in workspace settings first. Use the Xano CLI + MCP.

### 3. Seed JurisdictionRule — 4 states only
TX, CA, NY, FL × procedure categories
`NEUROTOXIN · FILLER · LASER · IPL · PEEL · MICRONEEDLING · IV · GLP1`

Each row needs: `permitted_credentials[]`, `supervision_model`
(NONE|GENERAL|DIRECT|ONSITE), `requires_delegation_doc`, `requires_medical_director`,
`citation_url`, `source`, `verified_at`.

Seed from public state board sources. Where a rule is uncertain, mark it and move on —
do not guess silently.

### 4. The Gate (`/shared/gate`)
Pure function, no network, fully unit-tested.

Input: `{ state, procedure_id, provider_id, clinic_id, patient_flags[] }`

Evaluate in order, collecting **all** failures (do not short-circuit):
1. Provider licence active + unexpired in `state`
2. Credential ∈ `permitted_credentials`
3. Supervision model satisfied
4. QUAD A tier requirements met
5. Good-faith exam recorded where required
6. Product lot not FDA-flagged
7. Board disciplinary status clear

Output must match the contract in PLAN.md §1.6, including a frozen `rule_snapshot`.

### 5. Synthetic corpus (`/fixtures`)
- 4 fictional clinics, one per state, obviously-fake licence formats
- 6 fictional providers spanning MD, NP, RN, AESTHETICIAN, LASER_TECH — **at least
  two must fail the Gate**
- Synthetic patient faces (generated, never real people)
- 8–10 intake documents: handwritten-style history, typed consent, product packaging
  with invented lot number, prior-treatment record
- **2–3 deliberately low-quality documents** so the human-review path fires on camera

### 6. Housekeeping
- `.env` populated from `.env.example` (do not commit)
- README with setup steps
- CI running unit tests

## Done when
- [ ] `gate.evaluate()` returns CLEAR for a valid encounter and BLOCKED with citations
      for an aesthetician attempting neurotoxin in TX
- [ ] Unit tests cover all 7 checks
- [ ] Corpus committed, all synthetic
- [ ] Clean checkout + `.env` → runs
