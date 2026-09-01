// Tell people where each link goes, and where to go next.
//
// The navigation named seven destinations and explained none of them. "Assumptions"
// and "Evidence" are indistinguishable if you do not already know what the site
// argues; "Receipt" sounds like billing. A judge with four minutes should not have to
// click all seven to find out which one answers their question.
//
// So every nav link carries what the page is and why you would open it, and every page
// ends by pointing at the two pages that follow from it. Nobody dead-ends.

const PAGES = {
  "/": {
    name: "Home",
    what: "The problem in one scroll: what goes wrong in med spas, and what a time-out is.",
    why: "Start here if you have not seen this before.",
  },
  "/try.html": {
    name: "Try it",
    what: "Run the safety check on an invented patient, then try to sneak an unsafe one past it.",
    why: "The fastest way to see what this actually does.",
  },
  "/receipt.html": {
    name: "Receipt",
    what: "The record the patient walks out holding, and how they can verify it themselves.",
    why: "See what the check produces for the person on the table.",
  },
  "/how-it-works.html": {
    name: "How it works",
    what: "The three steps behind a verdict, and the exact point where the AI stops and code takes over.",
    why: "Read this to decide whether the answer can be trusted.",
  },
  "/assumptions.html": {
    name: "Assumptions",
    what: "Every assumption the design rests on, each failure case, and the named test that pins it.",
    why: "No clinic has used this yet. This is the honest version of that sentence.",
  },
  "/api.html": {
    name: "API",
    what: "Call the same check from your own code in one request, with no key.",
    why: "For wiring it into booking software that already exists.",
  },
  "/evidence.html": {
    name: "Evidence",
    what: "The public source behind every number, rule and claim on this site.",
    why: "So you can check us instead of believing us.",
  },
};

// Where each page leads. Two options: the natural next step, and the sceptic's route.
const NEXT = {
  "/": ["/try.html", "/how-it-works.html"],
  "/try.html": ["/receipt.html", "/how-it-works.html"],
  "/receipt.html": ["/try.html", "/evidence.html"],
  "/how-it-works.html": ["/try.html", "/assumptions.html"],
  "/assumptions.html": ["/evidence.html", "/try.html"],
  "/api.html": ["/try.html", "/how-it-works.html"],
  "/evidence.html": ["/assumptions.html", "/try.html"],
};

function here() {
  const path = location.pathname.replace(/\/index\.html$/, "/");
  return PAGES[path] ? path : "/";
}

function annotateNav() {
  const current = here();
  let n = 0;
  for (const link of document.querySelectorAll(".nav-links a")) {
    const url = new URL(link.href, location.origin);
    // "Limits" is an anchor on the home page. Its pathname is "/", so without this it
    // claimed to be the current page on the home page and the real link never lit up.
    if (url.hash) continue;
    const key = url.pathname.replace(/\/index\.html$/, "/");
    const page = PAGES[key];
    if (!page || link.querySelector(".nav-hint")) continue;

    // Where am I. Without this the nav gives no sense of place at all.
    if (key === current) link.setAttribute("aria-current", "page");

    const hint = document.createElement("span");
    hint.className = "nav-hint";
    hint.id = `nav-hint-${++n}`;
    hint.innerHTML =
      `<span class="nav-hint-what"><b>What</b>${page.what}</span>` +
      `<span class="nav-hint-why"><b>Why</b>${page.why}</span>`;
    // The hint is described by, not part of, the link name: a screen reader should
    // still announce "Evidence", not the whole paragraph.
    link.setAttribute("aria-describedby", hint.id);
    link.append(hint);

    // A fixed 17rem card hung off the API link ran 90px past the right edge of a
    // 1280px window. Which side it opens on depends on where the link actually sits.
    const flip = () => {
      const r = link.getBoundingClientRect();
      hint.classList.toggle("nav-hint-right", r.left + 272 > window.innerWidth - 16);
    };
    link.addEventListener("mouseenter", flip);
    link.addEventListener("focus", flip);
  }
}

function offerNextStep() {
  const main = document.querySelector("main");
  if (!main || document.querySelector(".next-step")) return;
  const targets = (NEXT[here()] || []).filter((k) => PAGES[k]);
  if (!targets.length) return;

  const strip = document.createElement("section");
  strip.className = "next-step shell";
  strip.innerHTML =
    '<h2 class="next-step-title">Where to go next</h2><div class="next-step-cards">' +
    targets.map((key) => {
      const p = PAGES[key];
      return `<a class="next-step-card" href="${key}">
        <span class="next-step-name">${p.name}</span>
        <span class="next-step-what">${p.what}</span>
        <span class="next-step-why">${p.why}</span>
      </a>`;
    }).join("") +
    "</div>";
  main.append(strip);
}

document.addEventListener("DOMContentLoaded", () => { annotateNav(); offerNextStep(); });
