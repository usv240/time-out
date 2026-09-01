# Demo video script — Time-Out

**Target: 2 minutes 50 seconds.** The overall rules ask for 1–3 minutes; three sponsor
tracks ask for 2–4. 2:50 is the only window that satisfies every one of them.

Judging is on three things: **Progress**, **Concept** (does it solve a real problem),
and **Feasibility** (could this be a company). Each gets its own beat below, marked.

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

Timings are cumulative. Narration is what you say out loud; everything in brackets is
what you do.

### 0:00 – 0:20 · The hook  →  *Concept*

**On screen:** `/` landing page, top of the hero. Don't move the mouse yet.

> Before any surgery, the whole team stops and says out loud: right patient, right
> place, right procedure. It's called a time-out. When hospitals started doing it,
> complications dropped from eleven percent to seven.
>
> Med spas don't do this. There are thirteen thousand of them in the US, injecting
> Botox thousands of times a day.

### 0:20 – 0:34 · Why it matters  →  *Concept*

**On screen:** scroll slowly to the "Med spas are among the fastest-growing venues"
section.

> And when one of those goes wrong and ends up in court, the cause usually isn't a
> shaky hand. It's paperwork. Nobody took proper consent. Nobody checked whether the
> person holding the needle was allowed to.
>
> So I built the pause.

### 0:34 – 0:52 · The check runs  →  *Progress*

**On screen:** scroll to the encounter card. Pause on the patient line.

> Here's a patient booked for an injection today. Everything you'll see is invented —
> there's no real person anywhere in this project.
>
> Before it can go ahead, seven things have to be true.

**[Let the check run.]**

> About a second. Blocked.

### 0:52 – 1:14 · Why blocking well is the whole product  →  *Concept*

**On screen:** the red BLOCKED card. Move the cursor down the four "not documented"
rows as you say them, then rest it on the citation.

> And look at what it actually says. Not "error." Not "denied."
>
> It names the four documents that are missing. It cites the Texas rule it's applying.
> And it tells the clinic exactly how to fix it.
>
> That's the difference between software that stops you and software that helps you.

### 1:14 – 1:44 · Break it yourself  →  *Progress*

**On screen:** `/try.html`, scrolled to the attack buttons.

> Now don't take my word for it. Break it.
>
> Each of these takes the complete, valid record, breaks exactly one thing, and runs
> the whole check again. Live.

**[Click "Swap in the aesthetician." Wait for BLOCKED.]**

> A job title isn't permission.

**[Click "Use the FDA-flagged lot." Wait.]**
**[Click "Skip the teach-back." Wait.]**

> Every attempt is written to the audit log, with whoever tried it named as the actor.

### 1:44 – 1:56 · Your data, not mine  →  *Progress*

**On screen:** scroll to "Or compose your own encounter."

> And if you don't trust my six examples — here's every single field. Set it however
> you want and run it yourself.

### 1:56 – 2:16 · What the patient gets  →  *Concept*

**On screen:** `/receipt.html`. Scroll slowly through it.

> When everything does check out, this is what the patient walks out holding.
>
> What was checked. Who was responsible. A photo baseline of their skin from before
> the treatment. And a fingerprint of the exact rules used that day, published where
> anyone can look it up.

**[Click "Verify the receipt against DNS now."]**

> So in two years, anyone can prove this record wasn't quietly rewritten.

### 2:16 – 2:38 · How it's built  →  *Progress*

**On screen:** `/how-it-works.html` at the top, then scroll once.

> One rule shapes all of it. The software never decides what's legal.
>
> AI reads the documents. Ordinary code checks them against a written rule. Anything
> unclear goes to a named human. No model ever gets to guess.
>
> Xano is the whole backend. Nutrient reads the documents. SerpApi watches FDA
> warnings. Perfect Corp captures the skin baseline. Doctavian writes the consent.
> Foxit assembles the record and a real person signs it. And name.com publishes the
> proof.

### 2:38 – 2:50 · Close  →  *Feasibility*

**On screen:** back to `/`, hero visible.

> Insurers and defence lawyers already pay for this — after somebody gets hurt.
> Before is cheaper than after.
>
> Ninety-four tests, all of it public, every patient in it invented.
>
> It's live right now. Go and try to break it.

---

## If you have to cut to 2:00

Drop these two beats and nothing else. They're the least load-bearing:

- **1:44 – 1:56** (compose your own) — the attack buttons already made the point.
- **2:16 – 2:38** — replace the seven-sponsor list with one line:
  *"Seven APIs behind it, each doing the one job nothing else could."*

Do **not** cut 0:52–1:14. The blocked card explaining itself is the single most
persuasive twenty seconds in the video.

---

## Word-for-word narration, no stage directions

For reading straight through if you'd rather not glance at a script while recording.
About 400 words, which is 2:50 at a relaxed pace.

> Before any surgery, the whole team stops and says out loud: right patient, right
> place, right procedure. It's called a time-out. When hospitals started doing it,
> complications dropped from eleven percent to seven.
>
> Med spas don't do this. There are thirteen thousand of them in the US, injecting
> Botox thousands of times a day.
>
> And when one of those goes wrong and ends up in court, the cause usually isn't a
> shaky hand. It's paperwork. Nobody took proper consent. Nobody checked whether the
> person holding the needle was allowed to.
>
> So I built the pause.
>
> Here's a patient booked for an injection today. Everything you'll see is invented —
> there's no real person anywhere in this project. Before it can go ahead, seven
> things have to be true.
>
> About a second. Blocked.
>
> And look at what it actually says. Not "error." Not "denied." It names the four
> documents that are missing. It cites the Texas rule it's applying. And it tells the
> clinic exactly how to fix it. That's the difference between software that stops you
> and software that helps you.
>
> Now don't take my word for it. Break it. Each of these takes the complete, valid
> record, breaks exactly one thing, and runs the whole check again. Live.
>
> A job title isn't permission.
>
> Every attempt is written to the audit log, with whoever tried it named as the actor.
>
> And if you don't trust my six examples — here's every single field. Set it however
> you want and run it yourself.
>
> When everything does check out, this is what the patient walks out holding. What was
> checked. Who was responsible. A photo baseline of their skin from before the
> treatment. And a fingerprint of the exact rules used that day, published where anyone
> can look it up. So in two years, anyone can prove this record wasn't quietly
> rewritten.
>
> One rule shapes all of it. The software never decides what's legal. AI reads the
> documents. Ordinary code checks them against a written rule. Anything unclear goes to
> a named human. No model ever gets to guess.
>
> Xano is the whole backend. Nutrient reads the documents. SerpApi watches FDA
> warnings. Perfect Corp captures the skin baseline. Doctavian writes the consent.
> Foxit assembles the record and a real person signs it. And name.com publishes the
> proof.
>
> Insurers and defence lawyers already pay for this — after somebody gets hurt. Before
> is cheaper than after.
>
> Ninety-four tests, all of it public, every patient in it invented.
>
> It's live right now. Go and try to break it.

---

## Every claim in the script, and where it comes from

| Claim | Source |
|---|---|
| 11% → 7% complications | Haynes et al., NEJM 2009, cited on the landing page |
| ~13,000 US med spas | cited on `/evidence` |
| Malpractice causes are consent, risk communication, delegate liability | cited on `/evidence` |
| Four documents missing | the four `not documented` rows on the BLOCKED card |
| Attacks are live calls | `/try` says LIVE · Xano on each one |
| Every attempt audited | the audit log section on `/try` |
| 94 tests | `pytest tests` |
| Everything synthetic | stated on every page |

Nothing in the script is a claim the site doesn't already carry a source for. Keep it
that way if you rewrite a line.
