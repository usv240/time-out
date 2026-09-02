# Devpost submission — Time-Out

Paste each block into the matching Devpost field. Sponsor challenge text lives in
`sponsor-writeups.md`; this file is the project page itself.

---

## Project name

**Time-Out**

## Elevator pitch (Devpost hard-caps this at 200 characters — this is 187)

> Surgeons pause before every incision. Med spas don't. Time-Out checks who is injecting, what they're using, and whether the patient understood — and refuses when the evidence isn't there.

## Try it out (link)

https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io

## Video demo

`[VIDEO URL]` — recorded Sep 1, ≤3 minutes

## Built with (add each as a tag)

`xano` · `nutrient-dws` · `serpapi` · `perfect-corp-youcam` · `name-com-api` · `doctavian` · `foxit-pdf-services` · `foxit-esign` · `model-context-protocol` · `python` · `javascript` · `webcrypto` · `claude-code` · `codex`

## Image gallery (upload in this order, with these captions)

| File | Caption |
|---|---|
| `screenshots/01-landing.png` | Run the safety check — the real evaluator, no signup |
| `screenshots/02-try-blocked.png` | BLOCKED: a synthetic aesthetician, no delegation evidence, every failed fact cited |
| `screenshots/03-try-break-it.png` | Break it yourself — six real attacks against the live Gate, each refused with its citation |
| `screenshots/04-try-audit.png` | Every attempt in the audit log, with the judge as the actor |
| `screenshots/05-receipt.png` | The patient's receipt: seven checks, their skin baseline, and a published, verifiable record |
| `screenshots/06-reproduced.png` | Reproducibility, in your own browser: WebCrypto re-hashes the live ruleset and it matches |
| `screenshots/07-landing-dark.png` | Theme-aware, keyboard-complete |
| `screenshots/08-xano-tables.png` | The backend is Xano: 17 tables, each documented with the constraint it enforces — "append-only", "immutable once used by a decision", "never a finding of fact" |
| `screenshots/09-xano-functions.png` | The Gate as a Xano function: "no network calls and no short-circuiting… a safety determination for human review, never a legality decision" |

---

## Here's the whole story

### Some treatments cannot be undone

Before every incision, a surgical team stops. They confirm the patient, the site, and the procedure out loud. In the study that introduced the WHO surgical safety checklist, complications fell from 11.0% to 7.0% and inpatient deaths from 1.5% to 0.8% ([Haynes et al., NEJM 2009](https://pubmed.ncbi.nlm.nih.gov/19144931/)).

Med spas don't have one. There are about 13,000 of them in the US, growing fast, and neurotoxin and filler injections happen thousands of times a day in rooms where the person holding the needle may be an aesthetician, a "laser technician," or a nurse working under a delegation agreement nobody has seen. Complication rates are measurably higher than in physician offices. When a review looked at twenty med-spa malpractice cases, thirteen ended in verdicts for the patient, averaging near $2.5 million — and the leading causes weren't bad hands. They were **absent informed consent, failure to communicate risk, and liability for the actions of delegates.** Paperwork failures. All of them before the needle.

In April 2026 the FDA warned a Texas med spa that couldn't reconcile the authentic Botox it bought against what it recorded injecting.

Time-Out is the pause those rooms are missing.

### What it does

Before a cosmetic procedure can go ahead, Time-Out runs seven checks against the Texas ruleset and the evidence on file:

1. Is the licence active, in-state, unexpired?
2. May this person perform this — directly, or under documented delegation? *A job title is never an answer.*
3. Is there a patient-specific order, a signed protocol, current BLS, an available supervisor?
4. Was the pre-procedure assessment recorded?
5. Is the product lot captured and free of any confirmed alert?
6. Did the patient pass a teach-back — say the risks back in their own words, not tick a box?
7. Any disciplinary finding?

Three answers are possible: **CLEAR**, **BLOCKED**, or **REVIEW** — because some rules are genuinely ambiguous, and when they are, the software says so and a named human decides. It never guesses.

If the answer is BLOCKED, the screen names the exact missing evidence, cites the rule, and offers a remedy. A person attaches what's missing and re-runs the check. Nobody edits a database. If the answer is CLEAR, consent is compiled from a template that branches on who is performing the procedure, the patient completes the teach-back, a standardized skin baseline is captured, an agent assembles the record and *stops*, and a Medical Director signs the attestation. The result is a safety receipt — frozen with the exact ruleset used, hashed, published as a DNS record, and handed to the patient.

And if an FDA warning letter lands *after* an encounter is ready, it goes back to review. Ready is reversible.

### Try to break it

The landing page runs the real evaluator against a fresh synthetic encounter — no signup, no key. Then `/try` invites you to attack it: swap in the aesthetician, delete the delegation protocol, skip the patient order, use the FDA-flagged lot, skip the teach-back, let BLS lapse. Each button is a real call to the backend that takes the complete, valid evidence set, breaks exactly one thing, and re-runs the seven checks. Each refusal cites the rule. Each attempt lands in the audit log with you as the actor.

On `/how-it-works`, your browser fetches a live verdict, hashes the canonical ruleset itself with WebCrypto, and compares it to the server's fingerprint. They match, byte for byte. You don't have to take our word for it.

### How it's built

The rule that shapes everything: **the software never decides what's legal, and no model ever does arithmetic.** Models read documents into typed fields with confidence scores. Every verdict comes from deterministic code over a cited rules table. Anything uncertain goes to a named human.

- **Xano** is the entire backend — fifteen tables, the encounter state machine with guarded transitions, the Gate, an append-only audit log, the public API, and the static site — deployed from the CLI and committed as code.
- **Nutrient DWS** reads credential, intake, and product documents into typed fields with per-element confidence and page coordinates. Anything below the confidence floor routes to a named Medical Director before the encounter can advance. Redaction runs before anything leaves the vault.
- **SerpApi** searches FDA warning letters and Texas board actions live. A hit is an alert *candidate* that reopens a ready encounter; a person confirms or dismisses it, and that decision is audited. Our first live search returned the actual April 2026 warning letter.
- **Perfect Corp YouCam** captures the patient's skin baseline — twelve scored concerns, overlay masks, skin age — before treatment. A record the patient keeps. A baseline and communication aid; never a diagnosis.
- **name.com** publishes each receipt's SHA-256 as a DNS TXT record on a registered domain and reads it back through the API. Verification that doesn't require trusting us.
- **Doctavian** holds one consent template that branches on the authority pathway, loops over cited disclosures, and calculates only the non-clinical disclosure count. Nothing uncited enters the document.
- **Foxit** runs the assembly agent: from a plain prompt, through the official Foxit MCP server, to a watermarked three-page record — then it stops. The Medical Director's attestation is a human eSign action, and it was signed: envelope `35704700`, status EXECUTED. The agent reads the outcome back but issues only GETs, so it can never act on an envelope. We found, worked around and reported upstream three field-mapping bugs in the MCP server along the way, each with a reproduction.

### What this is not

We'd rather you trust the parts that work. It does not determine legality — it produces a safety determination for a licensed human to review. It does not certify that a treatment is safe, that a product is authentic, or that an outcome will be good. Teach-back isn't ours; what we haven't found elsewhere is binding a scored teach-back to a whole-encounter hold with a versioned rule snapshot. The receipt is a record, not a notary — the verification domain runs in a sandbox and DNS records are mutable by their owner. Texas neurotoxin only. Every clinic, patient, face, licence, lot, and document in this project is synthetic.

### Where it stands

All seven sponsor integrations run live against real APIs, with responses cached so the demo never depends on a third party answering at the moment a judge clicks. Doctavian was the hard one: generation returned TEMPLATE_READ_FAILED until we found the payload needs a root `data` wrapper the docs don't show. The generated consent PDF is committed and viewable on /try.

One person, ten build days, Claude Code and Codex, ninety-four tests, CI green, public repo.

**Repo:** https://github.com/usv240/time-out
