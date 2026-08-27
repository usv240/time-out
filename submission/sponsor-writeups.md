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

## Xano — "Rebuild a SaaS tool you hate"

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

**YouCam Skin Analysis captures the patient's pre-procedure baseline.** Twelve scored concerns, an overall score, skin age, and per-concern overlay masks, recorded before treatment and carried into the patient's own safety receipt. The image is captured to a fixed framing, because inconsistent before/after photos are exactly what gets challenged in a dispute.

**Consumer value:** the patient leaves with an objective record of their own skin *before* anything was done to it — something no med spa gives them today.

**Framing, stated plainly:** this is a baseline and communication aid. It is never a diagnosis and never an input to any legal reasoning. Faces in this project are synthetic, generated, and fictional.

**A note for your engineers:** the analysis rejects large images with `error_src_face_too_small` because it downsamples internally. A tight face crop at ~1024px wide is the working input; it's documented in code.

**Where Perfect Corp did the real work, and why:** an unexpected use of a retail beauty API — as a medico-legal baseline, a vertical you're already moving toward.

---

## name.com — Domain API Challenge

**Four name.com endpoints make the receipt independently verifiable.** Search and availability to claim the registry namespace; registration for `timeout-receipts-demo.com`; DNS to publish each safety receipt's SHA-256 as a TXT record; and read-back through the API to verify it.

A patient handed a Time-Out receipt can check that the record they hold matches what was published — without an account and without trusting our server.

**Limits, stated where the result is shown:** sandbox DNS doesn't propagate to public resolvers, so verification reads through the API rather than `dig`. And a TXT record is mutable by its owner. This is a verification channel, not an immutable notary. We say so on the receipt screen.

**Edge cases handled:** duplicate publish is idempotent (update, not a second record); a token that hasn't finished activating returns a clear "activating" state rather than a failure; a read-back mismatch is surfaced as a verification failure, never silently.

**Where name.com did the real work, and why:** not a domain search tool. DNS as public infrastructure for a record that has to outlive us.

---

## Nutrient — Turn documents into something people trust

**Nutrient DWS reads the evidence and decides who has to look at it.** Credential, intake, and product documents go through the Data Extraction API and come back as typed fields with **per-element confidence and page coordinates**. Any required field below the confidence floor — the floor lives in code, never in a prompt — routes to a named Medical Director — shown the source page with the uncertain field boxed at the coordinates DWS returned — before the encounter can advance. Processor-side semantic redaction runs before anything leaves the vault.

In our first live run on a three-page evidence record, 3 of 29 elements fell below the 0.80 floor and the review path fired — on real output, not a staged fixture.

**Deterministic, auditable, human-in-the-loop:** confidence gates an irreversible act. The repo is open source, as Nick asked.

**Uniqueness, stated narrowly:** we haven't found, in the public documentation of the named aesthetics platforms, a native scored evidence-bound hold on the whole encounter. Teach-back alone is not novel and we don't claim it.

**Where Nutrient did the real work, and why:** it's not an invoice parser. It's the reason a person sees the uncertain field before the needle, not after.

---

## Doctavian — Generate It Right. Sign It Tight.

**One Doctavian template carries the logic for every Texas neurotoxin consent.** It branches on procedure and on the provider's authority pathway (direct performer vs. delegated RN), loops over the cited risk disclosures required for that path, and calculates only the non-clinical disclosure count. Patient and injector sign. **Nothing uncited enters the document** — no invented cooling-off period, no calculated clinical dose. The Medical Director's attestation is a separate document with a separate signer, on purpose.

**Live status, stated honestly:** authentication, data source, solution, template upload, and data upload all succeed against the demo API. Generation currently fails at delivery with `COPY_FILE_GOOGLEDRIVE_FAILED` because the demo account defaulted to Google Drive output and we declined to grant a third party full Drive access for a hackathon build. We've asked Doctavian for an internal-storage delivery option. The template is real, tested, and in the repo at `before/doctavian/`.

**Where Doctavian did the real work, and why:** consent that changes shape depending on who is allowed to perform the procedure. Fifty static forms can't do that. One template with real branching can.

---

## Foxit — From a plain prompt to a signed document

**A Foxit agent assembles the safety record and stops before the irreversible step.** It starts from the prompt *"assemble the safety record for encounter SYN-ENC-BLOCKED-002"*, merges the three source sections through the Foxit MCP server, watermarks the result *SYNTHETIC — NOT FOR CLINICAL USE*, reads its properties into the manifest, and then **pauses**. The Medical Director's attestation is handed to Foxit eSign as a human action.

**Live status:** the agent runs live. Three `upload_document` calls, `get_pdf_properties`, and `download_document` go through the official Foxit MCP server; merge and watermark are routed through PDF Services REST on the same host because the TypeScript MCP server mis-maps `documents`→`documentInfos` and the watermark `opacity`/`text` fields — both workarounds are recorded in the run log with the reason, and we reported them upstream with repros: https://github.com/foxitsoftware/foxit-pdf-api-mcp-server/issues/4. The assembled record is watermarked SYNTHETIC on all three pages, and a real eSign draft folder (`folderId 35585692`) exists for the Medical Director. Nobody is emailed until a person chooses `send`.

**The pause is the point.** The agent does everything reversible. A licensed person takes the one action that can't be undone. The treatment-party signatures collected by Doctavian are never reused here.

**Where Foxit did the real work, and why:** the assembly is agent-driven and the signature is human-driven, with a hard boundary between them — which is exactly what your challenge asked for.
