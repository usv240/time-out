# Time-Out

Time-Out is a pre-procedure safety proof for cosmetic treatment. The current hero
path is deliberately narrow: **Texas + neurotoxin + synthetic data only**.

The Phase 1 Gate is a pure, offline Python function. It evaluates seven evidence
groups, returns `CLEAR`, `BLOCKED`, or `REVIEW`, preserves every finding and its
source, and freezes the exact rule JSON with a SHA-256 digest. Its output is a
pre-procedure safety determination for human review, not a legal opinion.

## Run locally

```bash
git clone https://github.com/usv240/time-out.git && cd time-out
python -m pip install -r requirements.txt
cp .env.example .env          # optional — only needed for live sponsor calls
python -m before.seed         # writes the synthetic cache
python -m before.verify       # runs the whole hero path offline, prints the receipt
python -m pytest tests -q     # 55 checks
```

Everything above runs with **no network and no credentials**. Live sponsor calls
(Nutrient, SerpApi, name.com, Perfect Corp, Foxit, Doctavian) activate only when
the matching keys are present in `.env`; otherwise the same typed, cached responses
replay. The demo is recorded network-disabled on purpose.

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
