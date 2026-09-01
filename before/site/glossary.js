// Plain-English definitions, attached to the first time each term appears on a page.
//
// The site was written by someone who had spent weeks inside Texas delegation law, and
// it showed: "neurotoxin", "delegation", "teach-back", "attestation" and "BLS" all
// arrived undefined. A judge is not a clinician and is not required to become one to
// follow the argument.
//
// Only the first occurrence per page is marked, so the prose stays readable rather
// than turning into a field of dotted underlines.

const TERMS = {
  "neurotoxin": "The injectable that relaxes a muscle to soften a line. Botox is the best-known brand.",
  "med spa": "A clinic selling cosmetic procedures. Often no doctor is on the premises while they happen.",
  "med spas": "Clinics selling cosmetic procedures. Often no doctor is on the premises while they happen.",
  "aesthetician": "A licensed skincare professional. Not a nurse and not a doctor, which is why who may inject is a real question.",
  "delegation": "A doctor formally handing a procedure to someone else, in writing, with conditions attached. Texas law turns on whether that paperwork exists.",
  "delegated": "Performed by someone the doctor formally handed the procedure to, in writing, with conditions attached.",
  "teach-back": "Asking the patient to say the risks back in their own words. It tests understanding; a signature only records that someone clicked.",
  "BLS": "Basic Life Support. Current CPR-level training, so somebody in the room can act if the patient reacts badly.",
  "attestation": "A named person signing to say they checked the record, and taking responsibility for that.",
  "Medical Director": "The doctor who is legally answerable for what happens at the clinic.",
  "rule snapshot": "A frozen copy of the exact rules used for one decision, so it can be re-checked years later even after the rules change.",
  "product lot": "The batch number printed on the vial. It is how a specific batch gets traced, or recalled.",
  "SHA-256": "A fingerprint of a file. Change one character anywhere and the fingerprint changes completely, so tampering shows.",
  "TXT record": "A short public note attached to a web domain. Anyone can look it up without an account.",
  "22 TAC": "Title 22 of the Texas Administrative Code: the rules governing medical practice in Texas.",
  "PHI": "Protected Health Information. Anything that identifies a real patient.",
  "MCP": "Model Context Protocol. A standard way for an AI agent to call tools rather than improvising HTTP requests.",
  "idempotent": "Doing it twice has the same effect as doing it once, so a retry cannot duplicate anything.",
  "WebCrypto": "Cryptography built into your browser, so the check runs on your machine rather than on our word.",
};

// Never mark text inside these: it is either code, already interactive, or a control.
const SKIP = new Set(["CODE", "PRE", "A", "BUTTON", "SCRIPT", "STYLE", "TEXTAREA",
                      "OPTION", "SELECT", "SUMMARY", "H1", "TITLE"]);

function defineTerms(root = document.querySelector("main")) {
  if (!root) return;
  const seen = new Set();
  // Longest first, so "med spas" wins over "med spa" and "product lot" over "lot".
  const ordered = Object.keys(TERMS).sort((a, b) => b.length - a.length);

  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      for (let el = node.parentElement; el && el !== root; el = el.parentElement) {
        if (SKIP.has(el.tagName) || el.classList.contains("term")) return NodeFilter.FILTER_REJECT;
      }
      return NodeFilter.FILTER_ACCEPT;
    },
  });

  const targets = [];
  while (walker.nextNode()) targets.push(walker.currentNode);

  for (const node of targets) {
    for (const term of ordered) {
      // Singular and plural are the same idea, so marking both is noise.
      const concept = term.replace(/s$/, "");
      if (seen.has(concept)) continue;
      // Case-sensitive for acronyms, insensitive for ordinary words.
      const acronym = term === term.toUpperCase();
      const pattern = new RegExp(`\\b${term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}\\b`,
                                 acronym ? "" : "i");
      const match = pattern.exec(node.nodeValue);
      if (!match) continue;

      const after = node.splitText(match.index);
      after.nodeValue = after.nodeValue.slice(match[0].length);
      const mark = document.createElement("span");
      mark.className = "term";
      mark.tabIndex = 0;
      mark.setAttribute("role", "button");
      mark.setAttribute("aria-label", `${match[0]}: ${TERMS[term]}`);
      mark.textContent = match[0];
      mark.append(Object.assign(document.createElement("span"),
        { className: "term-def", textContent: TERMS[term] }));
      after.parentNode.insertBefore(mark, after);
      seen.add(concept);
      break;   // one term per text node keeps the walk simple and the prose calm
    }
  }
}

// A dotted underline only helps if the reader knows to try it. Say so once, at the top
// of the page, and remember that they have been told.
const HINT_KEY = "timeout-glossary-hint";
function offerHint() {
  if (document.querySelector(".glossary-hint")) return;
  if (!document.querySelector(".term")) return;
  try { if (localStorage.getItem(HINT_KEY) === "seen") return; } catch { /* private mode */ }

  const hint = document.createElement("aside");
  hint.className = "glossary-hint";
  hint.innerHTML = '<span><strong>New to this?</strong> Words with a dotted underline, ' +
    'like <span class="term-sample">this</span>, have a plain-English definition. ' +
    'Hover over one, or tap it on a phone.</span>' +
    '<button type="button" class="glossary-hint-x" aria-label="Dismiss this tip">Got it</button>';

  const hero = document.querySelector(".page-hero, .receipt-header, main > section, main");
  (hero && hero.parentNode ? hero.parentNode : document.body)
    .insertBefore(hint, hero ? hero.nextSibling : null);

  hint.querySelector(".glossary-hint-x").addEventListener("click", () => {
    hint.remove();
    try { localStorage.setItem(HINT_KEY, "seen"); } catch { /* nothing to do */ }
  });
}

// Re-run when the console renders its results, so live output gets definitions too.
document.addEventListener("DOMContentLoaded", () => { defineTerms(); offerHint(); });
window.addEventListener("timeout:rendered", () => { defineTerms(); offerHint(); });

// A phone has no hover, so a tap opens the definition and a tap elsewhere closes it.
document.addEventListener("click", (e) => {
  const term = e.target.closest(".term");
  for (const open of document.querySelectorAll(".term.is-open")) {
    if (open !== term) open.classList.remove("is-open");
  }
  if (term) { term.classList.toggle("is-open"); e.stopPropagation(); }
});
document.addEventListener("keydown", (e) => {
  if (e.key === "Escape") {
    for (const open of document.querySelectorAll(".term.is-open")) open.classList.remove("is-open");
  }
  const term = e.target.closest?.(".term");
  if (term && (e.key === "Enter" || e.key === " ")) {
    e.preventDefault();
    term.classList.toggle("is-open");
  }
});
