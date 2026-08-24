// Bound to explicit Gate enum contract.
// Post-schema function binding.
// Rebound to typed-status BEFORE functions.
// Bound after BEFORE v1 function revisions.
// Compiled after reusable BEFORE functions.
// POST /encounters/:id/evaluate -> persisted evidence -> shared deterministic Gate -> frozen decision.
query "v1/encounters/{encounter_id}/evaluate" verb=POST {
  api_group = "BEFORE Public API"

  input {
    text encounter_id filters=trim
  }

  stack {
    db.get encounter {
      field_name = "public_id"
      field_value = $input.encounter_id
    } as $encounter
    precondition ($encounter != null && $encounter.synthetic) {
      error_type = "notfound"
      error = "Synthetic encounter not found."
    }

    function.run before_v1_evaluate_encounter {
      input = {encounter_id: $encounter.id, actor: "Public synthetic API"}
    } as $result
  }

  response = $result
  tags = ["before", "gate", "public"]
  guid = "DdsvUFjDe2O1HHHUcPgYaNsdQ50"
}
