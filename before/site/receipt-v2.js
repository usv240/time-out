// Patient safety receipt.
// The receipt is a static, committed artifact of the hero run (recorded live 2026-08-26).
// It states what was checked and never claims legality, safety, authenticity, or outcome.

const target = document.querySelector("#receipt-body");
const params = new URLSearchParams(location.search);
const requestedId = params.get("id") || decodeURIComponent(location.pathname.split("/").filter(Boolean).at(-1) || "");

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
}

function info(id, what, why, source) {
  return `<button class="info-btn" type="button" aria-expanded="false" aria-controls="${id}" aria-label="Explain">i</button>
    <div class="info-pop" id="${id}" hidden><p><b>What</b> ${escapeHtml(what)}</p><p><b>Why</b> ${escapeHtml(why)}</p><p><b>Source</b> <code>${escapeHtml(source)}</code></p></div>`;
}

const CHECK_COPY = {
  provider_license: "Licence active, in-state, unexpired",
  authority_pathway: "Authorised to perform this — directly or under documented delegation",
  delegation_and_supervision: "Patient-specific order, signed protocol, BLS, supervisor available",
  good_faith_exam: "Required examination recorded",
  product_evidence: "Product lot captured; no confirmed alert",
  comprehension: "Patient passed teach-back for this ruleset",
  board_status: "No disciplinary finding",
};

function checksTable(findings) {
  const rows = (findings || []).map((f) => {
    const cls = f.status === "PASS" ? "clear" : f.status === "REVIEW" ? "review" : "blocked";
    return `<tr class="finding ${cls}"><td>${escapeHtml(CHECK_COPY[f.check_id] || f.check_id)}</td><td><span class="status-pill ${cls}">${escapeHtml(f.status)}</span></td><td>${(f.citation_urls || []).slice(0, 1).map((u) => `<a href="${escapeHtml(u)}" target="_blank" rel="noopener">source</a>`).join("")}</td></tr>`;
  }).join("");
  return `<table class="findings"><thead><tr><th>Check</th><th>Result</th><th>Cited</th></tr></thead><tbody>${rows}</tbody></table>`;
}

function baselineBlock(b) {
  if (!b) return "";
  const scores = Object.entries(b.concerns || {}).sort((x, y) => x[0].localeCompare(y[0]));
  const grid = scores.map(([name, score]) => `<div class="score-row"><span>${escapeHtml(name.replaceAll("_", " "))}</span><meter min="0" max="100" value="${Number(score)}">${Number(score)}</meter><code>${Number(score)}</code></div>`).join("");
  const masks = (b.mask_refs || []).map((m) => `<img class="analysis-mask" src="${escapeHtml(m)}" alt="">`).join("");
  return `<section class="perfect-proof" aria-label="Your skin baseline">
    <div class="baseline-portrait"><img src="${escapeHtml(b.image_ref)}" alt="AI-generated fictional adult used for the synthetic baseline">${masks}</div>
    <div class="baseline-data"><p class="integration-kicker">YOUR BASELINE — BEFORE TREATMENT ${info("i-baseline", "A standardized skin analysis taken before anything was done, with scored concerns and overlays.", "An objective starting point you keep. If something looks different later, this is what it looked like first.", "Perfect Corp YouCam Skin Analysis (SD) · synthetic face")}</p>
    <div class="metric-pair"><div><span>Overall</span><strong>${Number(b.overall_score).toFixed(1)}</strong></div><div><span>Skin age (synthetic)</span><strong>${escapeHtml(b.skin_age)}</strong></div></div>
    <div class="score-grid">${grid}</div>
    <p class="evidence-boundary">${escapeHtml(b.boundary)}</p></div>
  </section>`;
}

function dnsBlock(dns) {
  const ok = Boolean(dns?.matches);
  return `<section class="dns-receipt-proof ${ok ? "dns-match" : "dns-unverified"}">
    <p class="integration-kicker">PUBLISHED RECORD ${info("i-dns", "The receipt's fingerprint (SHA-256) was published as a DNS TXT record under the registry domain, then read back through the name.com API.", "So you can check the receipt you hold matches what was published — without an account and without trusting this site.", "name.com CORE sandbox · " + (dns?.verified_through || "API read-back"))}</p>
    <strong>${ok ? "TXT READ-BACK MATCHED" : "TXT NOT VERIFIED"}</strong> <span class="src-badge cached">CACHED · verified ${escapeHtml((dns?.verified_at || "2026-08-26").slice(0, 10))}</span>
    <h3>${escapeHtml(dns?.txt_name || "")}.${escapeHtml(dns?.domain || "")}</h3>
    <code>${escapeHtml(dns?.txt_value || "")}</code>
    <p class="muted">${escapeHtml(dns?.caveat || "Sandbox DNS does not propagate publicly and a TXT record is mutable by its owner. This is a verification channel, not a notary.")}</p>
  </section>`;
}

async function loadReceipt() {
  try {
    const [receipt, hero] = await Promise.all([
      fetch("/data/receipt.json").then((r) => r.json()),
      fetch("/data/hero-timeline.json").then((r) => r.json()).catch(() => null),
    ]);
    if (requestedId && requestedId !== receipt.receipt_id && !requestedId.endsWith("receipt.html")) {
      // Only the hero receipt is committed as a static artifact. Say so instead of pretending.
      target.innerHTML = `<p class="console-error" role="alert">No committed receipt matches <code>${escapeHtml(requestedId)}</code>. Showing the recorded hero receipt <code>${escapeHtml(receipt.receipt_id)}</code> instead.</p>`;
    } else {
      target.innerHTML = "";
    }
    const steps = hero?.timeline || [];
    const finalGate = [...steps].reverse().find((s) => s.step?.startsWith("gate_clear"))?.result;
    const baseline = steps.find((s) => s.step === "baseline")?.result;
    const dns = receipt.dns_verification || {};

    target.insertAdjacentHTML("beforeend", `
      <div class="verification-stack">
        <div class="verification-result"><strong>WHAT WAS CHECKED BEFORE TREATMENT</strong><br>Seven checks, run against the Texas ruleset frozen at <code>${escapeHtml((receipt.rule_snapshot_sha256 || "").slice(0, 16))}…</code> ${info("i-snap", "The exact rules used were frozen and fingerprinted when the decision was made.", "So the decision still explains itself years later, even after the rules change.", "rule_snapshot_sha256 · reproducible byte-for-byte")}</div>
      </div>
      ${finalGate ? checksTable(finalGate.findings) : ""}
      ${baselineBlock(baseline)}
      <dl class="receipt-grid">
        <div class="receipt-field"><dt>Receipt</dt><dd><code>${escapeHtml(receipt.receipt_id)}</code></dd></div>
        <div class="receipt-field"><dt>Encounter</dt><dd><code>${escapeHtml(receipt.encounter_id)}</code></dd></div>
        <div class="receipt-field"><dt>Sealed</dt><dd><code>${escapeHtml(receipt.sealed_at)}</code></dd></div>
        <div class="receipt-field"><dt>Receipt fingerprint</dt><dd><code>${escapeHtml(receipt.receipt_hash)}</code></dd></div>
        <div class="receipt-field"><dt>Consent document</dt><dd><code>${escapeHtml(receipt.consent_document_id)}</code></dd></div>
        <div class="receipt-field"><dt>Medical Director attestation</dt><dd><code>${escapeHtml(receipt.attestation_id)}</code></dd></div>
      </dl>
      ${dnsBlock(dns)}
      <a class="button button-primary" href="/artifacts/time-out-safety-record.pdf" target="_blank" rel="noopener">Open the assembled safety record (PDF, watermarked SYNTHETIC)</a>
      <div class="receipt-boundary"><strong>What this proves — and what it does not</strong><p>${escapeHtml(receipt.boundary)}</p></div>
      <details class="machine-evidence"><summary>Machine evidence</summary><pre class="timeline-detail">${escapeHtml(JSON.stringify(receipt, null, 2))}</pre></details>`);
  } catch (error) {
    target.innerHTML = `<p class="console-error" role="alert">${escapeHtml(error.message)} Run the safety check in <a href="/try.html">the clinic console</a>, then open its receipt link.</p>`;
  }
}

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

loadReceipt();
