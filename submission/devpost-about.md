# About the project

Paste everything below the line into Devpost's **"About the project"** box. It is
already in Devpost's seven headings and formatted as Markdown, which that field accepts.

Nothing here is a claim the site does not already carry a source for. Numbers checked
2026-09-02: 97 offline tests, 56 live browser checks, 17 Xano tables, 13 public
endpoints, 8 backend functions, eSign envelope 35704700 EXECUTED.

---

## Inspiration

Before any surgery, the whole team stops and confirms out loud: right patient, right
place, right procedure. It is called a time-out, and it is boring on purpose. In the
study that introduced the WHO surgical safety checklist, complications fell from 11.0%
to 7.0% and inpatient deaths from 1.5% to 0.8% ([Haynes et al., NEJM
2009](https://pubmed.ncbi.nlm.nih.gov/19144931/)).

Med spas have no equivalent pause. There are roughly **13,000** of them in the US,
growing faster than the oversight, and neurotoxin injections happen thousands of times
a day in rooms where the person holding the needle may be an aesthetician, a "laser
technician", or a nurse working under a delegation agreement nobody has ever seen.

The thing that made me build this: when med-spa malpractice cases reach a verdict, the
leading causes are not bad hands. They are **absent informed consent, failure to
communicate risk, and liability for the actions of delegates**. Paperwork failures,
every one of them, and every one of them decidable *before* the needle goes in. In
April 2026 the FDA warned a Texas med spa that could not reconcile the authentic Botox
it had bought against what it had recorded injecting.

Time-Out is the pause those rooms are missing.

## What it does

Before a cosmetic procedure can go ahead, Time-Out runs seven checks against the Texas
ruleset and the evidence actually on file:

1. Is the licence active, in-state and unexpired?
2. May this person perform this, directly or under documented delegation? **A job title
   is never an answer on its own.**
3. Is there a patient-specific order, a signed protocol, current BLS, an available
   supervisor?
4. Was the pre-procedure assessment recorded?
5. Is the product lot captured and free of any confirmed alert?
6. Did the patient pass a teach-back, saying the risks back in their own words rather
   than ticking a box?
7. Any disciplinary finding?

Three answers are possible: **CLEAR**, **BLOCKED**, or **REVIEW**. Some rules are
genuinely ambiguous, and when they are, the software says so and a named human decides.
It never guesses.

**Blocking well is the whole product.** A BLOCKED result is not an error message. It
names the exact documents that are missing, cites the Texas rule it is applying, and
tells the clinic how to fix it. Somebody attaches the missing evidence and re-runs the
check. Nobody edits a database. That is the difference between software that stops you
and software that helps you.

When everything clears, consent is compiled from a template that branches on who is
performing the procedure, the patient completes a teach-back, a standardised skin
baseline is captured, an agent assembles the record and **stops**, and a Medical
Director signs the attestation by hand. The patient walks out with a safety receipt:
what was checked, who was responsible, their skin baseline, and a fingerprint of the
exact ruleset used, published where anyone can verify it later.

And if an FDA warning letter lands *after* an encounter is ready, it goes back to
review. Ready is reversible.

## How we built it

One rule shapes everything: **the software never decides what is legal, and no model
ever does arithmetic.** Models read documents into typed fields with confidence scores.
Every verdict comes from deterministic code over a cited rules table. Anything
uncertain stops for a named human.

- **Xano** is the entire backend: 17 tables, 13 public endpoints, 8 functions, the
  encounter state machine with guarded transitions, the Gate, an append-only audit log,
  and the static site. Deployed from the CLI and committed as code.
- **Nutrient DWS** reads credential, intake and product documents into typed fields with
  per-element confidence and page coordinates. Anything below the confidence floor
  routes to a Medical Director before the encounter can advance.
- **SerpApi** searches FDA warning letters and Texas board actions live. A hit is an
  alert *candidate* that can reopen a cleared encounter; a person confirms or dismisses
  it, and that decision is audited. Our first live search returned the actual April 2026
  warning letter.
- **Perfect Corp YouCam** captures the patient's skin baseline before treatment: twelve
  scored concerns, overlay masks, skin age. A record the patient keeps. A baseline and
  communication aid, never a diagnosis.
- **name.com** publishes each receipt's SHA-256 as a DNS TXT record on a registered
  domain and reads it back through the API, so verification does not require trusting
  us.
- **Doctavian** holds one consent template that branches on the authority pathway, loops
  over cited disclosures, and calculates only the non-clinical disclosure count.
- **Foxit** runs the assembly agent: from a plain prompt, through the official Foxit MCP
  server, to a watermarked three-page record, and then it stops. The attestation is a
  human eSign action, and it was signed: envelope **35704700**, status EXECUTED. The
  agent reads the outcome back but issues only GETs, so it can never act on an envelope.

The API is **open on purpose**. No signup, no key, no account. You can generate an
optional tag that labels your calls in the audit log, and it grants nothing: every
endpoint returns 200 with it, with a nonsense key, or with nothing at all. The whole
lifecycle works from any client: evaluate the seeded encounter and it comes back
BLOCKED, attach the missing evidence, evaluate again and it comes back CLEAR. Verified
end to end over plain HTTP with no credentials.

## Challenges we ran into

**Doctavian returned `TEMPLATE_READ_FAILED` and I twice concluded it was unwinnable.**
Both times I was wrong. The payload needs a root `data` wrapper that the docs do not
show. Once that was found, generation worked end to end and the consent PDF is committed
and viewable on the site.

**Two of the six attacks returned HTTP 400 instead of refusing.** Xano rejects `""` for
a required text input, and `""` is precisely how a caller says "the delegation document
is absent", which is the whole aesthetician-swap attack. Making those inputs optional
is what let the attack be expressed at all.

**The Gate failed open on a null delegation id**, because `null != ""` is true. Three
null guards, and a test that pins each one.

**The signed record contradicted its own signature page.** eSign overlays a signature;
it does not rewrite the body. So page 1 read "AWAITING HUMAN ATTESTATION" on a document
that had just been signed. The wording now holds in both states, and the record was
reassembled and re-signed.

**A citation the demo points at had rotted.** Texas moved its register to a new portal,
so every "22 TAC Chapter 169" link returned "the requested file was not found". The
frozen rule snapshot keeps the original URL deliberately, because a snapshot exists to
record
what was cited when it was taken, and repairing link rot inside it would defeat the
point. The reader is redirected at render time instead. Link rot is exactly the failure
a frozen snapshot is supposed to survive, and it happened to us mid-build.

**An em-dash cleanup pass silently deleted the `<title>` on all seven pages.** The regex
matched a title containing an em dash and returned only the text between the tags,
dropping the tags with the dash.
Browsers treat stray text in `<head>` as the start of `<body>`, so the title rendered as
body copy in the corner of every page and every tab showed the bare URL.

**Three separate bugs were things that existed but could not be seen.** The tip
explaining the glossary rendered 6,254px down the home page. The stats rail was
`position: sticky` and floated over the verdict card. The API playground answered in
0.6 seconds into a pane 884px below the fold, so the button looked dead. All three
passed every automated check, because the checks verified existence rather than
visibility.

## Accomplishments that we're proud of

**The blocked screen.** It took the most iterations and it is the thing that makes this
a product rather than a gate. It names four missing documents, cites the rule, and tells
you how to fix it.

**You can try to break it, live, with your own data.** Six attacks, each removing exactly
one thing the rules require, each a real call. Or set all nineteen fields yourself, or
download the evidence set, edit it and paste it back. Every attempt lands in the
append-only audit log with you named as the actor.

**Reproducibility you can check without trusting us.** Your browser fetches a live
verdict, hashes the canonical ruleset itself with WebCrypto, and compares it to the
server's fingerprint. They match byte for byte.

**The system refuses real patient data.** An email address, phone number or SSN in any
field is rejected before storage, not after. We wrote that guard, then found it rejected
legitimate synthetic data because it counted digits across all fields at once, and fixed
it to work per field.

**Seven sponsor integrations that each own a step nothing else could do**, with
responses cached so the demo never depends on a third party answering at the moment a
judge clicks. And 97 offline tests plus 56 live browser checks, CI green, public repo.

## What we learned

**A checker that only ever says yes has not been tested.** Most of the engineering went
into the failure paths, and almost every real bug was found by trying to break our own
system rather than by running it correctly.

**Verifying that something exists is not verifying that it works.** Three of our worst
bugs shipped past a green test suite because the assertions checked presence, not
position or visibility. Screenshots caught what the tests could not.

**The hard part of a safety product is the boundary, not the logic.** Deciding where the
software stops and a human starts is the design. Everything downstream of that
follows.

**Say what you have not proven.** No clinic has used this. We replaced the customer
stories we do not have with every assumption the design rests on, every edge case, and
the named test that pins each one.

## What's next for Time-Out

The customer is the clinic, and this sits in front of every procedure they book.

It starts narrow on purpose: **Texas, one drug class.** Every new state or procedure is
a rules file, not a rewrite. The ruleset is data, versioned and hashed, so adding
Florida or dermal filler is rule authoring plus review, not re-engineering.

Insurers and defence lawyers already pay for these failures, after somebody has been
hurt. Time-Out moves the check to the one moment it is still cheap to fix.

Before the needle.

**What would have to be true first:** a licensed medical director signing off on the
rules for each new jurisdiction, a real credential source instead of synthetic fixtures,
and a HIPAA posture that this sandbox deliberately does not have. It refuses real
patient data today, on purpose.

**Repo:** https://github.com/usv240/time-out
**Live:** https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io

---

## Built with (paste one at a time; Devpost caps at 25)

Devpost turns each of these into a tag, and sponsor judges filter by their own product
tag, so the seven sponsor products go in first. Every entry below is something the repo
actually calls, checked 2026-09-02.

**Sponsors first (these are the ones being filtered on):**

```
xano
nutrient
serpapi
perfect-corp
name.com
doctavian
foxit
```

**Then the rest, in order of how much they carry:**

```
foxit-esign
foxit-pdf-services
model-context-protocol
xanoscript
python
javascript
webcrypto
sha-256
dns
rest-api
oauth2
pkce
playwright
pytest
reportlab
pypdf
github-actions
html
```

That is exactly 25. If Devpost rejects a tag with a dot or a hyphen, try `namecom` and
`perfectcorp`, and drop `html` before dropping anything above it.

**Two worth not cutting:** `webcrypto` and `sha-256` are what back the reproducibility
claim, and `model-context-protocol` is the one that tells a Foxit judge the agent went
through their MCP server rather than raw HTTP.

## Try it out (links)

Add both. The live site first, because it is the one a judge will actually click.

```
https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io
https://github.com/usv240/time-out
```

If a third link is allowed, this one goes straight to the thing that makes the project
look real, with no navigation needed:

```
https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io/try.html
```
