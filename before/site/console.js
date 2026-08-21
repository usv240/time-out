const list = document.querySelector("#encounter-list");
const timeline = document.querySelector("#timeline");
const runPath = document.querySelector("#run-path");
const errorBox = document.querySelector("#console-error");
const receiptLink = document.querySelector("#receipt-link");
const consolePanel = document.querySelector("#console-panel");

const STEP_COPY = {
  blocked: ["Gate blocks the encounter", "Missing authority and pre-procedure evidence produces a deterministic hold."],
  gate_clear: ["Human remediation clears the Gate", "Medical Director reassigns to an RN and attaches delegation, order, protocol, BLS, and supervision evidence."],
  nutrient_review: ["Nutrient routes low confidence", "The extracted lot field goes to the Medical Director with page coordinates."],
  gate_clear_after_review: ["Gate reruns after review", "The source fixture remains unchanged; documented review evidence is attached."],
  consent: ["Doctavian compiles and signs consent", "The template branches on verified inputs and captures patient plus injector signatures."],
  teach_back_held: ["Teach-back holds the encounter", "A wrong answer triggers re-explanation and a named Injector review task."],
  teach_back_passed: ["Teach-back passes on retry", "The versioned answers are bound to the frozen rule snapshot."],
  baseline: ["Perfect Corp captures the SD baseline", "Standardized geometry, concern scores, and overlay are communication aids—not diagnosis."],
  foxit_pause: ["Foxit agent assembles, then stops", "Reversible record assembly ends at the human-signature boundary."],
  human_attestation: ["Medical Director attests", "A licensed human completes the irreversible eSign action."],
  alert_reversion: ["SerpApi candidate reopens review", "A prepared encounter moves backward; search data makes no conclusion."],
  alert_dismissed: ["Human dismisses the candidate", "The named reviewer records the decision and the encounter becomes ready again."],
  receipt: ["Receipt is sealed", "The bounded payload, rule snapshot, evidence references, and attestation are hashed."],
};

function pillFor(step, result) {
  if (result?.verdict === "BLOCKED" || step === "teach_back_held") return ["BLOCKED", "blocked"];
  if (step.includes("review") || step.includes("alert_reversion") || step === "foxit_pause") return ["REVIEW", "review"];
  if (result?.verdict === "CLEAR" || step === "receipt") return [step === "receipt" ? "SEALED" : "CLEAR", "clear"];
  return ["RECORDED", ""];
}

function renderEncounters(items) {
  list.replaceChildren();
  for (const item of items) {
    const button = document.createElement("button");
    button.type = "button";
    button.setAttribute("aria-current", item.id === "SYN-ENC-BLOCKED-002" ? "true" : "false");
    button.innerHTML = `${item.patient_display_name}<small>${item.id} · ${item.state}</small>`;
    list.append(button);
  }
}

async function loadEncounters() {
  const response = await fetch("/v1/encounters");
  if (!response.ok) throw new Error("Could not load the synthetic encounter list.");
  renderEncounters((await response.json()).items);
}

runPath.addEventListener("click", async () => {
  runPath.disabled = true;
  runPath.textContent = "Running workflow…";
  timeline.replaceChildren();
  receiptLink.hidden = true;
  errorBox.hidden = true;
  try {
    const response = await fetch("/v1/demo/run", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error?.message || "Workflow failed.");
    for (const [index, item] of payload.timeline.entries()) {
      const [title, description] = STEP_COPY[item.step];
      const [pill, className] = pillFor(item.step, item.result);
      const row = document.createElement("li");
      row.className = "timeline-item";
      const detail = JSON.stringify(item.result, null, 2);
      row.innerHTML = `<span class="timeline-index">${index + 1}</span><div><h3>${title}</h3><p>${description}</p></div><span class="status-pill ${className}">${pill}</span><pre class="timeline-detail">${detail.replaceAll("&", "&amp;").replaceAll("<", "&lt;")}</pre>`;
      timeline.append(row);
    }
    renderEncounters([payload.encounter]);
    const receipt = payload.timeline.at(-1).result;
    receiptLink.href = `/receipt/${receipt.receipt_id}`;
    receiptLink.hidden = false;
  } catch (error) {
    errorBox.textContent = `${error.message} Run “python -m before.seed” and restart with --offline.`;
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

loadEncounters().catch((error) => { errorBox.textContent = error.message; errorBox.hidden = false; });
