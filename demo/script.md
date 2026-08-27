# Time-Out — demo script (≤ 3:00)

One master cut, ≤ 3:00, satisfies every sponsor's length rule (Perfect Corp caps at
3:00; the others allow 4:00). Screen recording only, no talking head, captions burned
in. **Record with the network on** — every step on the hosted site is either a live
Xano call or a committed cached response, so nothing can fail mid-take; the
"CACHED · recorded 26 Aug" badges are visible and honest.

Recording: 1440×900, 100% zoom, light theme, Chrome, `Win+G` or OBS. Speak the
captions or leave them silent — the words on screen carry it.

---

## Beats

| Time | Screen | Caption (say it or show it) |
|---|---|---|
| 0:00 | `/` hero, cursor on **Run the safety check** | *Surgeons pause before every incision to confirm the patient, the site, and the procedure. It cuts complications by a third. Med spas don't do it.* |
| 0:12 | Click. Checks resolve one by one. Red band: **BLOCKED** | *Time-Out is that pause. This synthetic encounter is an aesthetician booked to inject neurotoxin in Texas — with no delegation evidence on file.* |
| 0:22 | Hover the failed finding: facts in mono, **source** link | *Every refusal names the exact fact that failed and cites the rule. Nothing about the patient is judged — only the record.* |
| 0:30 | Scroll to **LIVE · Xano** badge, then the **audit log** | *That ran live on the backend. Every transition is an audit event. Nobody edits a database.* |
| 0:40 | `/try`. Timeline step: **Nutrient routes low confidence** | *Documents are read into typed fields with confidence scores. A field below the floor goes to a named Medical Director before anything irreversible.* |
| 0:50 | Step: **SerpApi candidate reopens review** | *A live search found the actual FDA warning letter from April. A ready encounter goes back to review. Search never decides — a person confirms or dismisses, and that's audited.* |
| 1:02 | Step: **Doctavian compiles consent** → **Both parties sign** | *One consent template branches on who is performing the procedure and loops over the cited disclosures. Patient and injector sign.* |
| 1:12 | Step: **Teach-back holds** → **passes on retry** | *A signature proves someone clicked. Teach-back proves they understood. The first wrong answer holds the encounter.* |
| 1:22 | Step: **Perfect Corp baseline** — face, overlays, scores, skin age | *A standardized skin baseline, captured before treatment. Twelve scored concerns and overlays — the patient's own record. A baseline, never a diagnosis.* |
| 1:34 | Step: **Foxit agent assembles, then stops** — tool-call trace, SHA, `folderId` | *An agent assembled the record through the Foxit MCP server, watermarked every page SYNTHETIC, and stopped. The Medical Director's attestation is a human eSign — the agent never signs.* |
| 1:46 | Step: **Receipt sealed** — **TXT READ-BACK MATCHED** | *The receipt's fingerprint is published as a DNS record on name.com and read back through the API. The patient can verify it without trusting us.* |
| 1:54 | Click **Open the patient receipt** → `/receipt` — checks, baseline, published record, *What this proves* | *This is what the patient leaves with. And what it does not claim: not legality, not safety, not authenticity, not outcome.* |
| 2:06 | `/how-it-works` → **Fetch a live verdict and re-hash it** → **REPRODUCED** | *Every verdict ships with the exact ruleset it used. Your browser just hashed it and it matches the server, byte for byte.* |
| 2:18 | Back to `/try` → **Break it yourself**. Click **Use the FDA-flagged lot** → red **TIME OUT** | *Now try to get an unsafe procedure through. Each button breaks exactly one thing and re-runs the checks — live.* |
| 2:28 | Click **Skip the teach-back** → **TIME OUT** | *They signed. That isn't enough.* |
| 2:36 | Click **Swap in the aesthetician** → **TIME OUT**, citation visible | *A job title is never an answer. Texas requires documented delegation.* |
| 2:44 | Scroll to the audit log — the three attempts, **Judge:** as actor | *Every attempt you just made is in the log, with you as the actor.* |
| 2:50 | Click **Reset** → **CLEAR** | *Complete evidence, every check passes.* |
| 2:54 | Cut to `/` hero, still | *A signature proves someone clicked. Time-Out proves the right person, product, rules, understanding, and evidence were present — before the needle.* |
| 3:00 | End card: URL + repo | https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io · github.com/usv240/time-out |

---

## Rules for the take

- **Say the limits out loud** (1:54). Judges trust teams that bound their own claims.
- **Never say "first," "nobody else," or "determines legality."** The copy on screen already avoids it; match it.
- The red band appears only on BLOCKED / TIME OUT. Don't linger on it — 2 seconds is enough; it detonates on its own.
- If a live call is slow, wait — don't cut. The badge says LIVE; the wait is honest.
- One take is fine. Two is better. Pick the calmer one.

## Per-sponsor cut notes (same master, if a sponsor page wants a shorter clip)

| Sponsor | Clip | Runs |
|---|---|---|
| Xano | 0:12–0:40 + 2:18–2:50 | ~1:00 — the live Gate, the audit log, the attacks |
| Nutrient | 0:40–0:50 + 1:54–2:06 | ~0:25 — confidence routing, bounded receipt |
| SerpApi | 0:50–1:02 + 2:18–2:28 | ~0:25 — live alert reopening review; flagged lot |
| Perfect Corp | 1:22–1:34 + 1:54–2:06 | ~0:25 — baseline on the patient's receipt (≤3:00 master also complies) |
| name.com | 1:46–2:06 | ~0:20 — TXT published and read back, limits stated |
| Doctavian | 1:02–1:12 | ~0:10 — branching consent, two signers (+ honest status in the write-up) |
| Foxit | 1:34–1:46 | ~0:12 — agent trace, the pause, eSign handoff |

## Before you record — the checklist (Aug 31)

- [ ] `https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io/` loads; click **Run** once to warm the sandbox
- [ ] `/try` → Run → six attack buttons appear; try one; **Reset** returns CLEAR
- [ ] `/receipt.html` shows the face with overlays and **TXT READ-BACK MATCHED**
- [ ] `/how-it-works` → verifier returns **REPRODUCED**
- [ ] Browser at 100% zoom, light theme, 1440×900, bookmarks bar hidden
- [ ] Screen recorder tested for 10 seconds; audio optional
- [ ] Tell me **go** — I'll send the eSign attestation email to `ujwalsureshv@gmail.com` so you can show the signature request landing if you want the extra beat (optional; the draft folder is already on screen at 1:34)
