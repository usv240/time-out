// Bound to explicit Gate enum contract.
// Post-schema function binding.
// Rebound to typed-status BEFORE functions.
// Bound after BEFORE v1 function revisions.
// Compiled after reusable BEFORE functions.
// One-click public hero. It uses the real persisted state machine and Gate with synthetic evidence.
query "v1/encounters/demo/evaluate" verb=POST {
  api_group = "BEFORE Public API"

  input {
  }

  stack {
    function.run before_v1_demo_evaluate {
      input = {}
    } as $result
  }

  response = $result
  tags = ["before", "demo", "public", "synthetic-only"]
  guid = "kHsji-G7l8zvLi51b8LSo8aJ3H0"
}
