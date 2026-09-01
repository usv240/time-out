// An "i" on every section heading: what this section is, and why it is here.
//
// The site explained its seven checks and nothing else. A judge who does not already
// know why a page contains a section called "Could this be a company" has to infer it
// from the prose, which is the thing they do not have time to read.
//
// Keyed by heading text rather than by id, because most sections have no id. A test
// asserts every heading on every page has an entry, so a reworded heading fails the
// suite instead of quietly losing its explanation.

const SECTIONS = {
  // ---- home ----
  "this encounter cannot produce a safety receipt": [
    "The result of running all seven checks on one invented patient.",
    "Three checks failed, so it refuses to issue a record at all rather than issuing a weak one.",
  ],
  "one encounter three kinds of proof": [
    "The same encounter shown three ways: as a decision, as a signed document, and as a public record anyone can look up.",
    "A single proof is just a claim. Three independent ones that agree are hard to fake.",
  ],
  "med spas are among the fastest-growing venues for medi": [
    "Why this gap exists: the industry grew far faster than the oversight did.",
    "If the problem is not real, nothing else on this page matters.",
  ],
  "a cited checklist that cannot be skipped": [
    "The seven checks, each shown with the specific rule it comes from.",
    "A checklist you can skip is a suggestion. This one refuses to produce the record.",
  ],
  "three synthetic encounters three outcomes": [
    "One that passes, one that is blocked, and one that needs a human to decide.",
    "A checker that only ever says yes has not been tested.",
  ],
  "call the gate from your own system": [
    "The same seven checks, reachable as a single web request.",
    "No clinic will retype anything into a second system, so it has to reach them inside the software they already use.",
  ],
  "everything here is inspectable": [
    "The code, the rules, the tests and the records are all public.",
    "Safety software that cannot be audited is asking for trust it has not earned.",
  ],
  "four people one record": [
    "What the patient, the injector, the doctor and the regulator each get from the same record.",
    "If it only helps one of them, nobody adopts it.",
  ],
  "somebody already pays for this badly and afterwards": [
    "Whether this could be a real business, and who would actually pay for it.",
    "Insurers and lawyers already spend heavily on this after someone is hurt. Before is cheaper.",
  ],
  "nine tools each one owns a handoff": [
    "Which product does what, at which step of the pipeline.",
    "Tools bolted on for show are obvious. Each of these owns a step that nothing else here does.",
  ],
  "we'd rather you trust the parts that work": [
    "What this does not do, and what would have to be true before a real clinic used it.",
    "If you are deciding whether to believe the rest of the page, this is the most useful section on it.",
  ],

  // ---- try ----
  "encounters": [
    "Three prepared cases you can run: one clean, one blocked, one needing a human.",
    "Start with one of these, then change it and see what moves.",
  ],
  "hero encounter": [
    "The seven checks running against the live backend right now, as you watch.",
    "This is not a recording. The verdict is computed when you press the button.",
  ],
  "try to get an unsafe procedure through": [
    "Six buttons, each removing exactly one thing the rules require.",
    "The interesting question is not whether it says yes. It is whether you can make it say yes when it should not.",
  ],
  "every artifact this pipeline reads and writes": [
    "The actual files behind the demo: evidence sets, skin analyses, consent PDFs, signed records.",
    "You can open them yourself instead of taking a screenshot's word for it.",
  ],
  "call the sponsor apis yourself": [
    "Each outside integration, callable on its own.",
    "So you can confirm each one really runs, rather than trusting a list of logos.",
  ],
  "every transition as xano recorded it": [
    "The audit log for this encounter: every state change, in order, with who caused it.",
    "A safety record that can be edited silently is not a safety record.",
  ],

  // ---- how it works ----
  "no black box and no short circuit": [
    "Exactly where the AI stops and ordinary code takes over.",
    "A model that decides legality can be talked into anything. Code following a written rule cannot.",
  ],
  "who uses it and how rules change": [
    "Who touches the system, and what happens when the law itself changes.",
    "Rules do change. A system that cannot be updated safely dies at the first amendment.",
  ],
  "canonical json sha-256 deterministic rerun": [
    "How one decision is frozen so it can be re-run identically years later.",
    "A record nobody can reproduce is worth nothing in a dispute.",
  ],
  "don't take our word for the hash": [
    "Your browser fetches a live verdict and recomputes the fingerprint itself.",
    "If our number and your number disagree, the right response is to stop trusting us.",
  ],

  // ---- api ----
  "evaluate the seeded encounter": [
    "A complete working request you can send right now, with no key.",
    "The fastest way to see what comes back before reading any documentation.",
  ],
  "use the same gate from any client": [
    "The identical call written in curl, JavaScript and Python.",
    "Copy whichever one matches what you already build in.",
  ],
  "request": [
    "Every field the endpoint accepts, and what each one means.",
    "So you can build a real request of your own rather than replaying ours.",
  ],
  "response": [
    "What comes back: the verdict, the seven findings, and the frozen rules used.",
    "The findings are the useful part. A bare yes or no gives a clinic nothing to fix.",
  ],
  "core encounter api": [
    "The rest of the endpoints: create an encounter, evaluate it, fix it, issue the receipt.",
    "The whole lifecycle, not only the check in the middle of it.",
  ],
  "no signup no key": [
    "Why this is open to anyone, and what that costs us.",
    "A key would make the demo unverifiable for everybody who did not stop to request one.",
  ],

  // ---- assumptions ----
  "what we assume and why": [
    "Every belief this design rests on, written out plainly.",
    "Unstated assumptions are how safety software fails quietly.",
  ],
  "cases the gate actually handles": [
    "The specific situations it was built for, each with the named test that proves it.",
    "“It handles edge cases” means nothing without the list.",
  ],
  "when something breaks": [
    "What happens when an outside service fails, or the data is missing or contradictory.",
    "How a system behaves when it is broken matters more than how it behaves when everything works.",
  ],
  "what we have not proven": [
    "The claims we cannot yet back with evidence.",
    "Saying this out loud costs less than being caught not saying it.",
  ],

  // ---- evidence ----
  "what each sponsor surface actually does here": [
    "Each product used, the step it owns, and the file where you can see it called.",
    "So “built with” is something you can check rather than a wall of logos.",
  ],
  "no absolute novelty claim": [
    "What already exists in this space, and how this differs from it.",
    "Claiming to be first is easy to disprove and unnecessary.",
  ],
};

// "One encounter. Three kinds of proof." and "one encounter three kinds of proof"
// should be the same key, so punctuation and case are dropped.
function key(text) {
  // Allow-list rather than a list of punctuation to strip: hyphens and apostrophes
  // are part of words here ("fastest-growing", "don't"), everything else is noise.
  return text.toLowerCase().replace(/[‘’]/g, "'")
             .replace(/[^a-z0-9'\- ]+/g, " ")
             .replace(/\s+/g, " ").trim().slice(0, 54);
}

// The heading's own words. Another script appending to it must not be able to break
// the lookup, which is exactly what happened when the glossary injected a definition.
function headingText(heading) {
  const clone = heading.cloneNode(true);
  for (const extra of clone.querySelectorAll(".term-def, .info-btn, .info-pop")) extra.remove();
  return clone.textContent;
}

function explainSections() {
  for (const heading of document.querySelectorAll("main h2")) {
    // "Where to go next" is generated by nav-guide.js and explains itself.
    if (heading.closest(".next-step")) continue;
    if (heading.querySelector(".info-btn")) continue;
    const entry = SECTIONS[key(headingText(heading))];
    if (!entry) continue;

    const id = `sec-info-${Math.random().toString(36).slice(2, 9)}`;
    const button = document.createElement("button");
    button.className = "info-btn";
    button.type = "button";
    button.setAttribute("aria-expanded", "false");
    button.setAttribute("aria-controls", id);
    button.setAttribute("aria-label", `What this section is: ${headingText(heading).trim()}`);
    button.textContent = "i";
    heading.append(" ", button);

    const pop = document.createElement("div");
    pop.className = "info-pop";
    pop.id = id;
    pop.hidden = true;
    pop.innerHTML = `<p><b>What</b> ${entry[0]}</p><p><b>Why</b> ${entry[1]}</p>`;
    heading.after(pop);
  }
}

// app.js, console-v2.js and receipt-v2.js already delegate hover, focus and
// click-to-pin from the document for any .info-btn. Binding a second copy here would
// toggle twice per click and cancel itself out, so those pages only get the buttons.
const HAS_HANDLER = 'script[src*="app.js"], script[src*="console-v2.js"], script[src*="receipt-v2.js"]';

function bindInfo() {
  if (document.querySelector(HAS_HANDLER)) return;

  const show = (btn) => {
    const pop = document.getElementById(btn.getAttribute("aria-controls"));
    if (!pop) return;
    pop.hidden = false;
    btn.setAttribute("aria-expanded", "true");
  };
  const hide = (btn, force) => {
    const pop = document.getElementById(btn.getAttribute("aria-controls"));
    if (!pop || (!force && btn.dataset.pinned === "true")) return;
    pop.hidden = true;
    btn.setAttribute("aria-expanded", "false");
  };

  document.addEventListener("pointerover", (e) => {
    const btn = e.target.closest(".info-btn"); if (btn) show(btn);
  });
  document.addEventListener("pointerout", (e) => {
    const btn = e.target.closest(".info-btn");
    if (btn && !btn.contains(e.relatedTarget)) hide(btn);
  });
  document.addEventListener("focusin", (e) => {
    const btn = e.target.closest(".info-btn"); if (btn) show(btn);
  });
  document.addEventListener("focusout", (e) => {
    const btn = e.target.closest(".info-btn"); if (btn) hide(btn);
  });
  // A pointer hovers before it clicks, so the panel is already open when the click
  // lands. Toggle the pin, not the visibility, or the click closes what it opened.
  document.addEventListener("click", (e) => {
    const btn = e.target.closest(".info-btn"); if (!btn) return;
    const pinned = btn.dataset.pinned === "true";
    btn.dataset.pinned = String(!pinned);
    if (pinned) hide(btn, true); else show(btn);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key !== "Escape") return;
    for (const btn of document.querySelectorAll('.info-btn[aria-expanded="true"]')) {
      btn.dataset.pinned = "false";
      hide(btn, true);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => { explainSections(); bindInfo(); });
window.addEventListener("timeout:rendered", explainSections);
