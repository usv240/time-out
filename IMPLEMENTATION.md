# BEFORE implementation status - 21 Aug 2026

## Code-complete reference and live Xano spine

- Deterministic seven-check Gate with `CLEAR` / `BLOCKED` / `REVIEW`
- Current architecture state machine with guarded transitions
- Audit event on every transition and idempotent same-state retry
- Human remediation without direct database editing
- Frozen rule snapshot and byte-identical reproduction
- Named-role review for low-confidence Nutrient extraction
- SerpApi alert candidate and reversible ready state
- Doctavian branch/loop/calculate template contract and two treatment-party signers
- Versioned teach-back failure, re-explanation, retry, and encounter hold
- Perfect Corp SD baseline contract with fourteen concerns and VTO boundary
- Foxit assembly-agent pause, verified three-page PDF, and Medical Director eSign handoff
- Bounded receipt hash, name.com sandbox verification contract, and receipt verification
- HMAC-SHA256 webhook outbox
- Proposed -> human-reviewed -> effective -> snapshotted rule workflow
- Synthetic-only API, common-PHI-pattern rejection, 60 request/minute limit, and instant keys
- Public `/`, `/try`, `/api`, `/evidence`, `/how-it-works`, and `/receipt/:id` routes
- One-command cache seed and one-command verification

## Live Xano deployment

- Production site: `https://before-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io`
- Public API: `https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1`
- Workspace 1 contains 15 BEFORE tables, guarded encounter transitions, immutable audit events, and frozen rule snapshots.
- `POST /v1/encounters/{encounter_id}/evaluate` invokes the deterministic seven-check Gate.
- Live synthetic proof: `BLOCKED / REMEDIATION` -> documented remediation -> `CLEAR / GATE_EVALUATED`.
- Static-host production build 2 serves the landing page, API sandbox, evidence, walkthrough, console, and receipt pages.
- Verification: 34 repository tests pass; final full workspace dry-run reports no changes.

## External activation still required

| Dependency | Current evidence | Human action required |
|---|---|---|
| Xano | Live in workspace 1: 15 tables, four reusable functions, eight public endpoints, production static host | No action required for the implemented spine; preserve dry-run-before-push discipline |
| Nutrient | Typed cached extraction and review routing pass | Add credentials and map confirmed DWS endpoints |
| SerpApi | Typed candidate cache and human decision path pass | Add key, run and cache the two configured searches |
| Doctavian | Template contract and signed-result replay pass | Receive credentials, create template, execute two-party signing |
| Perfect Corp | SD/14-concern/VTO contract and replay pass | Obtain written approval for this non-diagnostic documentation framing, then add key |
| Foxit | Agent contract and rendered PDF pass | Add MCP/PDF Services/eSign credentials and reproduce the human handoff live |
| name.com | Five-operation sandbox contract and replay pass | Add credentials, register a sandbox domain, publish and read the TXT record |

`.env` remains untracked and no credentials are present in tracked files. Only Xano is claimed live;
the remaining vendor integrations continue to use bounded cached contracts until activated.

## Commands

```bash
python -m before.seed
python -m before.verify
python -m before.app.server --offline
python -m unittest discover -s tests -v
```

Optional PDF rebuild:

```bash
python -m pip install -r requirements-artifacts.txt
python -m before.build_evidence_pdf
```
