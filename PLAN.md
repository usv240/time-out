# DevNetwork [API + Cloud + AI] Hackathon 2026 — Master Build Plan

**Team size:** 2 · **Mode:** Online only · **Start:** Mon 17 Aug 2026 · **Submit:** Thu 3 Sep 2026, 10:00 AM PST
**Projects:** 2 · **Challenges targeted:** 10 · **Addressable prize pool:** ~$16,500

---

## 0. Decisions log (why the plan looks like this)

| Decision | Reason |
|---|---|
| **Not competing for the $12,500 overall prize** | Top 5 are phoned at 1:00 PM on Sep 3 and must be onsite in Santa Clara at 2:00 PM to pitch. We are online-only. |
| **Optimize purely for sponsor challenges** | Judged remotely from the Devpost submission. ~20 winnable slots against ~62 historical submissions. |
| **Two projects, not one** | Xano ($2.5K) and SerpApi ($3K) are the biggest sponsor prizes and both reward *focus*. In an 11-API project neither reads as the star. |
| **Baseline over TrueRate (wage theft)** | TrueRate v1 collided head-on with Mispaid (same input, same output, same $9.99 demand-letter model). TrueRate v2 was viable but could not fit Perfect Corp at all, and had a weak Xano fit. |
| **Kong + Impart demoted** | Both are listed sponsors with **no challenge and no prize**. The chain-of-custody layer designed for them wins $0. |
| **Tier 1 = the five sponsors who spoke at kickoff** | Perfect Corp, Nutrient, Doctavian, name.com, Xano. Every "Coming Soon" brief belongs to a sponsor who stayed silent. Engaged sponsors judge attentively. |
| **Open source from day one** | Nick Winder (Nutrient) explicitly asked for it. Also satisfies name.com's, Doctavian's and Xano's repo requirements. |

### Open questions blocking parts of this plan

1. **Does Perfect Corp's ToS permit clinical / documentation framing?** Ask Wayne Liu day one. Fallback: position as *consultation and documentation support*, never diagnosis.
2. **Do Foxit / Apptio / useBruno / Wundergraph briefs change our fit?** Re-check Devpost daily; all four were "Coming Soon" at kickoff.
3. **Does name.com CORE expose lookups for domains not in your account?** Ask Sam Stobbelaar in the hackathon chat. Current plan assumes **no** and is designed around it.

---

## 1. Project 1 — **Baseline**

> **Pitch:** Baseline verifies a procedure is legal for that provider in that state before it happens, generates the consent that state actually requires, seals the record so it's provable years later — and gives the patient a way to check any of it.

### 1.1 The problem, with evidence

| Finding | Source |
|---|---|
| ~**13,000** US med spas by end of 2026; outnumber McDonald's 2.5:1 in Florida | Singer, Jewell, Saltz & Fiala (2026), *Aesthetic Surgery Journal* 46(7):786, doi:10.1093/asj/sjag085 |
| **Complication rates statistically higher at med spas than physician offices**; documented HIV, hepatitis, and deaths; procedures performed by chiropractors, aestheticians, "laser technicians" | Same |
| Principal drivers of med spa litigation: **lack of informed consent · failure to inform of risks · vicarious liability for actions of delegates** · inappropriate dose · failure to recognize injury | "Emerging Legal Risks in Medical Spa Procedures: Insights From 20 Malpractice Cases", PubMed 42048538 (Westlaw, 2006–2024) |
| **QUAD A risk-stratified accreditation launched March 2026** — green/yellow/orange/red categories, training requirements, mandatory medical director oversight | Singer et al. (2026) |
| Indiana registration + adverse-event framework effective **1 Jul 2026**; Texas "Jennifer's Law" (Sept 2025); NY 200+ inspections Jan 2026; **FDA's first DSCSA warning to a med spa, April 2026** (suspected counterfeit Botox); Georgia bans paid physician-matching services | Holland & Knight, Aug 2026 — *cite the underlying statutes/FDA action directly, not the firm* |

**The gap:** a peer-reviewed analysis of actual litigation names our feature list as the top causes. Existing med spa software (PatientNow, Aesthetic Record, Symplast, Pabau, AestheticsPro) records what happened. **Nothing prevents it.**

### 1.2 What is genuinely not built (verified)

1. **Pre-treatment legality gating.** Compliance is sold as consulting (AmSpa is a trade association) and PDF checklists. No product checks before the appointment.
2. **Consent that branches on live state law.** Every EMR ships static templates.
3. **Patient-side verification.** All guidance is "look it up manually on your state board's website."

**Not our novelty (correction):** objective AI skin scoring is an established category — Facial Aesthetic Index, Facial Youth Index, Skin Quality Index, VISIA, HIPAA-compliant platforms. We *consume* it; we don't claim it.

### 1.3 Product surface

**Clinic app**
1. Book encounter → select procedure + assigned provider
2. **The Gate** runs: is this provider permitted to perform this procedure in this state under this supervision model?
3. Blocked → reason, citation, and the remedies (reassign / add delegation / add supervising physician)
4. Cleared → intake docs parsed, consent generated for that jurisdiction, baseline captured, three signatures collected
5. Record sealed → hash published → binder assembled

**Patient app**
1. Photograph the clinic's posted licence / practitioner credential → verify against state board
2. Photograph the product box → lot number checked against FDA warnings
3. Photograph the consent form handed to you → plain-language explanation of what it signs away
4. Keep your own anchored baseline

### 1.4 Architecture

```
                         ┌─────────────────────────────┐
   Clinic UI ───────────▶│  XANO  (backend of record)  │
   Patient UI ──────────▶│  auth · data model · logic  │
                         │  workflows · static hosting │
                         └──────────┬──────────────────┘
                                    │
              ┌─────────────────────┼─────────────────────┐
              ▼                     ▼                     ▼
      ┌───────────────┐   ┌──────────────────┐   ┌─────────────────┐
      │ NUTRIENT DWS  │   │  THE GATE        │   │  SERPAPI        │
      │ extract+conf  │──▶│  deterministic   │◀──│ live state law  │
      │ redact PHI    │   │  rules engine    │   │ FDA warnings    │
      │ Viewer review │   │  QUAD A tiers    │   │ board actions   │
      └───────────────┘   └────────┬─────────┘   └─────────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ▼              ▼              ▼
            ┌──────────────┐ ┌───────────┐ ┌──────────────┐
            │ PERFECT CORP │ │ DOCTAVIAN │ │ WUNDERGRAPH  │
            │ Camera Kit   │ │ consent   │ │ 1 subgraph   │
            │ skin baseline│ │ 3 signers │ │ per state    │
            │ VTO · video  │ │ sealed    │ └──────────────┘
            └──────────────┘ └─────┬─────┘
                                   ▼
                    ┌──────────────────────────────┐
                    │ SEAL                         │
                    │  FOXIT   → Bates binder      │
                    │  name.com→ DNS TXT hash      │
                    │  BRUNO   → .bru replay pack  │
                    └──────────────────────────────┘
```

**Hard architectural rule:** the LLM never decides legality and never does arithmetic. It maps documents to a typed schema. The Gate is deterministic code over a rules table. This is both correct engineering and precisely Nutrient's stated thesis.

### 1.5 Data model (Xano)

```
Clinic          id, name, state, address, license_no, medical_director_id, quad_a_status
Provider        id, clinic_id, name, credential_type (MD|DO|NP|PA|RN|LPN|AESTHETICIAN|LASER_TECH|CHIRO),
                license_no, license_state, license_expires, delegation_agreement_id, board_status
Procedure       id, name, category (NEUROTOXIN|FILLER|LASER|IPL|PEEL|MICRONEEDLING|IV|GLP1|BODY_CONTOUR),
                quad_a_tier (GREEN|YELLOW|ORANGE|RED), requires_good_faith_exam, requires_rx
JurisdictionRule id, state, procedure_category, permitted_credentials[], supervision_model
                (NONE|GENERAL|DIRECT|ONSITE), requires_delegation_doc, requires_medical_director,
                citation_url, source, verified_at
Encounter       id, clinic_id, patient_id, provider_id, procedure_id, scheduled_at, state,
                gate_decision_id, status
GateDecision    id, encounter_id, verdict (CLEAR|BLOCKED|CONDITIONAL), reasons[], rules_applied[],
                remedies[], evaluated_at, rule_snapshot (frozen JSON)
IntakeDoc       id, encounter_id, kind, dws_file_id, fields{}, confidence{}, review_status, reviewer_id
SkinBaseline    id, encounter_id, capture_meta{}, concerns{name:score 0-100}, overlay_url, captured_at
ConsentRecord   id, encounter_id, doctavian_doc_id, template_version, signers[3], signed_at, sealed_hash
EvidenceBundle  id, encounter_id, foxit_binder_id, sha256, dns_txt_name, dns_published_at, bru_pack_path
AuditEvent      id, encounter_id, actor, action, payload_hash, created_at
ProductLot      id, encounter_id, brand, lot_no, distributor, fda_flag, checked_at
```

### 1.6 The Gate — decision contract

**Input:** `{ state, procedure_id, provider_id, clinic_id, patient_flags[] }`

**Evaluation order (fail fast, collect all reasons):**
1. Provider licence active and unexpired in `state`
2. Provider credential ∈ `JurisdictionRule.permitted_credentials`
3. Supervision model satisfied (medical director on record / delegation doc present / onsite requirement)
4. QUAD A tier requirements met for the procedure category
5. Good-faith exam recorded where required
6. Product lot not on an FDA warning list
7. Board disciplinary status clear

**Output:**
```json
{ "verdict": "BLOCKED",
  "reasons": [{ "code":"CREDENTIAL_NOT_PERMITTED",
                "message":"An aesthetician may not administer neurotoxin in TX.",
                "citation":"...", "rule_id":"tx-neurotoxin-001" }],
  "remedies": [{ "code":"REASSIGN_PROVIDER", "eligible_provider_ids":[...] }],
  "rule_snapshot": { }
}
```

`rule_snapshot` freezes the exact rules used, so a decision made today is explainable in three years even after the law changes. **This is what makes the record defensible and it costs almost nothing to build.**

---

## 2. Project 2 — **Recon**

> **Pitch:** Expense reports rebuilt. Every receipt is checked against live market prices — a $340 hotel claim gets tested against what that room actually cost that night.

**Owner:** Builder B, from Aug 27. **Primary targets:** Xano, SerpApi. **Secondary:** Nutrient.

### 2.1 Why it exists
Xano's brief is "rebuild a SaaS tool you hate" — **Concur is the answer almost everyone gives**, so the premise needs zero explanation. SerpApi's brief is "Best AI Use Case" with live data improving the AI. Live price verification makes search data the *fraud signal itself*, not decoration. Occupational fraud runs ~5% of revenue and nobody has pointed live web pricing at expense review.

### 2.2 Scope (deliberately small — 5 days)
- Receipt upload → extraction (Nutrient) → line items, vendor, date, city, amount
- Policy model in Xano: per-category caps, per-city caps, approval thresholds
- **Live price verification (SerpApi):** hotels, flights, rideshare, meals — query the vendor + city + date, derive an expected range, flag variance
- Verdict per line: `WITHIN_MARKET` / `ABOVE_MARKET` / `UNVERIFIABLE`
- Approver queue with one-click approve/query, full audit trail
- Hosted on Xano static hosting

### 2.3 Data model (Xano)
```
Employee     id, name, email, department, policy_group_id
PolicyGroup  id, name, category_caps{}, city_multipliers{}, approval_threshold
Report       id, employee_id, period, status (DRAFT|SUBMITTED|QUERIED|APPROVED|REJECTED), total
LineItem     id, report_id, category, vendor, city, date, amount, receipt_file_id,
             extracted{}, confidence{}
PriceCheck   id, line_item_id, query, observed_low, observed_median, observed_high,
             source_urls[], verdict, variance_pct, checked_at
Decision     id, report_id, actor, action, note, created_at
```

### 2.4 The demo line
> **"This receipt says $340. That room was $210 that night."**

---

## 3. Sponsor master table

| # | Sponsor | Tier | Prize | Used in | What we build |
|---|---|---|---|---|---|
| 1 | **Perfect Corp** | 1 | $2,500 | Baseline | Camera Kit, Skin Analysis, VTO, image-to-video |
| 2 | **Xano** | 1 | $2,500 | **Recon** + Baseline | Full backend, workflows, auth, static hosting |
| 3 | **name.com** | 1 | $2,000 | Baseline | Search, availability, registration, DNS TXT anchors |
| 4 | **Nutrient DWS** | 1 | $1,500 | Baseline + Recon | Extraction+confidence, Viewer, semantic redaction, Processor |
| 5 | **Doctavian** | 1 | $1,000 | Baseline | Branching consent template, 3-signer flow, sealed trail |
| 6 | **SerpApi** | 2 | $3,000 | **Recon** + Baseline | Live price verification; live state law + FDA warnings |
| 7 | **Foxit** | 3 | $1,000 | Baseline | Bates binder assembly, Embed viewer |
| 8 | **useBruno** | 3 | $1,000 | Both | `.bru` reproducibility pack shipped as a deliverable |
| 9 | **Wundergraph** | 3 | $1,000 | Baseline | One Cosmo subgraph per state |
| 10 | **Apptio** | 3 | $1,000 | TBD | Held — hook ready if brief is FinOps-shaped |
| 11 | **Kong / Impart** | 4 | $0 | — | Skip unless trivial |

---

## 4. Sponsor integration specs

### 4.1 Perfect Corp — Tier 1, $2,500
**Console:** `yce.perfectcorp.com/api-console` · **Redeem:** `yce.perfectcorp.com/api-console/en/redeem-code/` → **1,000 free units (~$179)**
**Docs:** `docs.perfectcorp.com/develop/introduction` · Playground available · MCP optional (API is the requirement; MCP is a bonus)

| Capability | Use in Baseline |
|---|---|
| **JS Camera Kit** | Enforces consistent capture geometry. *Inconsistent framing is exactly why before/after photos get challenged in litigation.* This is the detail that proves we understand the domain. |
| **Skin Analysis API** (14 concerns, 0–100, colour overlays) | The pre-procedure baseline. Use **SD not HD** — HD burns credits. |
| **Virtual Try-On** | Expectation-setting during the consent conversation. Documented unrealistic-expectation management is itself a litigation defence. |
| **Image-to-video** | Renders the record walkthrough for the patient copy. |

**Creative hook:** a retail beauty API repurposed as medico-legal evidence — a vertical they already signalled interest in via the Keensight/Lummitry medical-beauty partnership (April 2026).
**⚠️ Blocking question:** confirm ToS permits clinical/documentation framing.

### 4.2 Xano — Tier 1, $2,500
**Signup:** `go.xano.co/devpost-challenge` · coupon in `.env` (free month, Essential)
**Setup:** enable CLI push in workspace settings · install CLI + MCP via `go.xano.co/start-xano-skill` · static hosting per `docs.xano.com/xano-cli/static-hosting`

- **Recon:** the entire backend — data model, business logic, workflows, approval state machine, auth, integrations, static-hosted frontend. *Xano is the star.*
- **Baseline:** encounters, providers, consent state machine, audit log, auth, hosting.

**Required build story (answer literally in the submission):** what software we replaced (Concur), why, which AI tools (Claude Code), how long it took, what would have taken far longer without AI + Xano.

### 4.3 name.com — Tier 1, $2,000
**Account:** `name.com/nameapi` · **Docs:** `docs.name.com` · **Hub:** `name.dev` · **Docs MCP:** `docs.name.com/integrations/mcp/api-docs-mcp`
**Sandbox:** `https://api.dev.name.com` · Basic Auth (base64) · autofills free credit

**⚠️ Sandbox gotchas (from Sam Stobbelaar's talk):**
- Credentials take **~15 minutes** to activate — 401s at first are expected
- `GET /core/v1/domains/{domain}` returns **Not Found** unless *you* registered it in the sandbox first
- DNS record create/read/update all work but **do not propagate to the internet**

**What we build — all four surfaces:**
| Surface | Use |
|---|---|
| Search | Reserve the registry namespace |
| Availability | Namespace collision check before sealing |
| Registration | Provision registry domains |
| **DNS management** | **Publish `SHA-256(evidence bundle)` as a TXT record** |

**Creative hook:** DNS as a zero-trust verification channel for clinical records. Anyone handed a Baseline chart can `dig TXT case-4f2a.<registry>` and confirm it matches, with no account and no trust in our servers.
**Honest caveat to state on camera:** a TXT record is mutable by its owner, so this is a *public verification channel*, not an immutable notary. Overclaiming loses a technical judge instantly.
**Dropped:** DNS entity-resolution of third-party employers — CORE is a registrar API, not a WHOIS/DNS lookup service.

### 4.4 Nutrient DWS — Tier 1, $1,500
**Campaign:** `api.nutrient.io/campaigns/api-world-cloudx-ai-hackathon-2026/` · credentials in `.env` — **not committed**
**Clients:** `nutrient-dws` (PyPI), official Python/Node clients, and `nutrient-dws-mcp-server`

| API | Use |
|---|---|
| **Data Extraction** | Intake forms, medical history, product packaging (**lot numbers** → FDA cross-check). Returns confidence + page coords + word-level detail. |
| **Confidence thresholds** | **Low-confidence fields route to DWS Viewer for medical director sign-off.** Confidence gates an irreversible act — this is the whole point. |
| **AI redaction** (semantic / regex / preset) | Strip PHI before anything leaves the vault. Use **semantic** mode — it's the differentiated one. |
| **Processor** | OCR, merge, convert. |

**Creative hook:** confidence scores gate an irreversible act. Nick Winder will see fifteen invoice parsers and KYC clones — Nutrient seeded those exact ideas in the brief. **Open-source the repo; he asked.**
**He judges on: uniqueness + the use case.** Put the competitive audit in the write-up.

### 4.5 Doctavian — Tier 1, $1,000
**Get credentials:** email `hello@doctavian.com` **on day one** — they said they'd set teams up fast. Developer portal has quick start + sample use cases + full API specs.

**What we build:** one consent template using **expressions** (real expression engine, conditional logic, calculations) and **elements** (branching, looping, nesting) that:
- branches on `state × procedure_category × quad_a_tier × patient_flags`
- loops over required risk disclosures for that procedure
- calculates dosing limits, cooling-off periods, follow-up windows
- renders a jurisdiction-correct consent every time from one template

Then **multi-signer signing**: patient → injector → supervising physician, with a sealed audit trail.

**Creative hook:** one template, fifty states, three signers.
**Bonus points confirmed at kickoff:** *"if your agent calls the API and does something real, and uses ours for the signatures if your idea calls for it — you get some bonus points."*

### 4.6 SerpApi — Tier 2, $3,000
**Recon (primary):** live price verification. Query vendor + city + date → observed low/median/high → variance verdict. **The search result is the fraud signal.**
**Baseline (secondary):** live state scope-of-practice rules, supervision requirements, FDA warnings and counterfeit lot alerts, state board disciplinary actions.

**⚠️ Demo safety:** cache every response to disk. The video must never depend on a live call succeeding.

### 4.7 Foxit — Tier 3, $1,000 (brief pending)
**Portal:** `developer-api.foxit.com` — free developer accounts

**What we build:** assemble the medico-legal chart binder — merge all source documents, **Bates-number**, paginate, stamp, build the table of exhibits — then serve the patient's copy through the **Embed API** (no-plugin, JS-controlled viewer).

**Creative hook:** three document sponsors, three non-overlapping jobs, mirroring real legal document production — **Nutrient extracts and verifies · Doctavian generates and signs · Foxit assembles and presents.**

### 4.8 useBruno — Tier 3, $1,000 (brief pending)
**What we build:** every sealed record ships with a `.bru` collection committed to the repo alongside it, replaying the exact API calls that produced the compliance decision. Run it with the Bruno CLI (official Docker image) in CI as our contract tests.

**Creative hook:** Bruno as a **deliverable**, not a dev tool. Only possible because Bruno is git-native, offline-only, and account-free — a cloud-synced Postman workspace could never be an audit artifact.

### 4.9 Wundergraph Cosmo — Tier 3, $1,000 (brief pending)
**What we build:** one subgraph per state's regulatory rules, composed into a national supergraph via the Cosmo Router (Apache 2.0, Go). Schema registry + composition checks let a contributor add a state without touching the core.

One query resolves: *for this provider, this procedure, this state → applicable rules + verdict + citations + source coordinates.*

**Creative hook:** federation used for **legal federalism**. Precedent: PhishLink won the Apollo GraphQL challenge here in 2023 for making a genuine graph.

### 4.10 Apptio — Tier 3, $1,000 (brief pending)
**Held.** If FinOps-shaped: per-encounter cost telemetry → **"what does it cost to prevent one adverse event."** Re-check the brief daily.

### 4.11 Kong / Impart — Tier 4, $0
No challenge, no prize. Only if trivial: Kong AI Gateway PII sanitizer on the model path.

---

## 5. Schedule

### Phase 1 · Foundations — Aug 17–19 · both builders

**Aug 17 (today) — unblock everything with lag**
- [ ] Email `hello@doctavian.com` for API credentials
- [ ] Create name.com account + API credentials (~15 min activation); **register 3–5 sandbox domains**
- [ ] Redeem Perfect Corp code → 1,000 units
- [ ] Xano signup with coupon; enable CLI push; install CLI + MCP
- [ ] Nutrient DWS account via campaign URL; SerpApi account
- [ ] Foxit developer account
- [ ] **Ask Wayne Liu: does ToS permit clinical/documentation framing?**
- [ ] **Ask Sam Stobbelaar: does CORE expose lookups for domains not in your account?**

**Aug 18**
- [ ] **Synthetic corpus** (safety-critical, see §6)
- [ ] Public repo + README + licence + CI skeleton
- [ ] Wire name.com Docs MCP and Xano MCP into Claude Code

**Aug 19**
- [ ] Data model finalised in Xano
- [ ] Gate decision contract locked
- [ ] `JurisdictionRule` seeded for **4 states only**: TX, CA, NY, FL (breadth is a trap; depth demos better)

### Phase 2 · Baseline core — Aug 20–26 · both builders

| Date | Work |
|---|---|
| Aug 20–21 | Xano backend: encounters, providers, procedures, consent state machine, audit log, auth |
| Aug 21–22 | **The Gate** — deterministic rules engine, QUAD A tiers, `rule_snapshot` freezing |
| Aug 22–23 | SerpApi: live state law, FDA warnings, board actions. **Cache everything.** |
| Aug 23–24 | Nutrient: extraction + confidence thresholds → Viewer routing; semantic PHI redaction |
| Aug 24–25 | Doctavian: branching template, three-signer flow, sealed trail |
| Aug 25–26 | Perfect Corp: Camera Kit, skin baseline, VTO |
| **Aug 26** | **🎯 Milestone: end-to-end runs start to finish. Ugly is fine.** |

### Phase 3 · Split — Aug 27–31

**Builder A — Baseline depth**
| Date | Work |
|---|---|
| Aug 27–28 | name.com DNS integrity anchors (hash → TXT → verify) |
| Aug 28–29 | Foxit Bates binder + Embed viewer |
| Aug 29–30 | Wundergraph state subgraphs |
| Aug 30–31 | Bruno reproducibility pack; patient-side verification view |

**Builder B — Recon end-to-end**
| Date | Work |
|---|---|
| Aug 27–28 | Xano backend: receipts, policy model, approval workflow (use CLI + MCP for speed) |
| Aug 28–29 | Nutrient receipt extraction |
| Aug 29–30 | **SerpApi live price verification** — the whole point |
| Aug 31 | Polish + Xano static hosting |

### Phase 4 · Freeze, film, write — Sep 1–2 · both

| Date | Work |
|---|---|
| **Sep 1** | **Feature freeze, both projects.** Anything unfinished is cut, not rushed. Bug triage only. |
| Sep 2 AM | Demo videos: Baseline 3 min, Recon 2 min |
| Sep 2 PM | 12 tailored write-ups (§8) — highest-ROI hours of the build |
| Sep 2 EVE | Both projects submitted on Devpost, all challenges selected |
| **Sep 3** | **Buffer only. Submit by 10:00 AM PST. No late projects accepted.** |

> **There is no slack in this schedule.** That is deliberate — see the cut order in §10.

---

## 6. Synthetic corpus spec — *safety-critical*

**Rule: never name a real clinic, never use a real person's face, never use a real licence number, never use a real lot number.** Publicly implying a real business commits malpractice is defamation regardless of intent.

Build on Aug 18:
- **4 fictional clinics** (one per seeded state) with invented licence numbers in obviously-fake formats
- **6 fictional providers** spanning MD, NP, RN, aesthetician, laser tech — at least two who *fail* the gate
- **Synthetic patient faces** — generated, never real people
- **8–10 intake documents**: handwritten-style medical history, typed consent, product packaging photo with an invented lot number, prior-treatment record
- Deliberately include **2–3 low-confidence documents** so the Viewer human-review path fires on camera
- **Recon:** 12–15 receipts, 3 of them priced above market

---

## 7. Demo scripts

### 7.1 Baseline — 3:00

> **The money shot:** *"This provider is an esthetician. In Texas, this procedure requires physician delegation. **Blocked.**"*
> Software saying **no** is what a judge remembers after sixty projects. Build the whole video around the refusal.

| Time | Beat |
|---|---|
| 0:00 | The problem in one sentence, over a real med-spa enforcement headline |
| 0:20 | Patient books. Gate runs. **BLOCKED** — live state rule cited on screen |
| 0:50 | Reassign to a qualified injector. Rules re-resolve; consent generates, branching visibly on state + risk tier |
| 1:30 | Camera Kit capture → scored overlays → three signatures |
| 2:10 | Record sealed. Cut to terminal: `dig TXT` returns the matching hash |
| 2:40 | Patient side: photograph a clinic licence, get an answer |

### 7.2 Recon — 2:00

| Time | Beat |
|---|---|
| 0:00 | "Everyone hates expense reports." No setup needed |
| 0:20 | Drop in receipts → extraction, line items, policy match |
| 1:00 | **"This receipt says $340. That room was $210 that night."** |
| 1:40 | Approval flow + the Xano backend running it |

**Production notes:** screen recording, no talking-head, captions burned in, every API response pre-cached. Both videos 1080p, uploaded to YouTube unlisted.

---

## 8. Submission copy

Past winners at this event made themselves trivially findable — *Hellosign & Clarifai Legal Contract Documents Analyzer*, *Clara – Signal Wire Powered Virtual Assistant*, *Next-Generation API Gateway with Deep Auth0 Integration*, *SpartanZuploSubmission*. Sponsor judges skim ~60 projects hunting for their own API.

**Per-challenge template:**
1. **First sentence names that sponsor's API and what it does here.**
2. Use their vocabulary — Nutrient: *deterministic, auditable, human-in-the-loop*; Doctavian: *branch, loop, calculate*; Bruno: *git-native*; Xano: *reviewed before production*.
3. One line on where their product did the real work **and why nothing else would have.**
4. Link the repo, the demo video, the live URL.

**Sponsor-specific additions:**
| Sponsor | Add |
|---|---|
| Nutrient | The competitive audit — what exists and why the gate doesn't. **He judges on uniqueness.** Note the repo is open source. |
| Xano | The build story, answered literally: replaced Concur; chose it because everyone hates it; Claude Code; N days; what would have taken far longer. |
| name.com | Endpoint coverage table (search + availability + registration + DNS) and the honest TXT-mutability caveat. |
| Doctavian | Screenshot the template's branching logic; name the three signers. |
| Perfect Corp | Lead with consumer value and the new vertical. Mention the case-study/podcast offer interest. |
| SerpApi | Show the before/after of a decision *with* and *without* live data. |

---

## 9. Risk register

| Risk | Likelihood | Response |
|---|---|---|
| Perfect Corp ToS bars clinical framing | Medium | Ask day one. Fallback: *documentation support*, never diagnosis |
| Doctavian credentials arrive late | Medium | Email day one; build template logic against published specs meanwhile |
| name.com sandbox limits | **Known** | Already designed around; anchors use domains we register |
| 11 integrations, 2 people | High | Cut order §10. Depth on Tier 1 beats breadth |
| Live API fails mid-demo | Medium | Cache every response to disk. Never let video depend on network |
| Naming a real clinic / real face | Low | Synthetic corpus enforced from Aug 18 |
| Tier 3 briefs never publish | Medium | Integrations are designed to stand alone; submit anyway |
| Both projects end up half-built | **Highest** | Aug 26 milestone is the checkpoint — if Baseline isn't end-to-end, **cancel Recon** |

---

## 10. Cut order

Cut from the bottom up, without debate:

1. **Kong / Impart** — no prize, no loss
2. **Wundergraph subgraphs** — collapse to a single schema
3. **Foxit binder** — Doctavian's signed output stands alone
4. **Bruno pack** — a README of the calls is a weak substitute but it's something
5. **Patient-side view** — clinic side carries the demo
6. **Recon** — if Baseline isn't end-to-end by Aug 26

**Never cut:** the Gate · consent generation · the three-signer flow · the skin baseline · **the demo video.**

---

## 11. Appendix — credentials & links

| Sponsor | Where |
|---|---|
| Devpost | `api-cloud-ai-hackathon-2026.devpost.com` |
| Perfect Corp | `yce.perfectcorp.com/api-console` · redeem `/redeem-code/` · docs `docs.perfectcorp.com/develop/introduction` |
| Nutrient | `api.nutrient.io/campaigns/api-world-cloudx-ai-hackathon-2026/` — credentials in `.env` (see `.env.example`) — **not committed** |
| Doctavian | `hello@doctavian.com` |
| name.com | `name.com/nameapi` · `docs.name.com` · `name.dev` · sandbox `https://api.dev.name.com` |
| Xano | `go.xano.co/devpost-challenge` · coupon in `.env` · `docs.xano.com` |
| SerpApi | `serpapi.com` |
| Foxit | `developer-api.foxit.com` |
| Bruno | `usebruno.com` · `github.com/usebruno/bruno` |
| Wundergraph | `wundergraph.com/cosmo/router` · `cosmo-docs.wundergraph.com` |

**Sponsor contacts:** Perfect Corp `valerie_torres@perfectcorp.com` · Doctavian `hello@doctavian.com` · name.com `daisy.edwards@identity.digital` · Nutrient `douglas@nutrient.io` · SerpApi `alaa@serpapi.com` · Hackathon `info@devnetwork.com`

---

## 12. Citations

1. Singer, Jewell, Saltz & Fiala (2026). "Med Spas: Patient Safety and Accreditation." *Aesthetic Surgery Journal* 46(7):786. doi:10.1093/asj/sjag085
2. "Emerging Legal Risks in Medical Spa Procedures: Insights From 20 Malpractice Cases." PubMed 42048538 (Westlaw-indexed cases 2006–2024)
3. "Experiences With Medical Spas and Associated Complications: A Survey of Aesthetic Practitioners"
4. "AI assistance in aesthetic medicine — a consensus on objective medical standards." PMC11626373
5. Holland & Knight (Aug 2026). "Medical Spa Compliance Under the Microscope" — *use for orientation; cite underlying statutes and the FDA action directly*
6. QUAD A risk-stratified accreditation programme, March 2026

**Do not cite:** market-size dollar figures (sources ranged $21.4B–$27.8B and med spa counts 8,000–52,833 — a 5× spread; use Singer et al.'s ~13,000 instead). The ASDS "Trends in Medical Spa Statistics" PDF is **unverified** — we could not parse it; do not quote numbers from it.

---

*Last updated: 17 August 2026*
