// Compiled after reusable BEFORE functions.
// Inspect current state, frozen decisions, and the append-only transition history.
query "v1/encounters/{encounter_id}" verb=GET {
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

    db.query gate_decision {
      where = $db.gate_decision.encounter_id == $encounter.id
      sort = {gate_decision.evaluated_at: "desc"}
      return = {type: "list"}
    } as $decisions

    db.query audit_event {
      where = $db.audit_event.encounter_id == $encounter.id
      sort = {audit_event.created_at: "asc"}
      return = {type: "list"}
    } as $audit_events
  }

  response = {encounter: $encounter, decisions: $decisions, audit_events: $audit_events}
  tags = ["before", "audit", "public"]
  guid = "DIwH2s6FtPMVP-AlZ_fIUYao2nw"
}
