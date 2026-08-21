# BEFORE implementation status - 20 Aug 2026

## Code-complete offline reference

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

## External activation still required

| Dependency | Current evidence | Human action required |
|---|---|---|
| Xano | Schema and API contracts exist; local reference passes | Enable billing/CLI push, authenticate workspace, reproduce functions, deploy static site |
| Nutrient | Typed cached extraction and review routing pass | Add credentials and map confirmed DWS endpoints |
| SerpApi | Typed candidate cache and human decision path pass | Add key, run and cache the two configured searches |
| Doctavian | Template contract and signed-result replay pass | Receive credentials, create template, execute two-party signing |
| Perfect Corp | SD/14-concern/VTO contract and replay pass | Obtain written approval for this non-diagnostic documentation framing, then add key |
| Foxit | Agent contract and rendered PDF pass | Add MCP/PDF Services/eSign credentials and reproduce the human handoff live |
| name.com | Five-operation sandbox contract and replay pass | Add credentials, register a sandbox domain, publish and read the TXT record |

No `.env` exists and the Xano CLI is unavailable in the current workspace. No live
vendor or deployment claim is made.

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
