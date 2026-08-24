const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";
const API_BASE = ["localhost", "127.0.0.1"].includes(location.hostname) ? "" : XANO_API_BASE;
const target = document.querySelector("#receipt-body");
const receiptId = decodeURIComponent(location.pathname.split("/").filter(Boolean).at(-1) || "");

function escapeHtml(value) {
  return String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
}

async function loadReceipt() {
  try {
    const response = await fetch(`${API_BASE}/v1/receipts/${encodeURIComponent(receiptId)}`);
    const receipt = await response.json();
    if (!response.ok) throw new Error(receipt.error?.message || "Receipt not found.");
    const verifyResponse = await fetch(`${API_BASE}/v1/receipts/verify`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ receipt_hash: receipt.receipt_hash }) });
    const verification = await verifyResponse.json();
    const hashVerified = Boolean(verification.verified);
    const dns = receipt.dns_verification || {};
    target.innerHTML = `<div class="verification-stack">
        <div class="verification-result ${hashVerified ? "" : "verification-failed"}"><strong>${hashVerified ? "HASH VERIFIED" : "HASH MISMATCH"}</strong><br>${hashVerified ? "Stored and recomputed receipt payloads match." : "The stored receipt did not reproduce. Do not rely on this record."}</div>
        <div class="verification-result ${dns.matches ? "" : "verification-pending"}"><strong>${dns.matches ? "NAME.COM TXT MATCHED" : "NAME.COM TXT NOT VERIFIED"}</strong><br>${escapeHtml(dns.verified_through)}</div>
      </div>
      <dl class="receipt-grid">
        <div class="receipt-field"><dt>Receipt</dt><dd><code>${escapeHtml(receipt.receipt_id)}</code></dd></div>
        <div class="receipt-field"><dt>Encounter</dt><dd><code>${escapeHtml(receipt.encounter_id)}</code></dd></div>
        <div class="receipt-field"><dt>Rule snapshot</dt><dd><code>${escapeHtml(receipt.rule_snapshot_sha256)}</code></dd></div>
        <div class="receipt-field"><dt>Receipt hash</dt><dd><code>${escapeHtml(receipt.receipt_hash)}</code></dd></div>
        <div class="receipt-field"><dt>Perfect baseline</dt><dd><code>${escapeHtml(receipt.baseline_capture_id)}</code></dd></div>
        <div class="receipt-field"><dt>Medical Director attestation</dt><dd><code>${escapeHtml(receipt.attestation_id)}</code></dd></div>
      </dl>
      <section class="dns-receipt-proof"><p class="integration-kicker">NAME.COM CORE SANDBOX / READ-BACK</p><h3>${escapeHtml(dns.fqdn || dns.domain)}</h3><code>${escapeHtml(dns.txt_value)}</code><p>${escapeHtml(dns.caveat)}</p></section>
      <a class="button button-primary" href="/artifacts/synthetic-safety-evidence-record.pdf" target="_blank" rel="noopener">Open assembled evidence record</a>
      <div class="receipt-boundary"><strong>What this proves - and what it does not</strong><p>${escapeHtml(receipt.boundary)}</p></div>
      <details><summary>Verification payload</summary><pre><code>${escapeHtml(JSON.stringify(verification, null, 2))}</code></pre></details>`;
  } catch (error) {
    target.innerHTML = `<p class="console-error" role="alert">${escapeHtml(error.message)} Run the complete workflow in <a href="/try.html">the clinic console</a>, then open its receipt link.</p>`;
  }
}

loadReceipt();
