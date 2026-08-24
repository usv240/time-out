const output = document.querySelector("#response-output");
const bodyInput = document.querySelector("#request-body");
const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";

async function evaluateDemo() {
  output.textContent = "Running deterministic Gate…";
  try {
    const parsed = JSON.parse(bodyInput.value);
    const response = await fetch(`${XANO_API_BASE}/v1/encounters/demo/evaluate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parsed) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || payload.error?.message || `Xano returned ${response.status}`);
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = JSON.stringify({ error: { message: error.message, remedy: "Send a valid JSON object and retry the live synthetic Xano sandbox." } }, null, 2);
  }
}
document.querySelector("#run-example").addEventListener("click", evaluateDemo);
document.querySelector("#send-request").addEventListener("click", evaluateDemo);
document.querySelector("#get-key").addEventListener("click", () => {
  const target = document.querySelector("#key-output");
  target.hidden = false;
  target.textContent = JSON.stringify({ access: "instant", signup: false, key_required: false, scope: "synthetic Texas neurotoxin only", endpoint: XANO_API_BASE }, null, 2);
});
