# Time-Out — demo script (≤ 3:00)

One master cut at ≤ 3:00 satisfies every sponsor's length rule (Perfect Corp caps at
3:00; the rest allow 4:00). Screen recording only, no talking head, captions burned in.
**Record with the network on** — every step is either a live call or a committed cached
response, and the CACHED badges are on screen and honest.

Recording: 1440×900, 100% zoom, light theme, Chrome, bookmarks bar hidden.

**Measured on prod, 29 Aug** — the page is faster than you'll expect, so don't rush the
pauses: the hero verdict lands **3.6s** after load with no click, `/try` shows the attack
buttons **1.8s** after you click Run, and each attack resolves in **0.6s**. The silence
after a refusal is doing work. Let it sit.

---

## Beats

| Time | Screen | Say this |
|---|---|---|
| 0:00 | `/` on load. Headline and the stat rail. Don't scroll yet. | *Surgeons stop before every incision and confirm the patient, the site, the procedure. Complications fell from eleven percent to seven when that checklist arrived. Thirteen thousand US med spas inject neurotoxin with no equivalent.* |
| 0:12 | Scroll to the card. It's already running. | *And when their malpractice cases reach a verdict, the leading causes aren't bad hands — they're absent consent, unexplained risk, unsupervised delegates. Paperwork failures, every one before the needle.* |
| 0:20 | Red band: **BLOCKED · DO NOT PROCEED**. Hover the failed facts. | *Time-Out is that pause. This synthetic encounter is an aesthetician booked to inject in Texas with no delegation evidence. It names the exact facts that failed and cites the rule.* |
| 0:32 | Point at **Snapshot** hash, then **Remedy**. | *Frozen with the exact ruleset it used. A person attaches what's missing and re-runs it. Nobody edits a database.* |
| 0:40 | Click **Try to break it →** | *Now try to get an unsafe procedure through.* |
| 0:46 | `/try` → **Run the complete safety workflow** → attacks appear | *This is the real backend. Each button takes the complete, valid evidence set and breaks exactly one thing.* |
| 0:54 | **Swap in the aesthetician** → red **TIME OUT** | *A job title is never an answer. Texas requires documented delegation.* |
| 1:02 | **Use the FDA-flagged lot** → **TIME OUT** | *A confirmed product alert stops it.* |
| 1:08 | **Skip the teach-back** → **TIME OUT** | *They signed. That isn't enough. Teach-back means saying the risks back in your own words.* |
| 1:16 | Scroll to the audit log — your three attempts, **Judge:** as actor | *Every attempt you just made is in the log, with you as the actor.* |
| 1:24 | **Reset** → **CLEAR** | *Complete evidence, all seven pass.* |
| 1:30 | Click through to `/receipt` | *This is what the patient leaves with.* |
| 1:36 | Scroll: seven checks → **skin baseline**, overlays, scores | *A standardized skin baseline captured before treatment. Twelve scored concerns. Skin analysis normally sells a treatment; here it runs once, before anything, and the record belongs to the patient.* |
| 1:48 | **PUBLISHED RECORD** — TXT read-back matched | *The receipt's fingerprint is published as a DNS record on the clinic's own domain, and read back through the name.com API.* |
| 1:56 | Click **Check this receipt's status now** → **STILL VALID** | *And this is the part I'd point at. A receipt says the checks passed on the day. If an FDA alert lands next week, the patient is holding paper that quietly stopped being true.* |
| 2:08 | Stay on the result. Point at the `_status` record. | *So every receipt carries a second record — its status — on the clinic's domain. Confirm an alert and it flips to REVOKED, with the reason. A missing record reads UNKNOWN, never valid. Absence is not validity.* |
| 2:22 | Scroll to **MEDICAL DIRECTOR ATTESTATION — SIGNED BY A NAMED HUMAN** | *An agent assembled this record through the Foxit MCP server, watermarked every page, and stopped. A named human signed it. The agent read the outcome back with GET requests only — it can never sign anything.* |
| 2:34 | `/how-it-works` → **Fetch a live verdict and re-hash it** → **REPRODUCED** | *Your browser just hashed the ruleset itself and matched the server, byte for byte. You don't have to take our word for it.* |
| 2:46 | `/` → scroll to **What this is not** | *It does not determine legality. It does not certify that a treatment is safe. Every clinic, patient, face and lot here is synthetic — no clinic has used this yet, and that's the next step, not a feature.* |
| 2:56 | End card: URL + repo | https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io · github.com/usv240/time-out |

---

## Rules for the take

- **Say the limits out loud** (2:46). Bounding your own claims is why the rest is believed.
- **Never say "first", "nobody else", or "determines legality."** The copy on screen already avoids it — match it.
- The red band is 2 seconds of screen time. It detonates on its own; don't linger.
- If a live call is slow, wait. The badge says LIVE and the wait is honest.
- One take is fine. Two is better. Pick the calmer one.
- **Do not read the nine-tool list aloud.** Showing two tools doing real work beats naming nine.

## Before you record — checklist

- [ ] `python -m tests.smoke_live` → **34/34**. If anything fails, fix it before recording.
- [ ] Hard-refresh each page once (Ctrl+Shift+R) so nothing serves from cache mid-take
- [ ] `/receipt.html` → **Check this receipt's status now** returns **STILL VALID**
- [ ] Browser 100% zoom, light theme, 1440×900, bookmarks bar hidden, notifications off
- [ ] Screen recorder tested for 10 seconds
- [ ] Close anything you would not want in a public gallery

## Per-sponsor cut notes (same master, if a challenge wants a shorter clip)

| Sponsor | Clip | Runs |
|---|---|---|
| Xano | 0:12–0:40 + 1:16–1:30 | ~0:40 — live Gate, cited refusal, audit log |
| name.com | 1:48–2:22 | ~0:35 — published record, then the revocation channel |
| Foxit | 2:22–2:34 | ~0:12 — agent assembles, stops, human signs, GET-only read-back |
| Perfect Corp | 1:36–1:48 + 2:46–2:56 | ~0:22 — baseline on the patient's receipt, limits stated (master is ≤3:00, so it also complies whole) |
| SerpApi | 1:02–1:08 + 1:56–2:22 | ~0:32 — flagged lot, and a confirmed alert revoking a receipt |
| Nutrient | 0:20–0:40 | ~0:20 — typed evidence, confidence routing, cited refusal |
| Doctavian | — | Not demonstrable; the write-up states why, honestly |

## If you have 4:00 instead of 3:00

Only two challenges cap at 3:00. If you cut a longer version for the rest, the extra
minute is best spent on:

1. `/try` → the **SerpApi live search** button (a real FDA query, on screen) — 20s
2. The **Nutrient** step: a field below the confidence floor boxed on its source page — 20s
3. The **"Could this be a company"** section: who buys it, and what it replaces — 20s

Record the 3:00 master first. The longer cut is a bonus, not the deliverable.
