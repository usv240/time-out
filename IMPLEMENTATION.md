# BEFORE implementation status - 24 Aug 2026

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
- Perfect Corp SD baseline with twelve returned concerns, overall score, synthetic skin age, masks, provenance, and an explicit VTO cut
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
- Verification: repository tests pass locally; the Xano dry-run discipline remains mandatory before the next push.

## Sponsor closure status — 24 Aug

| Dependency | Current evidence | Remaining closure |
|---|---|---|
| Xano | Live in workspace 1: 15 tables, four reusable functions, eight public endpoints, production static host | No action required for the implemented spine; preserve dry-run-before-push discipline |
| Nutrient | Live parse frozen behind the shared cache; exact offline replay; typed fields/confidence/coordinates; SHA-bound synthetic egress guard; named-role state-machine hold tested | Surface the source page/coordinates and review resolution in the hosted encounter UI |
| SerpApi | Live FDA + Texas Board queries frozen behind the shared cache; echoed keys scrubbed; candidates revert readiness to human review | Surface the audited confirm/dismiss action in the hosted encounter UI |
| Doctavian | Auth/solution/template/data upload proven | Rotate credentials, authorize Drive, generate branching consent, collect two signatures |
| Perfect Corp | Newly generated fictional face; live SD analysis; 12 returned scores/masks; raw ZIP cached; signed URL scrubbed; typed baseline and layered mask rendered | No remaining hero-path integration; conserve credits and keep VTO explicitly out of scope |
| Foxit | Live PDF Services upload proven | Implement prompt → MCP assembly → pause → Medical Director eSign |
| name.com | Actual deterministic receipt hash published and matched by sandbox API read-back; exact replay works without credentials | Preserve the explicit sandbox non-propagation, owner-mutability, and notary limits in every receipt view |

`.env` remains untracked and no credentials are present in tracked files or
reachable history. The compromised Doctavian values were removed on 24 Aug;
fresh rotated credentials are required. Exact closure gates live in
`tasks/07-release.md`.

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
