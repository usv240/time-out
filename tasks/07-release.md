# BEFORE release closure

Status source for the 24 Aug–3 Sep release push. A sponsor is not "live" merely
because an isolated request returned 2xx; it is complete only when its result is
typed, cached, replayable offline, consequential to an encounter, visible in the
demo, and bounded honestly in copy.

## Global gates

- [x] Credential-bearing Postman collection removed from reachable history and
  pruned from the local object database.
- [x] Exposed Doctavian values cleared; fresh rotated credentials are required.
- [x] Xano schema, Gate, guarded transitions, public API, and static site live.
- [x] Core workflow and Xano contract tests pass locally (46 pytest tests, including 29 unittest-style cases).
- [x] Every live vendor operation uses the shared cache envelope and offline
  replay; no direct uncached request remains.
- [ ] One encounter demonstrates every enabled sponsor consequence without
  direct database editing.
- [ ] Three clean, network-disabled dress rehearsals produce the same receipt.
- [ ] CI passes on the public repository and a release tag is recorded.

## Sponsor gates

### Xano

- [x] Fifteen BEFORE domain tables plus workspace support tables deployed.
- [x] Deterministic Gate and state transitions execute in Xano.
- [x] Static site and instant synthetic sandbox are public.
- [ ] Final integrated endpoints pushed only after the mandated full dry-run.

### Nutrient

- [x] Live Processor build and Extraction parse authenticated successfully.
- [x] Confidence and page-coordinate summary exists.
- [x] Live typed extraction is cached and replayable.
- [x] Low-confidence required field creates a named Medical Director review task
  visible in the encounter; resolution reruns the Gate.
- [x] A SHA-bound synthetic-only egress manifest refuses changed, real-entity, or identifier-bearing documents before transmission.

### SerpApi

- [x] Live FDA search authenticated and returned real public results.
- [x] Results are mapped only to `CANDIDATE`, never conclusions.
- [x] Cached candidate reverts `READY_FOR_PROCEDURE` to `HUMAN_REVIEW`.
- [ ] Named human confirm/dismiss decision is audited and shown in the demo.

### Perfect Corp

- [x] Synthetic face upload and SD Skin Analysis completed; result ZIP cached.
- [x] Fourteen concerns, overlays, overall score, and skin age parsed.
- [ ] Typed live baseline is persisted to the encounter and rendered in the UI.
- [ ] Camera framing/failure guidance is visible; VTO is either demonstrated
  honestly or cut explicitly.

### name.com

- [x] Sandbox search, availability, registration, TXT create, and read-back were
  exercised.
- [ ] The sealed receipt hash is published through the cached client and verified
  through the sandbox API from the receipt screen.
- [ ] Copy states sandbox non-propagation and owner mutability beside the result.

### Doctavian

- [x] Auth, data source, solution, template upload, and data upload were exercised.
- [ ] User authorizes Google Drive storage and supplies a fresh rotated API key
  and Drive-scoped bearer.
- [ ] Probe generation succeeds and template expression syntax is fixed.
- [ ] Real template branches on procedure/authority/patient flags, loops through
  cited disclosures, and collects patient + injector signatures.
- [ ] Generated/signed result is cached and attached to the encounter.

### Foxit

- [x] Live PDF Services upload returned a document ID.
- [ ] Agent starts from a plain prompt and performs assembly through Foxit MCP.
- [ ] Agent stops before the irreversible boundary.
- [ ] Medical Director eSign is completed by a human and cached; the Doctavian
  treatment-party signatures are never reused.

## Release and presentation

- [ ] Hosted hero path, API playground, empty states, and error states pass QA.
- [ ] Two first-time users complete the hero path unaided.
- [ ] 2–4 minute captioned, network-disabled video follows `plan/05-demo.md`.
- [ ] Seven sponsor-specific write-ups name the exact API contribution and limits.
- [ ] Devpost submission is complete before 3 Sep 2026, 10:00 AM PST.

## Change note

Created after reconciling the 24 Aug Claude handoff with the repository. It
corrects the earlier overstatement that all seven sponsors were fully live.
24 Aug integration closure: all raw sponsor transports were moved behind the
integrity-checked operation cache. Nutrient now parses a reproducible synthetic
PDF into typed fields/confidence/coordinates, refuses egress unless a matching
synthetic-only manifest is present, and routes uncertainty to a named Medical
Director. SerpApi runs FDA and Texas Board queries, removes echoed credentials
before caching, maps results only to candidates, and replays without network.
The frozen-response state-machine path and credential hygiene are covered by
tests; live captures for both vendors were refreshed successfully.
