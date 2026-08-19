# BEFORE

BEFORE is a pre-procedure safety proof for cosmetic treatment. The current hero
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
