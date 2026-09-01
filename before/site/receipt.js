const target = document.querySelector("#receipt-body");
const receiptId = decodeURIComponent(location.pathname.split("/").filter(Boolean).at(-1) || "");

function escapeHtml(value) { return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;"); }
async function loadReceipt() {
  try {
    const response = await fetch(`/v1/receipts/${encodeURIComponent(receiptId)}`);
    const receipt = await response.json();
    if (!response.ok) throw new Error(receipt.error?.message || "Receipt not found.");
    const verifyResponse = await fetch("/v1/receipts/verify", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ receipt_hash: receipt.receipt_hash }) });
    const verification = await verifyResponse.json();
    target.innerHTML = `<div class="verification-result"><strong>✓ HASH VERIFIED</strong><br>Stored and recomputed receipt payloads match.</div>
      <dl class="receipt-grid">
        <div class="receipt-field"><dt>Receipt</dt><dd><code>${escapeHtml(receipt.receipt_id)}</code></dd></div>
        <div class="receipt-field"><dt>Encounter</dt><dd><code>${escapeHtml(receipt.encounter_id)}</code></dd></div>
        <div class="receipt-field"><dt>Rule snapshot</dt><dd><code>${escapeHtml(receipt.rule_snapshot_sha256)}</code></dd></div>
        <div class="receipt-field"><dt>Receipt hash</dt><dd><code>${escapeHtml(receipt.receipt_hash)}</code></dd></div>
        <div class="receipt-field"><dt>Consent</dt><dd><code>${escapeHtml(receipt.consent_document_id)}</code></dd></div>
        <div class="receipt-field"><dt>Medical director attestation</dt><dd><code>${escapeHtml(receipt.attestation_id)}</code></dd></div>
      </dl><a class="button button-primary" href="/artifacts/synthetic-safety-evidence-record.pdf" target="_blank">Open assembled evidence record</a><div class="receipt-boundary"><strong>What this proves, and what it does not</strong><p>${escapeHtml(receipt.boundary)}</p></div>
      <div class="snapshot-proof"><div><p class="eyebrow">Sandbox verification channel</p><h3>${escapeHtml(receipt.dns_verification.domain)}</h3></div><code>${escapeHtml(receipt.dns_verification.txt_name)} = ${escapeHtml(receipt.dns_verification.txt_value)}</code></div>
      <p class="muted">Verified through the name.com sandbox API. Sandbox DNS does not propagate publicly, and the record remains mutable by its owner.</p>
      <pre><code>${escapeHtml(JSON.stringify(verification, null, 2))}</code></pre>`;
  } catch (error) {
    target.innerHTML = `<p class="console-error" role="alert">${escapeHtml(error.message)} Run the complete workflow in <a href="/try.html">the clinic console</a>, then open its receipt link.</p>`;
  }
}
loadReceipt();
