# Time-Out

Time-Out is a pre-procedure safety proof for cosmetic treatment. The current hero
path is deliberately narrow: **Texas + neurotoxin + synthetic data only**.

The Phase 1 Gate is a pure, offline Python function. It evaluates seven evidence
groups, returns `CLEAR`, `BLOCKED`, or `REVIEW`, preserves every finding and its
source, and freezes the exact rule JSON with a SHA-256 digest. Its output is a
pre-procedure safety determination for human review, not a legal opinion.

## Run locally

Python 3.11+ is sufficient; Phase 1 has no third-party dependencies.

```bash
python -m unittest discover -s tests -v
python -m before.gate_demo
```

The demo runs three committed scenarios: a fully documented RN path, an
aesthetician encounter missing delegation evidence, and a low-confidence product
document routed to review. All people, organizations, licences, lots, and records
under `fixtures/` are visibly fictional.

## Structure

- `before/` — clinic app and patient view (currently the offline Gate demo)
- `shared/gate/` — typed, deterministic Gate
- `fixtures/` — synthetic corpus and source-backed Texas rule snapshot
- `research/` — primary-source rule notes and competitive audit
- `tasks/` — implementation briefs and completion notes

Copy `.env.example` to `.env` only when external integrations begin. Never commit
credentials. Phase 1 makes no external calls and needs no environment variables.

## Run the complete synthetic product

The local reference backend mirrors the intended Xano contract and executes the
complete hero workflow with cached sponsor responses:

```bash
python -m before.seed
python -m before.app.server --offline
```

Open `http://localhost:4173/`. Public routes include `/try`, `/api`, `/evidence`,
`/how-it-works`, and `/receipt/:id`.

One-command verification:

```bash
python -m before.verify
python -m unittest discover -s tests -v
```

The offline hero path blocks missing authority evidence, accepts documented human
remediation, routes low-confidence extraction, records a failed and remediated
teach-back attempt, captures a synthetic SD baseline, pauses the document agent
before Medical Director eSign, reopens a ready encounter for an alert candidate,
and seals plus verifies a bounded receipt.

## Activation status

- **Working locally:** Gate, state machine, audit log, API, public routes, cached
  Nutrient/SerpApi/Doctavian/Perfect Corp/Foxit/name.com adapters, receipt, PDF
  evidence record, sandbox keys, signed webhook outbox, and rule-review workflow.
- **External activation required:** Xano workspace push/static hosting and live
  vendor calls. No `.env` is currently configured and the Xano CLI is unavailable.
- **Synthetic only:** never submit real patient, clinic, licence, lot, face, or
  document data. The API rejects common real-data patterns.
