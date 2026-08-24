// Full-import restoration marker.
// Dependency order: transition is compiled before its callers.
// Applies one guarded encounter transition and writes one audit event.
// Kept as the single transition boundary so dependent workflows recompile consistently.
// Retrying an already-applied transition is a no-op, so retries do not duplicate audit events.
function before_v1_transition {
  input {
    int encounter_id
    enum to_state {
      values = ["DRAFT", "EVIDENCE_PENDING", "GATE_EVALUATED", "HUMAN_REVIEW", "REMEDIATION", "CONSENT_COMPILED", "BASELINE_CAPTURED", "AWAITING_ATTESTATION", "READY_FOR_PROCEDURE", "SEALED"]
    }
    text actor filters=trim
    text action filters=trim
    text reason filters=trim
    json payload?
  }

  stack {
    db.get encounter {
      field_name = "id"
      field_value = $input.encounter_id
    } as $encounter

    precondition ($encounter != null) {
      error_type = "notfound"
      error = "Encounter not found."
    }

    var $is_retry {
      value = $encounter.state == $input.to_state
    }

    var $allowed {
      value = $is_retry || ($encounter.state == "DRAFT" && $input.to_state == "EVIDENCE_PENDING") || ($encounter.state == "EVIDENCE_PENDING" && ($input.to_state == "GATE_EVALUATED" || $input.to_state == "HUMAN_REVIEW")) || ($encounter.state == "GATE_EVALUATED" && ($input.to_state == "REMEDIATION" || $input.to_state == "HUMAN_REVIEW" || $input.to_state == "CONSENT_COMPILED")) || ($encounter.state == "REMEDIATION" && $input.to_state == "EVIDENCE_PENDING") || ($encounter.state == "HUMAN_REVIEW" && ($input.to_state == "EVIDENCE_PENDING" || $input.to_state == "CONSENT_COMPILED")) || ($encounter.state == "CONSENT_COMPILED" && ($input.to_state == "BASELINE_CAPTURED" || $input.to_state == "HUMAN_REVIEW")) || ($encounter.state == "BASELINE_CAPTURED" && $input.to_state == "AWAITING_ATTESTATION") || ($encounter.state == "AWAITING_ATTESTATION" && $input.to_state == "READY_FOR_PROCEDURE") || ($encounter.state == "READY_FOR_PROCEDURE" && ($input.to_state == "HUMAN_REVIEW" || $input.to_state == "SEALED"))
    }

    precondition ($allowed) {
      error_type = "inputerror"
      error = "Encounter state transition is not allowed."
    }

    conditional {
      if ($is_retry == false) {
        var $next_version {
          value = $encounter.version + 1
        }

        db.edit encounter {
          field_name = "id"
          field_value = $encounter.id
          data = {
            state  : $input.to_state
            version: $next_version
          }
        } as $updated_encounter

        var $payload_hash {
          value = ($input.payload|json_encode)|sha256:true|bin2hex
        }

        db.add audit_event {
          data = {
            created_at       : "now"
            encounter_id     : $encounter.id
            actor            : $input.actor
            action           : $input.action
            from_state       : $encounter.state
            to_state         : $input.to_state
            reason           : $input.reason
            payload_hash     : $payload_hash
            payload          : $input.payload
            encounter_version: $next_version
          }
        } as $audit_event
      }
    }

    db.get encounter {
      field_name = "id"
      field_value = $encounter.id
    } as $current_encounter
  }

  response = {encounter: $current_encounter, idempotent_retry: $is_retry}
  tags = ["before", "state-machine", "audit"]
  guid = "9l91T3w9U3w1W5f-7Bw6NnOOhzY"
}
