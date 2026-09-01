# Demo video script — Time-Out

**Target: 2:55 recorded runtime.** The overall rules ask for 1–3 minutes; three sponsor
tracks ask for 2–4. Just under three minutes is the only window that satisfies all of
them, and there is no margin above it — so a take that runs 3:01 has to be redone.

Runtime is narration plus silence, and the silence here was measured rather than
guessed. Every wait, timed twice on production:

| Wait | Measured |
|---|---|
| Fresh load of `/` to all seven rows resolved | ~2.0s (first row ~1.1s) |
| "Run the complete safety workflow" on `/try` | 0.5–0.7s |
| Each of the three attacks | 0.4–0.6s |
| "Check this receipt's status now" | ~0.1s to respond |
| **Total waiting on a server** | **about 3 seconds** |

So: 419 words at a relaxed 145 a minute is 2:53, plus ~3s of API waits, plus the one
deliberate pause. That lands at **2:55–3:00** — tight. Time your dry run end to end. If
it crosses 3:00, cut the beat at 1:44 (below), which buys back eight seconds and costs
nothing.

Judging is on three things: **Progress**, **Concept** (does it solve a real problem),
and **Feasibility** (could this be a company). Each beat below is marked with the one
it earns, so a rewrite can't quietly drop a criterion.

Record on the production site: https://timeout-prod-74602b-x6g0-xqak-a8ri.n7e.xano.io

---

## Before you record

- Browser at **1440px wide**, zoom 100%, light theme, bookmarks bar hidden.
- Dismiss the "New to this?" tip once so it isn't on screen in every shot.
- Open three tabs in this order: `/` · `/try.html` · `/receipt.html`
- Do one full dry run first. The attack buttons are live API calls; know how long
  they take on your connection so you aren't narrating into dead air.
- One take per section is fine. Cut between sections, not inside them.

**Delivery:** talk like you're showing this to a friend, not presenting to a panel.
Slow down on the numbers. The screen is doing the proving — you're just pointing.

---

## The script

Ten beats. Each one tells you **where to be**, **what to do**, **what to point at**,
and **what to say**. The words in `>` blocks are the narration and nothing else — say
those, do everything else silently.

Positions below are described by what you can see on screen, not pixel counts, because
dismissing the glossary tip shifts everything up by about 60px.

---

### Beat 1 · 0:00 – 0:20 · The hook  →  *Concept*

**Where:** tab 1, `/`. **Start the recording on a fresh page load** so nothing is
mid-animation.

**On screen:** the top of the page. You should see the eyebrow line
`TEXAS · NEUROTOXIN · SYNTHETIC DEMONSTRATION`, the headline **"Some treatments cannot
be undone."**, and the numbers column on the right.

**Point at:** nothing for the first sentence — let them read the headline. On "eleven
percent to seven", move the cursor to the **11% → 7%** figure in the right-hand column
and leave it there. On "thirteen thousand", drop it to **13,000** just below.

> Before any surgery, the team stops and confirms out loud: right patient, right place,
> right procedure. It's called a time-out. Complications dropped from eleven percent to
> seven.
>
> Med spas have no equivalent pause. Thirteen thousand of them in the US, injecting
> Botox thousands of times a day.

---

### Beat 2 · 0:20 – 0:34 · Why it matters  →  *Concept*

**Where:** same page, no navigation.

**Do:** scroll down slowly through the hero paragraph. Stop when the sentence
**"paperwork failures, every one of them before the needle"** is in the middle of the
screen. It is in bold, in the second half of the opening paragraph.

**Point at:** that bold phrase as you say "It's paperwork." Then move away — you are
about to change screens.

> And when one goes wrong in court, the cause usually isn't a shaky hand. It's
> paperwork. No proper consent. Nobody checked whether the person holding the needle
> was allowed to.
>
> So I built the pause.

---

### Beat 3 · 0:34 – 0:52 · The check runs  →  *Progress*

**Where:** same page. Keep scrolling — the encounter card is the next thing, about one
screen further down.

**On screen:** the white card headed `Encounter SYN-ENC-BLOCKED-002`, with
`Ava Chen · Neurotoxin · Austin, TX` under it, then a blue strip reading
**"Live call to Xano"**, then seven rows.

**Timed over five loads:** the rows start resolving about **1.1s** after the page
loads and the last one lands with the red panel at about **2.0s**. So there *is* a
visible run, and it is the best two seconds of the opening — the rows tick over one by
one while you speak.

You do not click anything to start it. The page evaluates on load, and the "Run the
safety check" button is gone about a second later. So the timing you want is: begin
your line as the page settles, and let the rows finish under your voice.

**Point at:** the patient line `Ava Chen · Neurotoxin · Austin, TX` on the first
sentence. Then draw the cursor slowly down the seven check rows — Provider licence,
Authority pathway, Delegation, Pre-procedure assessment, Product lot, Comprehension,
Disciplinary status — as you say "seven things have to be true". Land on the two red
`×` rows for the last line.

> Here's a patient booked for an injection today. Every person in this demo is
> invented. Before it can go ahead, seven things have to be true.
>
> About a second. Blocked.

---

### Beat 4 · 0:52 – 1:14 · Why blocking well is the whole product  →  *Concept*

**Where:** same page, scroll on so the red panel fills the screen.

**On screen:** the pink/red block headed **"BLOCKED · DO NOT PROCEED"** and
**"This encounter cannot produce a safety receipt."** Below it, four monospaced rows
each ending `not documented`, then `SOURCE  22 TAC Chapter 169`, then `SNAPSHOT` and a
long hash, then `REMEDY`.

**This is the most important twenty seconds in the video.** Your cursor is doing the
teaching here — move deliberately, one item per phrase.

**Point at, in this order:**

| As you say | Put the cursor on |
|---|---|
| "Not error. Not denied." | the words **BLOCKED · DO NOT PROCEED** |
| "the four documents that are missing" | run down all four `not documented` rows, one per beat |
| "It cites the Texas rule" | the link **22 TAC Chapter 169** |
| "tells the clinic exactly how to fix it" | the **REMEDY** line |

> And look at what it actually says. Not "error." Not "denied." It names the four
> documents that are missing. It cites the Texas rule it's applying. And it tells the
> clinic exactly how to fix it. That's the difference between software that stops you
> and software that helps you.

---

### Beat 5 · 1:14 – 1:44 · Break it yourself  →  *Progress*

**Where:** switch to tab 2, `/try.html`.

**Do this first, before you say anything.** The attack buttons **do not exist yet**.
Scroll down about half a screen to the big teal button **"Run the complete safety
workflow"** and click it. It answers in about half a second, and a new section headed
**"Try to get an unsafe procedure through."** appears below with six buttons in two
rows of three. Let that appear, then start talking.

**On screen after the click:** six buttons. Top row: *Swap in the aesthetician* /
*Delete the delegation protocol* / *Skip the patient-specific order*. Bottom row:
*Use the FDA-flagged lot* / *Skip the teach-back* / *Let BLS lapse, supervisor
off-site*.

**Know this before you click:** the answer appears **above** the buttons, and the
buttons shift down the page as it does. Don't chase the button with your cursor — after
each click, move up to the result panel instead. It is headed `BLOCKED`, with a
`LIVE · Xano` tag beside it and the line "You tried: ..." naming the attack you chose.

**Sequence, one at a time:**

1. Say the intro lines.
2. Click **Swap in the aesthetician**. Wait for BLOCKED. Point at the `LIVE · Xano`
   tag. Say the punchline.
3. Click **Use the FDA-flagged lot**. Wait. Point at the "You tried:" line so it is
   obvious the attack changed. Say the punchline.
4. Click **Skip the teach-back**. Wait. Say the punchline, then the audit-log line.

> Now don't take my word for it. Break it. Each of these takes the valid record, breaks
> one thing, and runs all seven checks again. Live.

**[Click "Swap in the aesthetician." Wait for BLOCKED.]**

> A job title isn't permission.

**[Click "Use the FDA-flagged lot." Wait.]**

> A flagged product stops it too.

**[Click "Skip the teach-back." Wait.]**

> And consent isn't a checkbox.
>
> Every attempt lands in the audit log, with whoever tried it named.

---

### Beat 6 · 1:44 – 1:52 · Your data, not mine  →  *Progress*

**Where:** same page, scroll down past the attack result.

**Do first:** the composer is **collapsed by default**. Click the line
**"Or compose your own encounter"** to expand it, then let it open before you speak.

**On screen once open:** a grid of five labelled groups (WHO IS PERFORMING IT, SUPERVISION AND THE ORDER, THE PRE-PROCEDURE
RECORD, THE PRODUCT, DID THE PATIENT UNDERSTAND) with checkboxes and dropdowns, and a
**"Run the Gate on my evidence"** button at the bottom.

**Point at:** sweep the cursor across the five groups. Don't click anything — there
isn't time, and the point is that the controls exist.

**If your dry run is over 3:00, this is the beat to cut.** It buys back eight seconds.

> Don't trust my examples? Every field is here. Change anything and run it yourself.

---

### Beat 7 · 1:52 – 2:10 · What the patient gets  →  *Concept*

**Where:** switch to tab 3, `/receipt.html`.

**Do:** scroll steadily from the top. You will pass, in this order: the header
**"Safety receipt"** with a `Synthetic` chip, the list of what was checked, the named
people, then a face image with **twelve scored skin concerns** beside it (Oiliness 64,
Pore visibility 68, and so on).

**Point at:** the checks list on "what was checked", the named people on "who was
responsible", the skin scores on "their skin baseline".

**Then:** keep scrolling to the button **"Check this receipt's status now"** — it is
roughly two-thirds down, in the section about the published record. Click it. It
responds in about a tenth of a second with *"Reading the clinic's DNS through
name.com"*. Point at the status line it returns while you say the last sentence.

> When everything checks out, this is what the patient walks out holding. What was
> checked, who was responsible, their skin baseline from before, and a fingerprint of
> the exact rules used that day.

**[Click "Check this receipt's status now."]**

> It's published outside Time-Out, so years later the patient can check the record
> hasn't silently changed.

---

### Beat 8 · 2:10 – 2:26 · How it's built  →  *Progress*

**Where:** navigate to `/how-it-works.html`.

**On screen:** start at the top — the headline **"Models extract. Humans resolve. Code
decides the hold."** says your first line before you do.

**Do:** scroll once, slowly, to the section headed **"No black box and no short
circuit."** Keep scrolling gently underneath it while you speak so the sponsor names
pass through the frame on their own.

**Point at:** nothing specific. This is the one beat where the cursor should rest. Let
the page move instead. **Do not read the sponsor names aloud** — the screen is showing
them, and seven proper nouns spoken in fifteen seconds is nothing anyone retains.

> One rule shapes the whole system. AI reads the evidence; it never decides what's
> legal. Code runs every check. Anything uncertain stops for a named human, and a live
> FDA warning can pull a cleared encounter back into review.
>
> Xano runs that workflow end to end. Seven other APIs handle the documents, consent,
> skin evidence, signing, and outside verification.

---

### Beat 9 · 2:26 – 2:44 · Who buys it  →  *Feasibility*

**Where:** back to tab 1, `/`. Scroll to the top so the headline is on screen again.

Returning to the opening image while you make the business case is deliberate: it ties
the money back to the problem the judge met ninety seconds ago.

**Point at:** nothing. Just talk. Slow down here — this is a third of the score, and it
is the part a rushed delivery ruins.

> The customer is the clinic, and this sits in front of every procedure they book.
>
> It starts narrow on purpose: Texas neurotoxin. Every new state or procedure is a
> rules file, not a rewrite.
>
> Today, insurers and defence lawyers deal with these failures after somebody has been
> hurt. Time-Out moves the check to the one moment it's still cheap to fix.
>
> Before the needle.

---

### Beat 10 · 2:44 – 2:55 · Close

**[One beat of silence. Count one, silently. That line is the positioning — don't run
into the next one.]**

**On screen:** stay on the hero. Move the cursor over the **"Try to break it →"**
button as you say the last line, but **don't click it.** Ending on a button the judge
could press is the invitation; pressing it yourself takes it away.

> It's live right now. The backend is real, the attacks are real. Go and try to break
> it.

---

## Quick reference: the whole run, one line each

Tape this next to your screen.

| # | Go | Do | Say |
|---|---|---|---|
| 1 | `/` fresh load | nothing | surgery has a time-out |
| 2 | scroll to bold "paperwork failures" | nothing | it's paperwork → so I built the pause |
| 3 | scroll to the encounter card | nothing; rows resolve over ~2s | seven things → blocked |
| 4 | scroll to the red panel | cursor down 4 rows, then citation, then remedy | not error, not denied |
| 5 | `/try.html` | **click "Run the complete safety workflow" first**, then 3 attacks | break it → 3 punchlines |
| 6 | scroll to the composer | **click it open**, sweep the five groups | every field is here |
| 7 | `/receipt.html` | scroll, then click "Check this receipt's status now" | what the patient holds |
| 8 | `/how-it-works.html` | scroll slowly, cursor still | AI reads, code decides |
| 9 | back to `/`, top | nothing | the customer is the clinic |
| 10 | hover "Try to break it →" | **don't click** | go and try to break it |

---

## If you have to cut to 2:00

Drop these two and nothing else:

- **1:44 – 1:52** (compose your own) — the attack buttons already made the point.
- **2:10 – 2:26** — compress to one line: *"AI reads the evidence. Code decides.
  Anything uncertain stops for a human. Seven APIs behind it, each doing the one job
  nothing else could."*

Do **not** cut 0:52–1:14 or 2:26–2:50. The first is the most persuasive twenty seconds
in the video; the second is the only place you answer "could this be a company," which
is a third of the score.

---

## Word-for-word narration, no stage directions

420 words. At a relaxed 145 words a minute that is 2:52, inside the three-minute cap.

> Before any surgery, the team stops and confirms out loud: right patient, right
> place, right procedure. It's called a time-out. Complications dropped from eleven
> percent to seven. Med spas have no equivalent pause. Thirteen thousand of them in
> the US, injecting Botox thousands of times a day. And when one goes wrong in court,
> the cause usually isn't a shaky hand. It's paperwork. No proper consent. Nobody
> checked whether the person holding the needle was allowed to. So I built the pause.
> Here's a patient booked for an injection today. Every person in this demo is
> invented. Before it can go ahead, seven things have to be true. About a second.
> Blocked. And look at what it actually says. Not "error." Not "denied." It names the
> four documents that are missing. It cites the Texas rule it's applying. And it tells
> the clinic exactly how to fix it. That's the difference between software that stops
> you and software that helps you. Now don't take my word for it. Break it. Each of
> these takes the valid record, breaks one thing, and runs all seven checks again.
> Live. A job title isn't permission. A flagged product stops it too. And consent
> isn't a checkbox. Every attempt lands in the audit log, with whoever tried it named.
> Don't trust my examples? Every field is here. Change anything and run it yourself.
> When everything checks out, this is what the patient walks out holding. What was
> checked, who was responsible, their skin baseline from before, and a fingerprint of
> the exact rules used that day. It's published outside Time-Out, so years later the
> patient can check the record hasn't silently changed. One rule shapes the whole
> system. AI reads the evidence; it never decides what's legal. Code runs every check.
> Anything uncertain stops for a named human, and a live FDA warning can pull a
> cleared encounter back into review. Xano runs that workflow end to end. Seven other
> APIs handle the documents, consent, skin evidence, signing, and outside
> verification.
>
> The customer is the clinic, and this sits in front of every procedure they book.
>
> It starts narrow on purpose: Texas neurotoxin. Every new state or procedure is a
> rules file, not a rewrite.
>
> Today, insurers and defence lawyers deal with these failures after somebody has been
> hurt. Time-Out moves the check to the one moment it's still cheap to fix.
>
> Before the needle.
>
> It's live right now. The backend is real, the attacks are real. Go and try to break
> it.

---

## The sentence a judge should be able to repeat afterwards

> Time-Out is a pre-procedure safety check for med spas. It catches missing evidence
> before the needle, tells the clinic how to fix it, and leaves the patient with a
> record they can verify.

If that's what they remember after one viewing, it landed.

---

## Every claim in the script, and where it comes from

| Claim | Source |
|---|---|
| 11% → 7% complications | Haynes et al., NEJM 2009, cited on the landing page |
| ~13,000 US med spas | cited on `/evidence` |
| "no equivalent pause" | the landing page says the same, and it is a claim about absence of a standard, not about any one clinic |
| Malpractice causes are consent, risk communication, delegate liability | cited on `/evidence` |
| Four documents missing | the four `not documented` rows on the BLOCKED card |
| Attacks are live calls | `/try` labels each one LIVE · Xano |
| Every attempt audited | the audit log section on `/try` |
| A live FDA warning reopens an encounter | the SerpApi alert path, described on `/how-it-works` |
| "check the record hasn't silently changed" | deliberately not "prove it wasn't rewritten": `/assumptions` says the receipt is a record, not a notary, and DNS is mutable by its owner |
| New states are a rules file | the ruleset is data, not code — `/how-it-works` |
| Everything synthetic | stated on every page |

Two things this script deliberately does **not** say:

- **No test count.** The README claimed 87 in three places and 94 in a fourth until
  today. Numbers that don't match across your own material cost more credibility than
  a big number buys. "The backend is real, the attacks are real" does the same work
  and can't be checked against a stale line. (For the record: 94 offline, 48 live.)
- **Nothing about what the receipt proves.** It shows a record hasn't changed. It does
  not certify the treatment was safe, and the script never implies it does.

Nothing here is a claim the site doesn't already carry a source for. Keep it that way
if you rewrite a line.
