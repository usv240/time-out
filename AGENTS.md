# AGENTS.md — read this before writing code

Context for any coding agent (Codex, Claude Code, Cursor) working in this repo.
Full strategy lives in `PLAN.md`. **Do not read PLAN.md for task instructions** — it is a
decision document (why this idea, prize tiers, cut order). Work from `tasks/*.md`.

## What we're building

Two projects for the DevNetwork [API + Cloud + AI] Hackathon 2026. Submit **3 Sep 2026, 10:00 AM PST**.

**Baseline** (`/baseline`) — compliance gate for medical aesthetics. Before a procedure happens,
verify it is legal for that provider in that state, generate the consent that state requires,
capture a clinical baseline, collect three signatures, seal the record.

**Recon** (`/recon`) — expense reports rebuilt. Receipts checked against live market prices.

## Hard rules — violating these breaks the project

1. **The LLM never decides legality and never does arithmetic.** Models map documents to a typed
   schema. All compliance verdicts and all money math run in deterministic code over a rules table.
2. **Synthetic data only. Always.** Never a real clinic name, real person's face, real licence
   number, real lot number, or real patient document. Publicly implying a real business commits
   malpractice is defamation.
3. **Cache every external API response to `.cache/`.** The demo video must never depend on a live
   call succeeding. Add a `--offline` mode that replays cache.
4. **Secrets live in `.env` only.** Never hardcode, never commit, never paste into a prompt.
   `.env.example` lists required keys.
5. **Every compliance decision freezes a `rule_snapshot`.** A decision made today must remain
   explainable in three years after the law changes.

## Stack

| Layer | Choice |
|---|---|
| Backend | **Xano** (data model, business logic, workflows, auth) |
| Hosting | Xano static hosting |
| Frontend | Keep it simple and fast — the demo video is the deliverable, not the framework |
| Documents | Nutrient DWS (extract/redact/view), Doctavian (generate/sign), Foxit (assemble/present) |
| Live data | SerpApi |
| Vision | Perfect Corp YouCam (Camera Kit, Skin Analysis, VTO) |
| Domains/DNS | name.com CORE (sandbox: `https://api.dev.name.com`) |
| Graph | Wundergraph Cosmo — one subgraph per US state |
| API collections | Bruno `.bru` files, committed |

## Known API gotchas

- **name.com:** credentials take ~15 min to activate (401s at first are expected).
  `GET /core/v1/domains/{domain}` returns Not Found unless *you* registered it in the sandbox first.
  DNS records create/read fine but **do not propagate to the internet**.
- **Perfect Corp:** use **SD** not HD for skin analysis — HD burns credits fast. Budget: 1,000 units.
- **Nutrient:** Data Extraction returns confidence + page coords. Low confidence must route to the
  DWS Viewer for human sign-off — that routing is the point, not a nice-to-have.
- **Doctavian:** templates use expressions + elements (branch, loop, calculate). Signing is
  multi-party — patient, injector, supervising physician.

## Conventions

- Small, reviewable commits. Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Every external call goes through a client module with caching + typed responses. No inline fetch.
- Seed only **4 states**: TX, CA, NY, FL. Breadth is a trap; depth demos better.
- Prefer boring, working code. This ships in 17 days and is judged on a video.

## Definition of done for any task

- [ ] Runs end to end from a clean checkout with `.env` populated
- [ ] Works offline from cache
- [ ] No secrets in tracked files
- [ ] Synthetic data only
- [ ] Brief note in the task file on what changed
