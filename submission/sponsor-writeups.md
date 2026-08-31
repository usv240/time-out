# Time-Out — sponsor submissions

Paste each section into the matching Devpost challenge. Every section is
self-contained: a judge skimming sixty projects should find their own API in the
first sentence.

**Links for every submission**
- Live: https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io
- API: `POST https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1/encounters/demo/evaluate`
- Repo: https://github.com/usv240/time-out
- Video: [VIDEO URL]

**One-line pitch (use everywhere)**
> Time-Out is the surgical time-out for cosmetic procedures: before an injection can go ahead, it checks who is performing it, what is being used, and whether the patient understood — and refuses to produce a safety record when the evidence isn't there.

---

## Xano — Build a better version of business software you use today

**Xano is the entire backend.** Fifteen tables, the encounter state machine with guarded transitions, the deterministic seven-check Gate, approval gates, an append-only audit log, the public REST API, and static hosting for the site — all in Xano, deployed from the CLI, with the workspace committed as code in `xano-workspace/`.

**Build story**

*What software did you replace?* The pre-procedure compliance checklist that med spas keep as a PDF in a binder, and the static consent form inside their EMR. Both record what happened. Neither can stop anything.

*Why did you choose it?* Because the leading causes of med spa malpractice verdicts — absent informed consent, failure to communicate risk, liability for delegates — are all paperwork failures that happen before the needle, and the existing tools are built to file paperwork, not to gate on it.

*Which AI tools did you use?* Claude Code and OpenAI Codex, with Xano's Developer MCP for schema validation.

*Approximately how long did it take to build?* Ten build days, one person, 17 Aug – 2 Sep 2026.

*What would have taken significantly longer without AI + Xano?* The schema, functions, and public API went from local `.xs` files to a live instance in one `xano workspace push`. A state machine with an audit event on every transition, idempotent retries, and human remediation without database edits would have been a week of backend work on its own.

**Where Xano did the real work, and why:** the product *is* a state machine with an audit trail. Xano isn't a database behind the app — it is the app.

---

## SerpApi — Best AI Use Case

**SerpApi supplies live alert candidates that can put a ready procedure on hold.** Time-Out searches FDA warning letters and Texas Medical Board actions. A hit becomes an `AlertCandidate`. If the encounter is already `READY_FOR_PROCEDURE`, it moves back to `HUMAN_REVIEW` until a named Medical Director confirms or dismisses the candidate — and that decision is audited.

In our first live run, the search returned the actual April 2026 FDA warning letter to a Texas med spa that couldn't reconcile its Botox purchases against what it administered. That's the demo.

**The boundary is explicit:** a search result never establishes that a product is counterfeit, that a licence is invalid, or that the law has changed. It changes the *workflow*, not the *conclusion*.

**Where SerpApi did the real work, and why:** live data with a consequence. Not a citations sidebar — a hold.

---

## Perfect Corp — AI-driven consumer experiences

**Skin analysis is normally used to sell a treatment. We run it in the opposite
direction — once, before anything is done, and the result belongs to the patient.**

YouCam Skin Analysis captures the pre-procedure baseline: twelve scored concerns, an
overall score, skin age, and a separate overlay mask per concern, to a fixed capture
contract (frontal, even light, ~1024px) because inconsistent before/after photos are
exactly what gets challenged in a dispute.

**The interactive part is the point.** Twelve stacked overlays make a picture nobody
can read — you cannot tell which mark produced which score. So on the patient's own
receipt the baseline is explorable: select a concern and that mask alone appears over
the face, captioned in plain language, with the score beside it. Concerns are ordered
lowest-score-first, which is the order a clinician would look at them. It is a
radiogroup — arrow keys move between concerns, and the caption is announced — because
a medical record that only works with a mouse is not a record everyone can read.

**Consumer value, concretely:** the patient walks out with an objective, timestamped
record of their own skin from before anything was done, published under their clinic's
domain and verifiable without an account. No med spa gives them that today. If
something looks different in six weeks, this is what it looked like first — and they
can point at the exact overlay and score rather than argue from memory.

**Framing, stated on the screen and not just here:** this is a baseline and a
communication aid. It is never a diagnosis and never an input to any legal reasoning.
Every face in this project is AI-generated and fictional.

**A note for your engineers:** the analysis rejects large images with
`error_src_face_too_small` because it downsamples internally before detection. A tight
face crop around 1024px wide is the working input. It is counterintuitive enough that
we documented it in code for the next person.

**Where Perfect Corp did the real work, and why:** an unexpected use of a retail beauty
API — as a medico-legal baseline the patient owns, in a vertical you are already moving
toward. The same twelve scores that would normally recommend a product here become the
evidence that a procedure happened to a person who looked like this beforehand.

---

## name.com — Domain API Challenge

**Every clinic gets the domain its own patients verify against.** Publishing every
receipt under a domain *we* control leaves the patient trusting us — which is the
exact thing the receipt exists to remove. So onboarding a clinic provisions a domain
that belongs to the clinic, and that clinic's receipts publish underneath it.

Four surfaces, each load-bearing:

| Surface | Endpoint | What it decides |
|---|---|---|
| Search | `POST /core/v1/domains:search` | Find a domain that reads as the clinic's own, not ours |
| Availability | `POST /core/v1/domains:checkAvailability` | Search suggests; availability is what we're willing to promise |
| Registration | `POST /core/v1/domains` | The clinic owns what its patients check against |
| DNS | `POST/PUT/GET /core/v1/domains/{domain}/records` | Two records per receipt: the **digest** (`_timeout.<id>`) and the **status** (`_status.<id>`) |

Run live for a synthetic clinic: `Cedar Park Aesthetics` → search returned 12
candidates → availability confirmed three purchasable at $17.99 →
**`cedarparkaesthetics.com` registered** → receipt `dbb4241c…` published and read
back at `_timeout.syn-receipt-syn-enc-blocked-002.cedarparkaesthetics.com`, matching.
Reproduce with `python -m before.onboard_clinic --clinic "Cedar Park Aesthetics"`
(add `--register` to perform the irreversible step).

**DNS as the revocation channel — the part we think is new.** Time-Out's central
claim is that ready is reversible: a confirmed FDA warning letter moves an encounter
back to human review. That held right up to the moment a receipt was issued. After
that the patient was holding a record saying the checks passed, with no way to learn
it had stopped being true.

Certificates solved this long ago by separating a certificate's contents from its
status. A receipt now carries both, on the clinic's own domain:

```
_timeout.<receipt-id>.<clinic>   digest  → is this the receipt that was issued?
_status.<receipt-id>.<clinic>    status  → is it still good?
```

Those are different questions, and conflating them is how a stale record ends up
looking authoritative. **A missing status record resolves to `UNKNOWN`, never to
valid** — an unpublished receipt and a good one must not look the same to a patient.

Run live: receipt sealed → `status=VALID`; FDA warning letter 723267 confirmed by a
named Medical Director → `status=REVOKED reason=... at=...`; the patient re-checks and
sees the revocation. The receipt page has a **Check this receipt's status now** button
that reads the clinic's domain live through Xano, so no credential touches the browser.
Reproduce with `python -m before.revoke_receipt --seal | --revoke "<reason>" | --show`.

Revocation is a human decision after confirming an alert candidate. The search result
never revokes anything by itself.

**Registration never runs from a page a visitor can click.** It is the one
irreversible call in the flow, so it lives in the onboarding script behind an
explicit flag — the same boundary the product draws everywhere else.

**Edge cases handled:** duplicate publish is idempotent (update, not a second
record); a token still activating returns a clear "activating" state rather than a
failure; a read-back mismatch surfaces as a verification failure, never silently.

**Limits, stated where the result is shown:** sandbox registrations don't resolve
publicly, so verification reads through the API rather than `dig`, and a TXT record
stays mutable by whoever owns the domain. Handing the domain to the clinic removes us
from the trust path; it does not make the record notarised. That sentence is on the
receipt screen, not just here.

**Where name.com did the real work, and why:** a registrar is normally where a
project starts. Here it is the last step — the thing that lets a patient check a
medical record without an account, without `dig`, and without trusting the clinic
that produced it or the vendor that built it.

---

## Nutrient — Turn documents into something people trust

**Nutrient DWS reads the evidence and decides who has to look at it.** Credential, intake, and product documents go through the Data Extraction API and come back as typed fields with **per-element confidence and page coordinates**. Any required field below the confidence floor — the floor lives in code, never in a prompt — routes to a named Medical Director — shown the source page with the uncertain field boxed at the coordinates DWS returned — before the encounter can advance. Processor-side semantic redaction runs before anything leaves the vault.

In our first live run on a three-page evidence record, 3 of 29 elements fell below the 0.80 floor and the review path fired — on real output, not a staged fixture.

**Deterministic, auditable, human-in-the-loop:** confidence gates an irreversible act. The repo is open source, as Nick asked.

**Uniqueness, stated narrowly:** we haven't found, in the public documentation of the named aesthetics platforms, a native scored evidence-bound hold on the whole encounter. Teach-back alone is not novel and we don't claim it.

**Where Nutrient did the real work, and why:** it's not an invoice parser. It's the reason a person sees the uncertain field before the needle, not after.

---

## Doctavian — Generate It Right. Sign It Tight.

**We call your generation API for real, through the full solution-based flow. Eleven
calls succeed. The engine's template read is what fails, and we do not think it is
our template.**

The whole chain runs live against `demo.api.doctavian.com`, authenticated with the
demo key and an OAuth bearer that refreshes itself:

```
POST /v1/documents/template/upload        201   file into Storage
POST /v1/documents/template/create        200   -> documentTemplateGuid
POST /v1/documents/data/upload            201   file into Storage
POST /v1/documents/datasource/create      200   -> dataSourceGuid
POST /v1/documents/configuration/create   200   PDF, delivered to Storage
POST /v1/documents/request/create         200   -> documentRequestGuid
GET  /v1/documents/request/{guid}/get     200   status: Failed
GET  /v1/common/user/get                  200
GET  /v1/common/limits/get                200
GET  /v1/documents/solution/{guid}/get    200
GET  /v1/documents/document/{id}/download 200   byte-identical read-back
```

The document request is accepted and reaches your pipeline. It comes back
`status: "Failed"`, `errorMessage: "Failed to read the template."`

**Why we do not think the template is ours.** We tried to disprove that first:

- **A Word-authored third-party `.docx` fails identically.** So does python-docx's own
  bundled `default.docx`, which Word produced. It is not our authoring tool.
- **A plain-text template with no expressions fails identically.** It is not our
  expression syntax.
- **The uploaded file is intact in your storage** — pushed through `document/upload`,
  pulled back through `document/{id}/download`, byte-identical: same SHA-256, same
  40,120 bytes, same ZIP magic.
- **Not a consistency race** — stable across 0, 5 and 15 second delays.
- The upload route is right: `template/upload` with `X-Storage-Type:
  document-template` is the only one whose id `generate` resolves. Every other route
  reports the file missing, which makes the two error codes a usable oracle.

Every docx we can produce or find fails the same way on the demo subscription, and no
document has ever been generated on this account (`generatedDocumentCount: 0`).

**Two things worth passing to your engineers**

1. **The OpenAPI spec disagrees with the implementation.**
   `POST /v1/documents/request/create` documents the field as `dataGuid`; sending that
   returns `400 REQUEST_DATA_ID_REQUIRED`. The field the service actually accepts is
   **`dataSourceGuid`**. That cost an hour, and the error message points away from the
   real cause.
2. **Freshly uploaded templates intermittently report `FILE_MISSING_FROM_STORAGE`** on
   the very next call, then resolve on a retry. It looks like a write-visibility race.

**What the template is for.** One template, not a library. It branches on the authority
pathway — a physician injecting and a nurse injecting under delegation produce
genuinely different consent — loops over only the disclosures our rules engine actually
cited for that encounter, and calculates the non-clinical disclosure count. Patient and
injector both sign. Every other consent form in this industry is a static PDF that says
the same thing regardless of who picks up the needle.

**We also solved the problem we first wrote to you about.** Generation defaulted to
Google Drive delivery, and we would not grant a third party blanket Drive scope over a
patient-consent workflow. Setting `deliveryMethod: "Storage"` on both the configuration
and the request removes that requirement entirely.

**Where Doctavian does the real work, and why:** consent computed from *who is actually
performing the procedure*, citing only the rules that applied, is the difference between
a signature and a record. We are one engine-side read away from the artifact, and we are
not going to claim a generated document we do not have.

---

## Foxit — From a plain prompt to a signed document

**A Foxit agent assembles the safety record and stops before the irreversible step.** It starts from the prompt *"assemble the safety record for encounter SYN-ENC-BLOCKED-002"*, merges the three source sections through the Foxit MCP server, watermarks the result *SYNTHETIC — NOT FOR CLINICAL USE*, reads its properties into the manifest, and then **pauses**. The Medical Director's attestation is handed to Foxit eSign as a human action.

**Live status:** the agent runs live. Three `upload_document` calls, `get_pdf_properties`, and `download_document` go through the official Foxit MCP server; merge and watermark are routed through PDF Services REST on the same host because the TypeScript MCP server mis-maps `documents`→`documentInfos` and the watermark `opacity`/`text` fields — both workarounds are recorded in the run log with the reason, and we reported them upstream with repros: https://github.com/foxitsoftware/foxit-pdf-api-mcp-server/issues/4. The assembled record is watermarked SYNTHETIC on all three pages and was handed to eSign for the named Medical Director (`folderId 35611080`), who signed it — envelope status `EXECUTED`, 27 Aug 2026. The agent then read the outcome back and downloaded the executed PDF; both files are published on the receipt page.

Three details we were deliberate about. **Sending is a human choice**, never the agent's: `request_attestation(send=False)` is the default and emails nobody. **Reading is not writing**: `collect_attestation()` issues only GETs, and a test asserts it can never POST to an envelope. **The two fingerprints differ, and we say why** rather than hiding it — signing appends a signature and certificate page, so the assembled digest (`6d993838…`) and the signed digest (`c7002375…`) cannot match; publishing only one would let us pass an unsigned file off as signed.

**The pause is the point.** The agent does everything reversible. A licensed person takes the one action that can't be undone. The treatment-party signatures collected by Doctavian are never reused here.

**Where Foxit did the real work, and why:** the assembly is agent-driven and the signature is human-driven, with a hard boundary between them — which is exactly what your challenge asked for.
