const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";
const API_BASE = ["localhost", "127.0.0.1"].includes(location.hostname) ? "" : XANO_API_BASE;
const list = document.querySelector("#encounter-list");
const timeline = document.querySelector("#timeline");
const runPath = document.querySelector("#run-path");
const errorBox = document.querySelector("#console-error");
const receiptLink = document.querySelector("#receipt-link");
const consolePanel = document.querySelector("#console-panel");

const STEP_COPY = {
  blocked: ["Gate blocks the encounter", "Missing authority and pre-procedure evidence produces a deterministic hold."],
  gate_clear: ["Human remediation clears the Gate", "A Medical Director supplies the documented delegation, order, protocol, BLS, and supervision evidence."],
  nutrient_review: ["Nutrient routes low confidence", "Required extraction uncertainty goes to a named Medical Director with source coordinates."],
  gate_clear_after_review: ["Gate reruns after review", "The documented human resolution is evaluated against the same frozen rules."],
  consent: ["Doctavian compiles treatment consent", "The template branches on verified inputs and records patient plus injector signatures."],
  teach_back_held: ["Teach-back holds the encounter", "A wrong answer triggers re-explanation and a named Injector review task."],
  teach_back_passed: ["Teach-back passes on retry", "Versioned answers are bound to the frozen rule snapshot."],
  baseline: ["Perfect Corp captures the SD baseline", "Returned concern scores and masks document the starting point; they are not diagnosis."],
  foxit_pause: ["Foxit assembly stops for a human", "Reversible evidence assembly ends at the Medical Director signature boundary."],
  human_attestation: ["Medical Director attests", "A licensed human completes the irreversible eSign action."],
  alert_reversion: ["SerpApi candidate reopens review", "A prepared encounter moves backward; search data makes no conclusion."],
  alert_dismissed: ["Human dismisses the candidate", "The named reviewer records the decision and the encounter becomes ready again."],
  receipt: ["Receipt is sealed and read back", "The exact receipt hash is checked locally and through the name.com sandbox API."],
};

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
}

function pillFor(step, result) {
  if (result?.verdict === "BLOCKED" || step === "teach_back_held") return ["BLOCKED", "blocked"];
  if (step.includes("review") || step === "alert_reversion" || step === "foxit_pause") return ["REVIEW", "review"];
  if (result?.verdict === "CLEAR" || step === "receipt") return [step === "receipt" ? "SEALED" : "CLEAR", "clear"];
  return ["RECORDED", ""];
}

function baselineProof(result) {
  const scores = Object.entries(result.concerns || {}).sort((a, b) => a[0].localeCompare(b[0]));
  const scoreGrid = scores.map(([name, score]) => `<div class="score-row"><span>${escapeHtml(name.replaceAll("_", " "))}</span><meter min="0" max="100" value="${Number(score)}">${Number(score)}</meter><code>${Number(score)}</code></div>`).join("");
  return `<section class="perfect-proof" aria-label="Perfect Corp baseline evidence">
    <div class="baseline-portrait"><img src="${escapeHtml(result.image_ref)}" alt="Newly generated fictional adult used for the synthetic baseline"><img class="analysis-mask" src="${escapeHtml(result.overlay_ref)}" alt=""></div>
    <div class="baseline-data"><p class="integration-kicker">PERFECT CORP / SD SKIN ANALYSIS</p><div class="metric-pair"><div><span>Overall</span><strong>${Number(result.overall_score).toFixed(1)}</strong></div><div><span>Synthetic skin age</span><strong>${escapeHtml(result.skin_age)}</strong></div></div><div class="score-grid">${scoreGrid}</div><p class="capture-guidance"><strong>Capture contract:</strong> frontal face, even diffuse light, hair clear of the face, neutral expression. Reframe and retry if the detector rejects the image. VTO is intentionally not used in this hero path.</p><p class="evidence-boundary">${escapeHtml(result.boundary)}</p></div>
  </section>`;
}

function dnsProof(result) {
  const dns = result.dns_verification || {};
  const status = dns.matches ? "TXT READ-BACK MATCHED" : "TXT NOT VERIFIED";
  const stateClass = dns.matches ? "dns-match" : "dns-unverified";
  return `<section class="dns-proof ${stateClass}" aria-label="name.com receipt verification"><div><p class="integration-kicker">NAME.COM CORE SANDBOX</p><strong>${status}</strong></div><code>${escapeHtml(dns.txt_name)}<br>${escapeHtml(dns.txt_value)}</code><p>${escapeHtml(dns.caveat)}</p></section>`;
}

function renderEncounters(items) {
  list.replaceChildren();
  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-current", item.id === "SYN-ENC-BLOCKED-002" ? "true" : "false");
    button.innerHTML = `${escapeHtml(item.patient_display_name)}<small>${escapeHtml(item.id)} / ${escapeHtml(item.state)}</small>`;
    list.append(button);
  }
}

function renderTimeline(items) {
  timeline.replaceChildren();
  items.forEach((item, index) => {
    const [title, description] = STEP_COPY[item.step] || [item.step, "Recorded workflow evidence."];
    const [pill, className] = pillFor(item.step, item.result);
    const row = document.createElement("li");
    row.className = "timeline-item";
    const specialized = item.step === "baseline" ? baselineProof(item.result) : item.step === "receipt" ? dnsProof(item.result) : "";
    const detail = escapeHtml(JSON.stringify(item.result, null, 2));
    row.innerHTML = `<span class="timeline-index">${index + 1}</span><div><h3>${escapeHtml(title)}</h3><p>${escapeHtml(description)}</p></div><span class="status-pill ${className}">${pill}</span>${specialized}<details class="machine-evidence"><summary>Machine evidence</summary><pre class="timeline-detail">${detail}</pre></details>`;
    timeline.append(row);
  });
}

runPath.addEventListener("click", async () => {
  runPath.disabled = true;
  runPath.textContent = "Running the complete workflow...";
  timeline.replaceChildren();
  receiptLink.hidden = true;
  errorBox.hidden = true;
  try {
    const response = await fetch(`${API_BASE}/v1/demo/run`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error?.message || "Workflow failed.");
    renderTimeline(payload.timeline || []);
    const encounter = payload.encounter || {};
    renderEncounters([{ id: encounter.id, patient_display_name: encounter.patient_display_name || "Synthetic patient", state: encounter.state }]);
    const receipt = (payload.timeline || []).find((item) => item.step === "receipt")?.result;
    if (receipt) {
      receiptLink.href = `/receipt/${encodeURIComponent(receipt.receipt_id)}`;
      receiptLink.hidden = false;
    }
  } catch (error) {
    errorBox.textContent = `${error.message} Retry the synthetic workflow.`;
    errorBox.hidden = false;
  } finally {
    runPath.disabled = false;
    runPath.textContent = "Run the complete safety workflow again";
  }
});

const density = document.querySelector("#density");
density.value = localStorage.getItem("before-density") || "comfortable";
consolePanel.classList.toggle("compact", density.value === "compact");
density.addEventListener("change", () => {
  localStorage.setItem("before-density", density.value);
  consolePanel.classList.toggle("compact", density.value === "compact");
});

renderEncounters([{ id: "SYN-ENC-BLOCKED-002", patient_display_name: "Synthetic patient", state: "READY TO RUN" }]);
