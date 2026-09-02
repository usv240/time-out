const output = document.querySelector("#response-output");
const bodyInput = document.querySelector("#request-body");
const XANO_API_BASE = "https://x6g0-xqak-a8ri.n7e.xano.io/api:before";

// Both buttons write into one response pane near the bottom of the page. "Run this
// request" sits about 900px above it, so clicking it changed nothing you could see and
// the page looked broken: the call had in fact run and answered. Give feedback at the
// button, then bring the answer to the reader.
async function evaluateDemo(event) {
  const button = event && event.currentTarget;
  const restore = button ? button.textContent : null;
  if (button) {
    button.disabled = true;
    button.textContent = "Running…";
  }
  output.textContent = "Running deterministic Gate…";
  try {
    const parsed = JSON.parse(bodyInput.value);
    const response = await fetch(`${XANO_API_BASE}/v1/encounters/demo/evaluate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(parsed) });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.message || payload.error?.message || `Xano returned ${response.status}`);
    output.textContent = JSON.stringify(payload, null, 2);
  } catch (error) {
    output.textContent = JSON.stringify({ error: { message: error.message, remedy: "Send a valid JSON object and retry the live synthetic Xano sandbox." } }, null, 2);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = restore;
    }
    // Only scroll if the answer is off screen, so the button next to the pane does not
    // yank the page for someone who can already see it.
    const box = output.getBoundingClientRect();
    if (box.top > window.innerHeight - 80 || box.bottom < 0) {
      // Explicit offset rather than scrollIntoView: the pane grows from 200px to about
      // 3900px as the JSON lands, and the browser resolved the scroll against the old
      // layout, ignoring scroll-margin-top and parking "verdict" under the sticky
      // header. Compute it after the growth and there is nothing to get wrong.
      const header = document.querySelector(".site-header");
      const clearance = (header ? header.getBoundingClientRect().height : 0) + 24;
      window.scrollTo({
        top: output.getBoundingClientRect().top + window.scrollY - clearance,
        behavior: "smooth",
      });
    }
  }
}
document.querySelector("#run-example").addEventListener("click", evaluateDemo);
document.querySelector("#send-request").addEventListener("click", evaluateDemo);
document.querySelector("#get-key").addEventListener("click", async () => {
  const target = document.querySelector("#key-output");
  const button = document.querySelector("#get-key");
  target.hidden = false;
  target.textContent = "Issuing a tag from the live API...";
  button.disabled = true;
  try {
    // A real POST. The key it returns is optional everywhere: it tags your calls in
    // the audit log and grants nothing, which is why there is no signup behind it.
    const response = await fetch(`${XANO_API_BASE}/v1/keys`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label: "issued from the docs page" }),
    });
    const body = await response.json();
    target.textContent = JSON.stringify(body, null, 2);
  } catch (error) {
    target.textContent = `Could not reach the API: ${error.message}`;
  } finally {
    button.disabled = false;
  }
});
