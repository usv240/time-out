# Time-Out implementation status - 27 Aug 2026

## Code-complete reference and live Xano spine

- Deterministic seven-check Gate with `CLEAR` / `BLOCKED` / `REVIEW`
- Current architecture state machine with guarded transitions
- Audit event on every transition and idempotent same-state retry
- Human remediation without direct database editing
- Frozen rule snapshot and byte-identical reproduction
- Named-role review for low-confidence Nutrient extraction
- SerpApi alert candidate and reversible ready state
- Reproducible three-page Doctavian DOCX with native conditional/loop/count elements, cached generation/envelope transport, and an explicit Patient + Injector completion gate
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

- Production site: `https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io`
- Public API: `https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1`
- Workspace 1 contains 15 Time-Out tables, guarded encounter transitions, immutable audit events, and frozen rule snapshots.
- `POST /v1/encounters/{encounter_id}/evaluate` invokes the deterministic seven-check Gate.
- Live synthetic proof: `BLOCKED / REMEDIATION` -> documented remediation -> `CLEAR / GATE_EVALUATED`.
- Static-host production build 2 serves the landing page, API sandbox, evidence, walkthrough, console, and receipt pages.
- Verification: repository tests pass locally; the Xano dry-run discipline remains mandatory before the next push.

## Hosted site — 27 Aug

- `/try`: step 1 runs the Gate live on Xano against a fresh per-visitor encounter; sponsor steps replay cached live responses (badged CACHED · 26 Aug); every step has an `i` (what / why / source); **Break it yourself** — six attacks, each the complete evidence set with one thing broken, sent to `remediate` + `evaluate` live; reset; audit log from `GET /v1/encounters/{id}`; Foxit MCP trace + eSign folderId.
- `/receipt`: the committed hero receipt — seven checks with sources, the patient's baseline (14 scores, overlay masks), DNS read-back + limits, the watermarked record, bounded language.
- `/how-it-works`: fetch a live verdict, SHA-256 the canonical ruleset with WebCrypto, compare — REPRODUCED.
- Fixed: the previous console and receipt called `/v1/demo/run` and `/v1/receipts/verify`, which exist only in the local reference server; both pages were broken on the hosted site.
- Dress rehearsals: three network-disabled runs, identical receipt hash (`demo/rehearsals.md`).
- Submission text ready: `submission/devpost.md`, `submission/sponsor-writeups.md`, seven screenshots, `demo/script.md` (≤3:00).

## Sponsor closure status — 24 Aug

| Dependency | Current evidence | Remaining closure |
|---|---|---|
| Xano | Live in workspace 1: 15 tables, four reusable functions, eight public endpoints, production static host | No action required for the implemented spine; preserve dry-run-before-push discipline |
| Nutrient | Live parse frozen behind the shared cache; exact offline replay; typed fields/confidence/coordinates; SHA-bound synthetic egress guard; named-role state-machine hold tested | Surface the source page/coordinates and review resolution in the hosted encounter UI |
| SerpApi | Live FDA + Texas Board queries frozen behind the shared cache; echoed keys scrubbed; candidates revert readiness to human review | Surface the audited confirm/dismiss action in the hosted encounter UI |
| Doctavian | Auth, data source, solution, template upload, data upload live. Native branch/loop/count DOCX built and tested. Generation fails at delivery: `COPY_FILE_GOOGLEDRIVE_FAILED` — the demo account defaulted to Drive output and we declined full Drive access. Asked Doctavian for an internal-storage option. | Live generation only if a non-Drive delivery is provided |
| Perfect Corp | Newly generated fictional face; live SD analysis; 12 returned scores/masks; raw ZIP cached; signed URL scrubbed; typed baseline and layered mask rendered | No remaining hero-path integration; conserve credits and keep VTO explicitly out of scope |
| Foxit | Agent live: prompt → 5 MCP calls (upload ×3, properties, download) + merge/watermark via PDF Services REST because the TypeScript MCP server mis-maps `documents`→`documentInfos` and watermark `opacity`/`text`; both recorded in the run log. 3/3 pages watermarked SYNTHETIC. Real eSign draft folder 35585692 for the Medical Director (nobody emailed until a person chooses `send`). | Human eSign completion during the recording |
| name.com | Corrected runtime receipt hash published at a digest-versioned TXT host and matched by sandbox API read-back; exact replay works without credentials | Preserve the explicit sandbox non-propagation, owner-mutability, and notary limits in every receipt view |

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
