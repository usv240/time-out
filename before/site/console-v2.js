// Clinic console.
// LIVE  = a real call to the Xano backend from this browser (per-visitor encounter).
// CACHED = a sponsor response recorded live on 2026-08-26 and replayed here so the
//          demo never depends on a third-party API answering at the moment a judge clicks.

const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";
const API_BASE = ["localhost", "127.0.0.1"].includes(location.hostname) ? "" : XANO_API_BASE;
const V1 = `${API_BASE}/v1`;

const list = document.querySelector("#encounter-list");
const timeline = document.querySelector("#timeline");
const runPath = document.querySelector("#run-path");
const errorBox = document.querySelector("#console-error");
const receiptLink = document.querySelector("#receipt-link");
const consolePanel = document.querySelector("#console-panel");
const auditPanel = document.querySelector("#audit-events");
const auditMeta = document.querySelector("#audit-meta");
const attackGrid = document.querySelector("#attack-grid");
const attackResult = document.querySelector("#attack-result");
const attackReset = document.querySelector("#attack-reset");

let liveEncounterId = null;
let heroTimeline = null;
let foxitRun = null;
let esignFolder = null;
let tamperCompare = null;

const STEP_COPY = {
  blocked: ["Gate blocks the encounter", "Missing authority and pre-procedure evidence produces a deterministic hold."],
  gate_clear: ["Human remediation clears the Gate", "A Medical Director supplies the documented delegation, order, protocol, BLS, and supervision evidence."],
  nutrient_review: ["Nutrient routes low confidence", "Required extraction uncertainty goes to a named Medical Director with source coordinates."],
  gate_clear_after_review: ["Gate reruns after review", "The documented human resolution is evaluated against the same frozen rules."],
  consent: ["Doctavian compiles treatment consent", "The template branches and loops over verified inputs, then pauses with both signatures pending."],
  consent_signed: ["Both treatment parties sign", "Patient plus Injector completion recorded; the Medical Director attestation stays a separate Foxit event."],
  teach_back_held: ["Teach-back holds the encounter", "A wrong answer triggers re-explanation and a named Injector review task."],
  teach_back_passed: ["Teach-back passes on retry", "Versioned answers are bound to the frozen rule snapshot."],
  baseline: ["Perfect Corp captures the baseline", "Returned concern scores and masks document the starting point. Not a diagnosis."],
  foxit_pause: ["Foxit agent assembles, then stops", "Reversible assembly through the MCP server ends at the human-signature boundary."],
  human_attestation: ["Medical Director attests", "A licensed human completes the irreversible eSign action."],
  alert_reversion: ["SerpApi candidate reopens review", "A prepared encounter moves backward. Search data makes no conclusion."],
  alert_dismissed: ["Human dismisses the candidate", "The named reviewer records the decision and the encounter becomes ready again."],
  receipt: ["Receipt is sealed and read back", "The receipt hash is published to name.com and read back through the sandbox API."],
};

// WHAT / WHY / SOURCE for the `i` buttons. Every entry must cite something real.
const INFO = {
  blocked: ["The seven checks ran on a fresh synthetic encounter and at least one failed.", "A failed check means the evidence to proceed safely is not on file. Nothing about the patient is judged; only the record.", "Texas Medical Board 22 TAC §169.25; Tex. Occ. Code §157.001"],
  gate_clear: ["A person attached the missing evidence and re-ran the same checks.", "Remediation is a human act with a name on it, never a database edit.", "Audit event: remediation_applied (below)"],
  nutrient_review: ["A required extracted field fell below the confidence floor.", "Uncertain evidence is shown to a named person before an irreversible step, not after.", "Nutrient DWS Data Extraction — per-element confidence and page coordinates"],
  gate_clear_after_review: ["The reviewer's resolution was recorded and the Gate ran again.", "Same rules, same snapshot, one more fact on file.", "Frozen rule snapshot SHA-256 (unchanged between runs)"],
  consent: ["One template branched on the authority pathway and looped over cited disclosures.", "Consent that changes shape with who is performing the procedure cannot be a static form.", "Doctavian expressions + elements; nothing uncited enters the document"],
  consent_signed: ["Patient and injector signed the treatment consent.", "Two treatment-party signatures are required before a baseline is captured.", "Doctavian signature record"],
  teach_back_held: ["The patient answered a risk question incorrectly.", "A signature proves someone clicked. Teach-back checks they understood.", "Systematic review, PubMed 31948345"],
  teach_back_passed: ["After re-explanation, the patient answered correctly.", "Attempts are recorded, not hidden, and versioned to the ruleset.", "Comprehension record bound to rule_snapshot_sha256"],
  baseline: ["A standardized skin analysis captured concern scores and overlays.", "An objective starting point the patient keeps. It is never a diagnosis.", "Perfect Corp YouCam Skin Analysis (SD), synthetic face"],
  foxit_pause: ["An agent assembled the record through the Foxit MCP server and stopped.", "The agent does reversible work; a licensed person takes the irreversible step.", "Foxit PDF Services + eSign draft folder (below)"],
  human_attestation: ["The Medical Director's attestation was requested through eSign.", "Only a named human can apply this signature.", "Foxit eSign folder — created as a draft, sent on a person's command"],
  alert_reversion: ["A live search surfaced an FDA warning letter matching the product context.", "New public information can reopen a ready encounter. That is the point of a hold.", "SerpApi → fda.gov warning letter, April 2026"],
  alert_dismissed: ["A named reviewer examined the candidate and dismissed it.", "Search results never decide anything; people do, and the decision is audited.", "Audit event: alert_candidate_dismissed"],
  receipt: ["The record was hashed and the hash published as a DNS TXT record.", "Anyone holding the receipt can check it matches what was published.", "name.com CORE sandbox — non-propagating, owner-mutable; a verification channel, not a notary"],
};

// The complete, valid evidence set for a delegated RN in Texas. Every attack below is this set
// with exactly one thing broken, so the judge sees which single fact the Gate refused on.
const CLEARED = {
  credential_type: "RN", training_documented: true, complication_training: true,
  delegation_agreement_id: "SYN-DELEG-001", protocol_id: "SYN-PROTO-001", delegating_physician_active: true,
  patient_specific_order_present: true, order_contains_drug_dose_strength_route: true, bls_current: true,
  supervisor_onsite: true, supervisor_immediately_available: true, physician_emergency_appointment_available: true,
  patient_flags: [], practitioner_patient_relationship_established: true, adequate_medical_record_present: true,
  performer_identity_disclosed: true, product_lot_no: "INVENTED-LOT-0007",
  product_alert_status: "MATCHED_TO_NO_CAPTURED_ALERT", comprehension_passed: true, comprehension_score: 100,
  actor: "Judge (synthetic session)",
};

const ATTACKS = [
  { id: "title", label: "Swap in the aesthetician", claim: "“A job title should be enough.”",
    patch: { credential_type: "AESTHETICIAN", training_documented: false, complication_training: false, delegation_agreement_id: "", protocol_id: "", delegating_physician_active: false } },
  { id: "delegation", label: "Delete the delegation protocol", claim: "“The paperwork is somewhere.”",
    patch: { delegation_agreement_id: "", protocol_id: "", delegating_physician_active: false } },
  { id: "order", label: "Skip the patient-specific order", claim: "“Same dose as always.”",
    patch: { patient_specific_order_present: false, order_contains_drug_dose_strength_route: false } },
  { id: "lot", label: "Use the FDA-flagged lot", claim: "“It came from a supplier.”",
    patch: { product_lot_no: "FLAGGED-LOT-2026", product_alert_status: "CONFIRMED_ALERT" } },
  { id: "teachback", label: "Skip the teach-back", claim: "“They signed, that’s enough.”",
    patch: { comprehension_passed: false, comprehension_score: 40 } },
  { id: "bls", label: "Let BLS lapse, supervisor off-site", claim: "“Nothing ever goes wrong.”",
    patch: { bls_current: false, supervisor_onsite: false, supervisor_immediately_available: false, physician_emergency_appointment_available: false } },
];

const MASK_FILES = new Set(["acne", "droopy_lower_eyelid", "droopy_upper_eyelid", "eye_bag", "firmness", "moisture", "oiliness", "pore", "radiance", "redness", "texture", "wrinkle"]);
function maskSrc(ref) {
  if (!ref) return null;
  if (String(ref).includes("/")) return ref;                       // already a path
  return MASK_FILES.has(ref) ? `/assets/perfectcorp/synthetic-patient-02-${ref}-overlay.png` : null;
}

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
}

function info(key) {
  const entry = INFO[key];
  if (!entry) return "";
  const [what, why, source] = entry;
  const id = `info-${key}`;
  return `<button class="info-btn" type="button" aria-expanded="false" aria-controls="${id}" aria-label="Explain this step">i</button>
    <div class="info-pop" id="${id}" hidden><p><b>What</b> ${escapeHtml(what)}</p><p><b>Why</b> ${escapeHtml(why)}</p><p><b>Source</b> <code>${escapeHtml(source)}</code></p></div>`;
}

function badge(kind) {
  return kind === "live"
    ? `<span class="src-badge live" title="Real call to the Xano backend from this browser">LIVE · Xano</span>`
    : `<span class="src-badge cached" title="Recorded live on 2026-08-26 and replayed">CACHED · recorded 2026-08-26</span>`;
}

function pillFor(step, result) {
  if (result?.verdict === "BLOCKED" || step === "teach_back_held") return ["BLOCKED", "blocked"];
  if (step.includes("review") || step === "consent" || step === "alert_reversion" || step === "foxit_pause") return ["REVIEW", "review"];
  if (step === "consent_signed") return ["SIGNED", "clear"];
  if (result?.verdict === "CLEAR" || step === "receipt") return [step === "receipt" ? "SEALED" : "CLEAR", "clear"];
  return ["RECORDED", ""];
}

function findingsTable(result) {
  const findings = result?.findings || [];
  if (!findings.length) return "";
  const rows = findings.map((f) => {
    const cls = f.status === "PASS" ? "clear" : f.status === "REVIEW" ? "review" : "blocked";
    const facts = Object.entries(f.facts || {}).map(([k, v]) => `<code>${escapeHtml(k)}=${escapeHtml(JSON.stringify(v))}</code>`).join(" ");
    const cite = (f.citation_urls || []).map((u) => `<a href="${escapeHtml(u)}" target="_blank" rel="noopener">source</a>`).join(" ");
    return `<tr class="finding ${cls}"><td><code>${escapeHtml(f.check_id)}</code></td><td><span class="status-pill ${cls}">${escapeHtml(f.status)}</span></td><td>${escapeHtml(f.summary)}<div class="facts">${facts}</div></td><td>${cite}</td></tr>`;
  }).join("");
  return `<table class="findings"><thead><tr><th>Check</th><th>Result</th><th>What was found</th><th>Cited</th></tr></thead><tbody>${rows}</tbody></table>`;
}


function nutrientProof(result) {
  const conf = Object.entries(result.confidence || {});
  const low = conf.filter(([, v]) => String(v).toUpperCase() === "LOW").map(([k]) => k);
  const rows = conf.map(([field, level]) => {
    const cls = String(level).toUpperCase() === "LOW" ? "blocked" : String(level).toUpperCase() === "MEDIUM" ? "review" : "clear";
    return `<tr class="finding ${cls}"><td><code>${escapeHtml(field)}</code></td><td><span class="status-pill ${cls}">${escapeHtml(level)}</span></td><td>${escapeHtml(String((result.fields || {})[field] ?? ""))}</td></tr>`;
  }).join("");
  return `<section class="nutrient-proof" aria-label="Nutrient extraction review">
    <p class="integration-kicker">NUTRIENT DWS / EXTRACTION REVIEW</p>
    <div class="nutrient-split">
      <figure><img src="/assets/nutrient/low-confidence-lot.png" alt="Source document with the low-confidence lot field outlined"><figcaption>The source page, with <code>${escapeHtml(low.join(", ") || "the uncertain field")}</code> boxed at the coordinates DWS returned.</figcaption></figure>
      <div><table class="findings"><thead><tr><th>Field</th><th>Confidence</th><th>Extracted</th></tr></thead><tbody>${rows}</tbody></table>
      <p class="evidence-boundary">Routed to <strong>${escapeHtml(result.assigned_role || "a named reviewer")}</strong>. The encounter cannot advance until a person confirms it. The confidence floor lives in code, never in a prompt.</p></div>
    </div>
  </section>`;
}

function baselineProof(result) {
  const scores = Object.entries(result.concerns || {}).sort((a, b) => a[0].localeCompare(b[0]));
  const scoreGrid = scores.map(([name, score]) => `<div class="score-row"><span>${escapeHtml(name.replaceAll("_", " "))}</span><meter min="0" max="100" value="${Number(score)}">${Number(score)}</meter><code>${Number(score)}</code></div>`).join("");
  const masks = (result.mask_refs || []).map(maskSrc).filter(Boolean).map((m) => `<img class="analysis-mask" src="${escapeHtml(m)}" alt="">`).join("");
  return `<section class="perfect-proof" aria-label="Perfect Corp baseline evidence">
    <div class="baseline-portrait"><img src="${escapeHtml(result.image_ref)}" alt="AI-generated fictional adult used for the synthetic baseline">${masks || `<img class="analysis-mask" src="${escapeHtml(result.overlay_ref)}" alt="">`}</div>
    <div class="baseline-data"><p class="integration-kicker">PERFECT CORP / SD SKIN ANALYSIS</p><div class="metric-pair"><div><span>Overall</span><strong>${Number(result.overall_score).toFixed(1)}</strong></div><div><span>Synthetic skin age</span><strong>${escapeHtml(result.skin_age)}</strong></div></div><div class="score-grid">${scoreGrid}</div><p class="capture-guidance"><strong>Capture contract:</strong> frontal face, even light, hair clear of the face, neutral expression, ~1024px wide. Larger images are rejected by the detector.</p><p class="evidence-boundary">${escapeHtml(result.boundary)}</p></div>
  </section>`;
}

function dnsProof(result) {
  const dns = result.dns_verification || {};
  const status = dns.matches ? "TXT READ-BACK MATCHED" : "TXT NOT VERIFIED";
  const stateClass = dns.matches ? "dns-match" : "dns-unverified";
  return `<section class="dns-proof ${stateClass}" aria-label="name.com receipt verification"><div><p class="integration-kicker">NAME.COM CORE SANDBOX</p><strong>${status}</strong></div><code>${escapeHtml(dns.txt_name || dns.fqdn)}<br>${escapeHtml(dns.txt_value)}</code><p>${escapeHtml(dns.caveat)}</p></section>`;
}

function foxitProof() {
  if (!foxitRun) return "";
  const calls = (foxitRun.calls || []).map((c) => {
    const rest = c.tool.startsWith("REST");
    return `<li><code>${escapeHtml(c.tool)}</code> <span class="ms">${c.ms} ms</span>${rest ? `<div class="why">${escapeHtml(c.args?.why || "")}</div>` : ""}</li>`;
  }).join("");
  const folder = esignFolder?.folder || {};
  return `<section class="foxit-proof" aria-label="Foxit agent trace">
    <p class="integration-kicker">FOXIT / MCP AGENT TRACE</p>
    <p class="prompt">Prompt: <code>${escapeHtml(foxitRun.prompt)}</code></p>
    <ol class="tool-calls">${calls}</ol>
    <p><strong>Output</strong> <code>${escapeHtml(foxitRun.output_pdf)}</code> · SHA-256 <code>${escapeHtml((foxitRun.output_sha256 || "").slice(0, 16))}…</code> · 3/3 pages watermarked</p>
    <p class="boundary"><strong>Paused at the boundary.</strong> ${escapeHtml(foxitRun.boundary_note)}</p>
    ${tamperCompare ? `<div class="tamper-proof"><p class="integration-kicker">TAMPER CHECK — FOXIT PDF-COMPARE</p><p>We altered one line of the sealed record and asked Foxit to compare the two. It found ${tamperCompare.differences.length} difference on page ${tamperCompare.differences[0]?.page} of ${tamperCompare.pages_compared} — the attestation page: <code>${escapeHtml(tamperCompare.differences[0]?.text || "")}</code></p><p class="muted">The receipt fingerprint catches any change; this shows a reviewer <em>where</em> it happened.</p></div>` : ""}
    <p><strong>eSign handoff</strong> — envelope <code>${escapeHtml(folder.folderId)}</code> for the ${escapeHtml(esignFolder?.signer_role || "Medical Director")}: <em>${escapeHtml(esignFolder?.mode || "")}</em>. Sending is a human choice; the default emails nobody.</p>
  </section>`;
}

function renderEncounters(items) {
  list.replaceChildren();
  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-current", "true");
    button.innerHTML = `${escapeHtml(item.patient_display_name)}<small>${escapeHtml(item.id)} / ${escapeHtml(item.state)}</small>`;
    list.append(button);
  }
}

function renderTimeline(items, liveIndexes = new Set([0])) {
  timeline.replaceChildren();
  items.forEach((item, index) => {
    const [title, description] = STEP_COPY[item.step] || [item.step, "Recorded workflow evidence."];
    const [pill, className] = pillFor(item.step, item.result);
    const row = document.createElement("li");
    row.className = "timeline-item";
    let specialized = "";
    if (item.step === "baseline") specialized = baselineProof(item.result);
    else if (item.step === "nutrient_review") specialized = nutrientProof(item.result);
    else if (item.step === "receipt") specialized = dnsProof(item.result);
    else if (item.step === "foxit_pause") specialized = foxitProof();
    else if (item.result?.findings) specialized = findingsTable(item.result);
    const detail = escapeHtml(JSON.stringify(item.result, null, 2));
    row.innerHTML = `<span class="timeline-index">${index + 1}</span><div><h3>${escapeHtml(title)} ${info(item.step)}</h3><p>${escapeHtml(description)}</p>${badge(liveIndexes.has(index) ? "live" : "cached")}</div><span class="status-pill ${className}">${pill}</span>${specialized}<details class="machine-evidence"><summary>Machine evidence</summary><pre class="timeline-detail">${detail}</pre></details>`;
    timeline.append(row);
  });
}

async function renderAudit(encounterId) {
  if (!auditPanel) return;
  try {
    const response = await fetch(`${V1}/encounters/${encodeURIComponent(encounterId)}`);
    const payload = await response.json();
    const events = payload.audit_events || [];
    auditMeta.textContent = `${events.length} events · ${badgeText("live")} · encounter ${encounterId}`;
    auditPanel.replaceChildren();
    for (const ev of events) {
      const li = document.createElement("li");
      const when = ev.created_at ? new Date(ev.created_at).toISOString().replace("T", " ").slice(0, 19) : "";
      li.innerHTML = `<code>${escapeHtml(when)}</code> <strong>${escapeHtml(ev.actor)}</strong> ${escapeHtml(ev.action)} <span class="muted">${escapeHtml(ev.from_state || "")} → ${escapeHtml(ev.to_state || "")}</span>${ev.reason ? `<div class="muted">${escapeHtml(ev.reason)}</div>` : ""}`;
      auditPanel.append(li);
    }
  } catch (error) {
    auditMeta.textContent = `Audit log unavailable: ${error.message}`;
  }
}
function badgeText(kind) { return kind === "live" ? "LIVE · Xano" : "CACHED"; }

async function loadStatic() {
  const [hero, foxit, esign, tamper] = await Promise.all([
    fetch("/data/hero-timeline.json").then((r) => r.json()),
    fetch("/data/foxit-run.json").then((r) => r.json()).catch(() => null),
    fetch("/data/esign-folder.json").then((r) => r.json()).catch(() => null),
    fetch("/data/tamper-compare.json").then((r) => r.json()).catch(() => null),
  ]);
  heroTimeline = hero; foxitRun = foxit; esignFolder = esign; tamperCompare = tamper;
}

async function runHeroPath() {
  runPath.disabled = true;
  runPath.textContent = "Running the safety check…";
  timeline.replaceChildren();
  receiptLink.hidden = true;
  errorBox.hidden = true;
  try {
    if (!heroTimeline) await loadStatic();
    // Step 1 is LIVE: the Gate runs on Xano against a fresh per-visitor encounter.
    const response = await fetch(`${V1}/encounters/demo/evaluate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const live = await response.json();
    if (!response.ok) throw new Error(live.message || live.error?.message || "The live Gate call failed.");
    liveEncounterId = live.encounter_id;
    const steps = (heroTimeline.timeline || []).map((s, i) => (i === 0 ? { step: "blocked", result: live } : s));
    renderTimeline(steps, new Set([0]));
    renderEncounters([{ id: live.encounter_id, patient_display_name: "Synthetic patient", state: live.state }]);
    await renderAudit(live.encounter_id);
    const receipt = steps.find((item) => item.step === "receipt")?.result;
    if (receipt) { receiptLink.href = `/receipt.html?id=${encodeURIComponent(receipt.receipt_id)}`; receiptLink.hidden = false; }
    attackGrid.closest("section")?.removeAttribute("hidden");
  } catch (error) {
    errorBox.textContent = `${error.message} The synthetic Xano sandbox may be rate-limited; try again in a few seconds.`;
    errorBox.hidden = false;
  } finally {
    runPath.disabled = false;
    runPath.textContent = "Run the safety check again";
  }
}

// ---------------------------------------------------------------- Break it yourself

async function remediateAndEvaluate(patch, label) {
  const body = { ...CLEARED, ...patch, encounter_id: liveEncounterId, actor: `Judge: ${label}` };
  const r = await fetch(`${V1}/encounters/${encodeURIComponent(liveEncounterId)}/remediate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error((await r.json()).message || "remediate failed");
  const e = await fetch(`${V1}/encounters/${encodeURIComponent(liveEncounterId)}/evaluate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ encounter_id: liveEncounterId }) });
  const verdict = await e.json();
  if (!e.ok) throw new Error(verdict.message || "evaluate failed");
  return verdict;
}

function renderAttack(attack, verdict) {
  const failed = (verdict.findings || []).filter((f) => f.status !== "PASS");
  const cls = verdict.verdict === "CLEAR" ? "clear" : verdict.verdict === "REVIEW" ? "review" : "blocked";
  const headline = verdict.verdict === "BLOCKED" ? "TIME OUT — this encounter cannot proceed."
    : verdict.verdict === "REVIEW" ? "HOLD — a person has to decide." : "CLEAR — every check passed.";
  attackResult.className = `attack-result ${cls}`;
  attackResult.innerHTML = `<div class="attack-head"><span class="status-pill ${cls}">${escapeHtml(verdict.verdict)}</span> ${badge("live")}</div>
    <h3>${escapeHtml(headline)}</h3>
    <p class="muted">You tried: <strong>${escapeHtml(attack ? attack.label : "Reset to the complete evidence set")}</strong>${attack ? ` — ${escapeHtml(attack.claim)}` : ""}</p>
    ${failed.length ? findingsTable({ findings: failed }) : `<p>All seven checks passed on the complete evidence set.</p>`}
    <p class="muted">Rule snapshot <code>${escapeHtml((verdict.rule_snapshot_sha256 || "").slice(0, 16))}…</code> — the same frozen rules every time.</p>`;
  attackResult.hidden = false;
  attackResult.setAttribute("role", verdict.verdict === "BLOCKED" ? "alert" : "status");
}

function renderAttackGrid() {
  attackGrid.replaceChildren();
  for (const attack of ATTACKS) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "attack-btn";
    b.innerHTML = `<strong>${escapeHtml(attack.label)}</strong><small>${escapeHtml(attack.claim)}</small>`;
    b.addEventListener("click", async () => {
      if (!liveEncounterId) { errorBox.textContent = "Run the safety check first to open a synthetic encounter."; errorBox.hidden = false; return; }
      for (const btn of attackGrid.querySelectorAll("button")) btn.disabled = true;
      b.classList.add("busy");
      try { renderAttack(attack, await remediateAndEvaluate(attack.patch, attack.label)); await renderAudit(liveEncounterId); }
      catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
      finally { for (const btn of attackGrid.querySelectorAll("button")) btn.disabled = false; b.classList.remove("busy"); }
    });
    attackGrid.append(b);
  }
}

attackReset?.addEventListener("click", async () => {
  if (!liveEncounterId) return;
  attackReset.disabled = true;
  try { renderAttack(null, await remediateAndEvaluate({}, "reset")); await renderAudit(liveEncounterId); }
  catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
  finally { attackReset.disabled = false; }
});

// `i` buttons: click to open, Esc to close, focus returns to the trigger.
document.addEventListener("click", (event) => {
  const btn = event.target.closest(".info-btn");
  if (!btn) return;
  const pop = document.getElementById(btn.getAttribute("aria-controls"));
  const open = btn.getAttribute("aria-expanded") === "true";
  btn.setAttribute("aria-expanded", String(!open));
  pop.hidden = open;
});
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  for (const btn of document.querySelectorAll('.info-btn[aria-expanded="true"]')) {
    btn.setAttribute("aria-expanded", "false");
    document.getElementById(btn.getAttribute("aria-controls")).hidden = true;
    btn.focus();
  }
});

runPath.addEventListener("click", runHeroPath);

const density = document.querySelector("#density");
if (density) {
  density.value = localStorage.getItem("before-density") || "comfortable";
  consolePanel.classList.toggle("compact", density.value === "compact");
  density.addEventListener("change", () => {
    localStorage.setItem("before-density", density.value);
    consolePanel.classList.toggle("compact", density.value === "compact");
  });
}

renderEncounters([{ id: "new synthetic encounter", patient_display_name: "Synthetic patient", state: "READY TO RUN" }]);
renderAttackGrid();
loadStatic().catch(() => {});


// ---------------------------------------------------------------- live sponsor calls
const RECEIPT_DIGEST = "dbb4241ce3e278ee28ed887bd36967c4cb6a36a24039fd7f32d60fea8f6a83ab";

async function liveCall(button, out, path, body, render) {
  button.disabled = true; const label = button.textContent; button.textContent = "Calling…";
  out.hidden = false; out.className = "attack-result"; out.textContent = "Waiting for the sponsor API…";
  try {
    const r = await fetch(`${V1}${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const d = await r.json();
    if (!r.ok) throw new Error(d.message || "The sponsor API did not answer.");
    out.className = "attack-result clear"; out.innerHTML = render(d);
  } catch (e) {
    out.className = "attack-result review";
    out.innerHTML = `<p>${escapeHtml(e.message)}</p><p class="muted">The cached result recorded 26 Aug remains on this page — the demo never depends on a third party answering.</p>`;
  } finally { button.disabled = false; button.textContent = label; }
}

document.querySelector("#live-serp")?.addEventListener("click", (e) =>
  liveCall(e.target, document.querySelector("#live-serp-out"), "/live/serpapi-scan", {}, (d) => `
    <div class="attack-head"><span class="status-pill clear">${d.count} CANDIDATES</span> <span class="src-badge live">LIVE · SerpApi via Xano</span></div>
    <p class="muted">Query <code>${escapeHtml(d.query)}</code></p>
    <ul>${(d.candidates || []).map((c) => `<li><a href="${escapeHtml(c.source_url)}" target="_blank" rel="noopener">${escapeHtml(c.title)}</a></li>`).join("")}</ul>
    <p class="muted">${escapeHtml(d.boundary)}</p>`));

document.querySelector("#live-dns")?.addEventListener("click", (e) =>
  liveCall(e.target, document.querySelector("#live-dns-out"), "/live/receipt-verify", { digest: RECEIPT_DIGEST }, (d) => `
    <div class="attack-head"><span class="status-pill ${d.matches ? "clear" : "blocked"}">${d.matches ? "TXT MATCHED" : "NO MATCH"}</span> <span class="src-badge live">LIVE · name.com via Xano</span></div>
    <p><code>${escapeHtml(d.fqdn || "")}</code></p><p><code>${escapeHtml(d.answer || "")}</code></p>
    <p class="muted">${escapeHtml(d.caveat)}</p>`));
