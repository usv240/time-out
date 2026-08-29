// Patient safety receipt.
// The receipt is a static, committed artifact of the hero run (recorded live 2026-08-26).
// It states what was checked and never claims legality, safety, authenticity, or outcome.

const target = document.querySelector("#receipt-body");
const params = new URLSearchParams(location.search);
const requestedId = params.get("id") || decodeURIComponent(location.pathname.split("/").filter(Boolean).at(-1) || "");

const MASK_FILES = new Set(["acne", "droopy_lower_eyelid", "droopy_upper_eyelid", "eye_bag", "firmness", "moisture", "oiliness", "pore", "radiance", "redness", "texture", "wrinkle"]);
function maskSrc(ref) {
  if (!ref) return null;
  if (String(ref).includes("/")) return ref;                       // already a path
  return MASK_FILES.has(ref) ? `/assets/perfectcorp/synthetic-patient-02-${ref}-overlay.png` : null;
}

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
  preprocedure_assessment: "Pre-procedure assessment recorded",
  good_faith_exam: "Pre-procedure assessment recorded",
  product_lot: "Product lot captured; no confirmed alert",
  product_evidence: "Product lot captured; no confirmed alert",
  comprehension: "Patient passed teach-back for this ruleset",
  board_status: "No disciplinary finding",
  disciplinary_status: "No disciplinary finding",
};

function checksTable(findings) {
  const rows = (findings || []).map((f) => {
    const cls = f.status === "PASS" ? "clear" : f.status === "REVIEW" ? "review" : "blocked";
    return `<tr class="finding ${cls}"><td>${escapeHtml(CHECK_COPY[f.check_id] || f.check_id)}</td><td><span class="status-pill ${cls}">${escapeHtml(f.status)}</span></td><td>${(f.citation_urls || []).slice(0, 1).map((u) => `<a href="${escapeHtml(u)}" target="_blank" rel="noopener">source</a>`).join("")}</td></tr>`;
  }).join("");
  return `<table class="findings"><thead><tr><th>Check</th><th>Result</th><th>Cited</th></tr></thead><tbody>${rows}</tbody></table>`;
}

// Twelve concerns, twelve overlay masks, twelve scores. Rendering them stacked made a
// static picture; a patient could not tell which mark belonged to which score. Selecting
// one shows that mask alone over the face, with the score and what it does and does not
// mean. The point of a baseline is that the patient can read it, not just hold it.
const CONCERN_COPY = {
  radiance: ["Radiance", "How evenly light reflects off the skin surface."],
  pore: ["Pore visibility", "Where pores read as larger in this lighting."],
  oiliness: ["Oiliness", "Surface shine at the time of capture."],
  moisture: ["Moisture", "Estimated surface hydration."],
  redness: ["Redness", "Areas reading warmer than surrounding skin."],
  texture: ["Texture", "Local variation in the skin surface."],
  firmness: ["Firmness", "How defined the facial contour reads."],
  wrinkle: ["Wrinkles", "Lines the analysis could resolve at this resolution."],
  acne: ["Blemishes", "Spots the analysis marked as raised or inflamed."],
  droopy_lower_eyelid: ["Lower eyelid", "Contour beneath the eye."],
  eye_bag: ["Under-eye", "Shadowing and puffiness under the eye."],
  droopy_upper_eyelid: ["Upper eyelid", "How the upper lid sits over the eye."],
};

function baselineBlock(b) {
  if (!b) return "";
  const entries = Object.entries(b.concerns || {})
    .sort((x, y) => Number(x[1]) - Number(y[1]));          // lowest score first: what a clinician looks at
  const masks = (b.mask_refs || []).filter((r) => maskSrc(r));

  const layers = masks.map((ref) => `<img class="analysis-mask" data-mask="${escapeHtml(ref)}" src="${escapeHtml(maskSrc(ref))}" alt="" hidden>`).join("");

  const rows = entries.map(([name, score], i) => {
    const [label, blurb] = CONCERN_COPY[name] || [name.replaceAll("_", " "), ""];
    const has = masks.includes(name);
    return `<button class="concern" role="radio" aria-checked="${i === 0}" tabindex="${i === 0 ? 0 : -1}"
      data-concern="${escapeHtml(name)}" data-blurb="${escapeHtml(blurb)}" data-label="${escapeHtml(label)}"
      ${has ? "" : "data-nomask=\"1\""}>
      <span class="concern-name">${escapeHtml(label)}</span>
      <span class="concern-bar"><span style="width:${Number(score)}%"></span></span>
      <span class="concern-score">${Number(score)}</span>
    </button>`;
  }).join("");

  return `<section class="perfect-proof" aria-label="Your skin baseline">
    <div class="baseline-portrait">
      <img src="${escapeHtml(b.image_ref)}" alt="AI-generated fictional adult used for the synthetic baseline">
      ${layers}
      <p class="mask-caption" id="mask-caption" aria-live="polite"></p>
    </div>
    <div class="baseline-data">
      <p class="integration-kicker">YOUR BASELINE — BEFORE TREATMENT ${info("i-baseline", "A standardized skin analysis taken before anything was done, with a score and an overlay for each of twelve concerns.", "An objective starting point you keep. If something looks different later, this is what it looked like first — and you can see exactly which mark produced which score.", "Perfect Corp YouCam Skin Analysis (SD) · synthetic face")}</p>
      <div class="metric-pair"><div><span>Overall</span><strong>${Number(b.overall_score).toFixed(1)}</strong></div><div><span>Skin age (synthetic)</span><strong>${escapeHtml(b.skin_age)}</strong></div></div>
      <p class="muted concern-hint">Select a concern to see it on the face. Lowest scores first &mdash; those are the ones worth watching.</p>
      <div class="concern-list" role="radiogroup" aria-label="Skin concerns">${rows}</div>
      <p class="evidence-boundary">${escapeHtml(b.boundary)}</p>
    </div>
  </section>`;
}

function selectConcern(btn) {
  const wrap = btn.closest(".perfect-proof");
  if (!wrap) return;
  for (const b of wrap.querySelectorAll(".concern")) {
    b.setAttribute("aria-checked", String(b === btn));
    b.tabIndex = b === btn ? 0 : -1;
  }
  const name = btn.dataset.concern;
  for (const layer of wrap.querySelectorAll(".analysis-mask")) {
    layer.hidden = layer.dataset.mask !== name;
  }
  const caption = wrap.querySelector("#mask-caption");
  if (caption) {
    caption.textContent = btn.dataset.nomask
      ? `${btn.dataset.label} — scored, no overlay returned for this concern.`
      : `${btn.dataset.label} — ${btn.dataset.blurb}`;
  }
  btn.focus();
}

// A receipt carries two records on the clinic's own domain, answering two different
// questions: the digest says "is this the receipt that was issued?", the status says
// "is it still good?". A patient needs the second one, because an alert can land after
// they have already walked out.
const XANO_V1 = ["localhost", "127.0.0.1"].includes(location.hostname)
  ? "/v1" : "https://x6g0-xqak-a8ri.n7e.xano.io/api:before/v1";

function statusBlock() {
  return `<section class="dns-receipt-proof" id="status-proof">
    <p class="integration-kicker">IS THIS RECEIPT STILL GOOD? ${info("i-status", "A separate status record published on your clinic's own domain, read live through the name.com API.", "A receipt says the checks passed on the day. If an FDA alert or a board action lands afterwards, this is how you find out — without calling the clinic that gave it to you.", "name.com CORE sandbox · _status.<receipt-id>.<clinic domain>")}</p>
    <p class="muted">Checks the clinic&rsquo;s own domain, not ours. A missing record reports <code>UNKNOWN</code>, never valid &mdash; absence is not validity.</p>
    <button class="button button-primary" id="check-status" type="button">Check this receipt&rsquo;s status now</button>
    <div id="status-out" hidden></div>
  </section>`;
}

async function checkStatus() {
  const out = document.querySelector("#status-out");
  const btn = document.querySelector("#check-status");
  btn.disabled = true;
  out.hidden = false;
  out.innerHTML = `<p class="muted">Reading the clinic&rsquo;s DNS through name.com…</p>`;
  try {
    const r = await fetch(`${XANO_V1}/live/receipt-status`);
    const d = await r.json();
    if (!r.ok) throw new Error(d.message || "status lookup failed");
    const cls = d.status === "VALID" ? "dns-match" : d.status === "REVOKED" ? "dns-unverified" : "";
    const headline = d.status === "VALID" ? "STILL VALID"
      : d.status === "REVOKED" ? "REVOKED — DO NOT RELY ON THIS RECEIPT"
      : "UNKNOWN — no status published";
    document.querySelector("#status-proof").className = `dns-receipt-proof ${cls}`;
    out.innerHTML = `<strong>${escapeHtml(headline)}</strong>
      <span class="src-badge live">LIVE · name.com via Xano</span>
      ${d.reason ? `<p><b>Reason</b> ${escapeHtml(String(d.reason).replaceAll("-", " "))}</p>` : ""}
      ${d.at ? `<p class="muted">Recorded ${escapeHtml(d.at)}</p>` : ""}
      <h3>${escapeHtml(d.fqdn || "")}</h3>
      <code>${escapeHtml(d.answer || "")}</code>
      <p class="muted">${escapeHtml(d.caveat || "")}</p>`;
  } catch (error) {
    out.innerHTML = `<p class="console-error" role="alert">${escapeHtml(error.message)}</p>`;
  } finally {
    btn.disabled = false;
  }
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

function attestationBlock(esign) {
  const a = esign?.attestation;
  const signed = Boolean(a?.executed);
  const who = (a?.signed_by || []).map((s) => s.name).filter(Boolean).join(", ");
  // Two documents, deliberately: what the agent produced, and what the human returned.
  const assembled = `<a class="button" href="/artifacts/time-out-safety-record.pdf" target="_blank" rel="noopener">Open the assembled record (PDF, watermarked SYNTHETIC)</a>`;
  if (!signed) {
    return `<section class="attestation-proof">
      <p class="integration-kicker">MEDICAL DIRECTOR ATTESTATION ${info("i-attest", "The agent assembled this record and stopped. A named human signs it through Foxit eSign.", "An agent that could sign its own attestation would make the attestation worthless. The pause is the point.", "Foxit eSign · envelope " + escapeHtml(String(esign?.folder?.folderId || "")))}</p>
      <strong>AWAITING SIGNATURE</strong>
      <p class="muted">This record is not attested until the Medical Director signs it.</p>
      ${assembled}</section>`;
  }
  return `<section class="attestation-proof dns-match">
    <p class="integration-kicker">MEDICAL DIRECTOR ATTESTATION ${info("i-attest", "The agent assembled this record and stopped. A named human signed it through Foxit eSign, and the agent read the outcome back.", "An agent that could sign its own attestation would make the attestation worthless. The pause is the point.", "Foxit eSign · envelope " + escapeHtml(String(a.folder_id)))}</p>
    <strong>SIGNED BY A NAMED HUMAN</strong>
    <h3>${escapeHtml(who)}</h3>
    <p class="muted">Envelope <code>${escapeHtml(String(a.folder_id))}</code> · status <code>${escapeHtml(a.folder_status)}</code></p>
    <p class="muted">Signing appends a signature and a certificate page, so the signed file's fingerprint differs from the assembled one by design. Both are published:<br>
      assembled <code>${escapeHtml((a.assembled_sha256 || "").slice(0, 24))}…</code><br>
      signed <code>${escapeHtml((a.signed_pdf_sha256 || "").slice(0, 24))}…</code></p>
    <a class="button button-primary" href="/artifacts/time-out-safety-record-signed.pdf" target="_blank" rel="noopener">Open the signed record (PDF)</a>
    ${assembled}
    <p class="evidence-boundary">The agent never signs. It assembled the record, handed it to a named human, and read the outcome back.</p>
  </section>`;
}

async function loadReceipt() {
  try {
    const [receipt, hero, esign] = await Promise.all([
      fetch("/data/receipt.json").then((r) => r.json()),
      fetch("/data/hero-timeline.json").then((r) => r.json()).catch(() => null),
      fetch("/data/esign-folder.json").then((r) => r.json()).catch(() => null),
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
      ${statusBlock()}
      ${attestationBlock(esign)}
      <div class="receipt-boundary"><strong>What this proves — and what it does not</strong><p>${escapeHtml(receipt.boundary)}</p></div>
      <details class="machine-evidence"><summary>Machine evidence</summary><pre class="timeline-detail">${escapeHtml(JSON.stringify(receipt, null, 2))}</pre></details>`);
  } catch (error) {
    target.innerHTML = `<p class="console-error" role="alert">${escapeHtml(error.message)} Run the safety check in <a href="/try.html">the clinic console</a>, then open its receipt link.</p>`;
  }
}

document.addEventListener("click", (event) => {
  const concern = event.target.closest(".concern");
  if (concern) { selectConcern(concern); return; }
  if (event.target.closest("#check-status")) { checkStatus(); return; }
  const btn = event.target.closest(".info-btn");
  if (!btn) return;
  const pop = document.getElementById(btn.getAttribute("aria-controls"));
  const open = btn.getAttribute("aria-expanded") === "true";
  btn.setAttribute("aria-expanded", String(!open));
  pop.hidden = open;
});
document.addEventListener("keydown", (event) => {
  // A radiogroup is expected to move with arrows, not Tab.
  const current = event.target.closest?.(".concern");
  if (current && ["ArrowDown", "ArrowRight", "ArrowUp", "ArrowLeft", "Home", "End"].includes(event.key)) {
    const all = [...current.closest(".concern-list").querySelectorAll(".concern")];
    const i = all.indexOf(current);
    const next = event.key === "Home" ? 0
      : event.key === "End" ? all.length - 1
      : ["ArrowDown", "ArrowRight"].includes(event.key) ? (i + 1) % all.length
      : (i - 1 + all.length) % all.length;
    event.preventDefault();
    selectConcern(all[next]);
    return;
  }
  if (event.key !== "Escape") return;
  for (const btn of document.querySelectorAll('.info-btn[aria-expanded="true"]')) {
    btn.setAttribute("aria-expanded", "false");
    document.getElementById(btn.getAttribute("aria-controls")).hidden = true;
    btn.focus();
  }
});

loadReceipt();
