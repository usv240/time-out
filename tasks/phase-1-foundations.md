# Phase 1 — Foundations (Aug 17–19)

Read `AGENTS.md` first. Do not read `PLAN.md` for instructions.

## Scope discipline
**Texas only. Neurotoxin only.** One hero path. Everything else is out of scope
until the hero path runs end to end.

## Goal
The Gate returns a three-state verdict for a synthetic encounter, with citations
and a frozen rule snapshot. No sponsor integrations yet beyond Xano.

## Tasks

### 1. Repo structure
```
/before        clinic app + patient receipt view
/shared        rules engine, types, API clients
/fixtures      synthetic corpus (committed)
/tasks         these briefs
```

### 2. Xano data model
`Clinic · Provider · Procedure · JurisdictionRule · Encounter · GateDecision ·
IntakeDoc · SkinBaseline · Comprehension · ConsentRecord · SafetyReceipt ·
AuditEvent · ProductLot`

Enable CLI push in workspace settings first. Use the Xano CLI + MCP.
**Xano must visibly be the system** — state machine, rules, approvals, audit all live here.

### 3. Seed JurisdictionRule — Texas neurotoxin only
Rows need: `permitted_credentials[]`, `supervision_model`
(NONE|GENERAL|DIRECT|ONSITE), `requires_delegation_doc`, `requires_medical_director`,
`requires_good_faith_exam`, `citation_url`, `source`, `verified_at`, `confidence`.

Seed from primary sources: Texas Medical Board, Texas Board of Nursing.
Where a rule is genuinely ambiguous, mark it `REVIEW` — never guess silently.

### 4. The Gate (`/shared/gate`)
Pure function, no network, fully unit-tested.

**Three-state verdict — this matters:**
- `CLEAR` — all checks pass on unambiguous rules
- `BLOCKED` — a check fails on an unambiguous rule
- `REVIEW` — a rule is ambiguous, stale, or the evidence is low-confidence.
  A human decides. **The software never resolves ambiguity by guessing.**

Evaluate in order, collecting **all** findings (do not short-circuit):
1. Provider licence active + unexpired in state
2. Credential ∈ `permitted_credentials`
3. Supervision model satisfied
4. Good-faith exam recorded where required
5. Product lot verifiable and not alerted
6. Patient comprehension recorded and passing
7. Board disciplinary status clear

Every finding carries `citation_url` + the exact facts that failed.
Output freezes `rule_snapshot` so the decision stays explainable years later.

**Language rule:** the Gate produces a *safety determination for human review*.
It never "determines legality." Enforce this in copy, types, and comments.

### 5. Synthetic corpus (`/fixtures`)
- 1 fictional Texas clinic, obviously-fake licence format
- 3 fictional providers: one aesthetician (fails), one RN with delegation (clears),
  one medical director
- Synthetic patient face (generated, never a real person)
- 5–6 intake documents incl. product packaging with an invented lot number
- **1–2 deliberately low-confidence documents** so the review path fires on camera

### 6. Housekeeping
`.env` from `.env.example` · README · CI running unit tests

## Done when
- [ ] Gate returns BLOCKED with citation for aesthetician + neurotoxin in TX
- [ ] Gate returns CLEAR for RN with valid delegation
- [ ] Gate returns REVIEW for a low-confidence or ambiguous input
- [ ] Unit tests cover all 7 checks and all 3 verdicts
- [ ] No copy anywhere claims the software determines legality
