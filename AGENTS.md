# AGENTS.md — read this before writing code

Context for any coding agent (Codex, Claude Code, Cursor) working in this repo.
Full strategy lives in `PLAN.md`. **Do not read PLAN.md for task instructions** — it is a
decision document (why this idea, prize tiers, cut order). Work from `tasks/*.md`.

## What we're building

Two projects for the DevNetwork [API + Cloud + AI] Hackathon 2026. Submit **3 Sep 2026, 10:00 AM PST**.

**Time-Out** (`/before`) — the pre-procedure safety proof for cosmetic treatments. Before an
injection or laser treatment begins, Time-Out verifies the provider's authority, checks product
provenance and active alerts, confirms the patient actually *understands* the consent, captures a
standardized clinical baseline, and produces a signed, independently verifiable safety receipt.

Scope: **Texas · neurotoxin · one hero path.** Recon (expense reports) was cancelled — current
market prices cannot reconstruct what was purchasable at the historical booking moment, so
"above market" was never a sound fraud signal.

## Hard rules — violating these breaks the project

1. **The software never determines legality.** It produces a *safety determination for human
   review*. Models map documents to a typed schema; verdicts run in deterministic code over a
   rules table. Enforce this in copy, types, and comments — no exceptions.
   Verdicts are three-state: `CLEAR` / `BLOCKED` / `REVIEW`. Ambiguity resolves to REVIEW,
   never to a guess.
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
| Documents | Nutrient DWS (extract/redact/review), Doctavian (consent + treatment-party signing), Foxit (agent-assembled evidence record + medical director eSign) |
| Live data | SerpApi |
| Vision | Perfect Corp YouCam (Camera Kit, Skin Analysis, VTO) |
| Domains/DNS | name.com CORE (sandbox: `https://api.dev.name.com`) |


## Known API gotchas

- **name.com:** credentials take ~15 min to activate (401s at first are expected).
  `GET /core/v1/domains/{domain}` returns Not Found unless *you* registered it in the sandbox first.
  DNS records create/read fine but **do not propagate to the internet**.
- **Perfect Corp:** use **SD** not HD for skin analysis — HD burns credits fast. Budget: 1,000 units.
- **Nutrient:** Data Extraction returns confidence + page coords. Low confidence must route to the
  DWS Viewer for human sign-off — that routing is the point, not a nice-to-have.
- **Doctavian:** templates use expressions + elements (branch, loop, calculate). Signs the
  **consent** with treatment-party signatures (patient + injector).
- **Foxit:** brief is an *agent from plain prompt to signed document* via MCP + PDF Services,
  with explicit handoff to human signing. Foxit collects the **medical director attestation** —
  never the same signature as Doctavian.
- **Live prize pool is $13,500 across 7 challenges.** Apptio, useBruno, Wundergraph, Kong and
  Impart have no challenge — do not build for them.

## Conventions

- Small, reviewable commits. Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).
- Every external call goes through a client module with caching + typed responses. No inline fetch.
- **Texas only, neurotoxin only.** One hero path done excellently beats breadth.
- Never claim novelty absolutely. Zenoti already ships credential-based booking gating and
  lot-level injectable reconciliation. Our defensible ground is jurisdiction rules-as-code with
  citations, the frozen snapshot, the comprehension gate, and the patient-verifiable receipt.
- Prefer boring, working code. This ships in 17 days and is judged on a video.

## Definition of done for any task

- [ ] Runs end to end from a clean checkout with `.env` populated
- [ ] Works offline from cache
- [ ] No secrets in tracked files
- [ ] Synthetic data only
- [ ] Brief note in the task file on what changed
