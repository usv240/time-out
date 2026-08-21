const output = document.querySelector("#response-output");
const bodyInput = document.querySelector("#request-body");

async function evaluateDemo() {
  output.textContent = "Running deterministic Gate…";
  try {
    const parsed = JSON.parse(bodyInput.value);
    const response = await fetch("/v1/encounters/demo/evaluate", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parsed) });
    const payload = await response.json();
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = JSON.stringify({ error: { message: error.message, remedy: "Send a valid JSON object and ensure the local API server is running." } }, null, 2);
  }
}
document.querySelector("#run-example").addEventListener("click", evaluateDemo);
document.querySelector("#send-request").addEventListener("click", evaluateDemo);
document.querySelector("#get-key").addEventListener("click", async () => {
  const target = document.querySelector("#key-output");
  target.hidden = false;
  target.textContent = "Issuing synthetic sandbox key…";
  const response = await fetch("/v1/sandbox-keys", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  target.textContent = JSON.stringify(await response.json(), null, 2);
});
