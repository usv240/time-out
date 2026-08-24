const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";
const DEMO_DECISION_URL = `${XANO_API_BASE}/v1/encounters/demo/evaluate`;
const THEME_ORDER = ["system", "light", "dark"];

const runButton = document.querySelector("#run-check");
const actionPanel = document.querySelector("#evaluation-action");
const resultPanel = document.querySelector("#blocked-result");
const afterCopy = document.querySelector("#after-copy");
const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");

function statusLabel(status) { return status === "BLOCK" ? "FAIL" : status; }
function statusClass(status) { return status === "BLOCK" ? "is-fail" : status === "REVIEW" ? "is-review" : "is-pass"; }
function statusIcon(status) { return status === "BLOCK" ? "×" : status === "REVIEW" ? "…" : "✓"; }
function humanizeFact(key) { return key.replaceAll("_", " "); }
function factValue(value) {
  if (value === true) return "documented";
  if (value === false) return "not documented";
  if (value === null) return "not recorded";
  return String(value);
}

function populateBlockedResult(decision) {
  const primaryFailure = decision.findings.find((finding) => finding.check_id === "delegation_and_supervision");
  const factsToShow = ["delegation_document_present", "patient_specific_order_present", "protocol_signed_and_dated", "supervisor_immediately_available"];
  document.querySelector("#blocked-summary").textContent = primaryFailure.summary;
  const facts = document.querySelector("#failed-facts");
  facts.replaceChildren();
  for (const key of factsToShow) {
    const wrapper = document.createElement("div");
    const term = document.createElement("dt");
    const description = document.createElement("dd");
    term.textContent = humanizeFact(key);
    description.textContent = factValue(primaryFailure.facts[key]);
    wrapper.append(term, description);
    facts.append(wrapper);
  }
  const citation = document.querySelector("#blocked-citation");
  citation.href = primaryFailure.citation_urls[0];
  document.querySelector("#snapshot-hash").textContent = decision.rule_snapshot_sha256;
}

async function runEvaluation() {
  runButton.disabled = true;
  runButton.textContent = "Evaluating evidence…";
  try {
    const response = await fetch(DEMO_DECISION_URL, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}", cache: "no-store" });
    if (!response.ok) throw new Error(`Demo response returned ${response.status}`);
    const decision = await response.json();
    const interval = prefersReducedMotion.matches ? 0 : 150;
    for (const [index, finding] of decision.findings.entries()) {
      const row = document.querySelector(`[data-check="${finding.check_id}"]`);
      if (!row) continue;
      if (interval) await new Promise((resolve) => window.setTimeout(resolve, index === 0 ? 80 : interval));
      row.classList.add(statusClass(finding.status));
      row.querySelector(".check-icon").textContent = statusIcon(finding.status);
      row.querySelector(".check-status").textContent = statusLabel(finding.status);
    }
    populateBlockedResult(decision);
    actionPanel.hidden = true;
    resultPanel.hidden = false;
    afterCopy.hidden = false;
    resultPanel.focus({ preventScroll: true });
  } catch (error) {
    runButton.disabled = false;
    runButton.textContent = "Retry the safety check";
    actionPanel.querySelector("p").textContent = "The recorded evaluator response could not be loaded. Start a local server and retry.";
    console.error(error);
  }
}
runButton.addEventListener("click", runEvaluation);
document.querySelector("#reset-demo").addEventListener("click", () => {
  for (const row of document.querySelectorAll(".check-row")) {
    row.classList.remove("is-pass", "is-review", "is-fail");
    row.querySelector(".check-icon").textContent = "○";
    row.querySelector(".check-status").textContent = "WAITING";
  }
  resultPanel.hidden = true;
  afterCopy.hidden = true;
  actionPanel.hidden = false;
  runButton.disabled = false;
  runButton.textContent = "Run the safety check";
});

for (const button of document.querySelectorAll(".info-button")) {
  button.addEventListener("click", () => {
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    const willOpen = panel.hidden;
    for (const otherButton of document.querySelectorAll(".info-button")) {
      document.getElementById(otherButton.getAttribute("aria-controls")).hidden = true;
      otherButton.setAttribute("aria-expanded", "false");
    }
    panel.hidden = !willOpen;
    button.setAttribute("aria-expanded", String(willOpen));
  });
}
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const openButton = document.querySelector('.info-button[aria-expanded="true"]');
  if (!openButton) return;
  document.getElementById(openButton.getAttribute("aria-controls")).hidden = true;
  openButton.setAttribute("aria-expanded", "false");
  openButton.focus();
});

const themeButton = document.querySelector("#theme-toggle");
function currentTheme() { return localStorage.getItem("before-theme") || "system"; }
function renderThemeButton(theme) {
  themeButton.setAttribute("aria-label", `Theme: ${theme}. Activate for next theme.`);
  themeButton.title = `Theme: ${theme}`;
  themeButton.querySelector("span").textContent = theme === "light" ? "☀" : theme === "dark" ? "☾" : "◐";
}
function setTheme(theme) {
  if (theme === "system") {
    document.documentElement.removeAttribute("data-theme");
    localStorage.removeItem("before-theme");
  } else {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("before-theme", theme);
  }
  renderThemeButton(theme);
}
themeButton.addEventListener("click", () => {
  const nextIndex = (THEME_ORDER.indexOf(currentTheme()) + 1) % THEME_ORDER.length;
  setTheme(THEME_ORDER[nextIndex]);
});
renderThemeButton(currentTheme());

const menuButton = document.querySelector("#menu-toggle");
const navLinks = document.querySelector("#nav-links");
menuButton.addEventListener("click", () => {
  const open = menuButton.getAttribute("aria-expanded") !== "true";
  menuButton.setAttribute("aria-expanded", String(open));
  menuButton.setAttribute("aria-label", open ? "Close menu" : "Open menu");
  navLinks.classList.toggle("is-open", open);
});
for (const link of navLinks.querySelectorAll("a")) {
  link.addEventListener("click", () => {
    menuButton.setAttribute("aria-expanded", "false");
    menuButton.setAttribute("aria-label", "Open menu");
    navLinks.classList.remove("is-open");
  });
}
