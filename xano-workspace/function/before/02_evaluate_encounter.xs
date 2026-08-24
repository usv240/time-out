// Post-schema binding: preprocedure_evidence_status.
// Gate revision binding: typed pre-procedure status.
// Gate revision binding: fail-closed typed evidence.
// Dependency order: evaluate_encounter is compiled before its callers.
// Loads persisted evidence, calls the pure Gate, freezes the decision, and advances the hold state.
function before_v1_evaluate_encounter {
  input {
    int encounter_id
    text actor filters=trim
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

    precondition ($encounter.synthetic) {
      error_type = "accessdenied"
      error = "This workspace accepts synthetic encounters only."
    }

    precondition ($encounter.state == "EVIDENCE_PENDING") {
      error_type = "inputerror"
      error = "Encounter must be EVIDENCE_PENDING before evaluation. Remediate first, then rerun."
    }

    db.get provider {
      field_name = "id"
      field_value = $encounter.provider_id
    } as $provider

    db.query authority_evidence {
      where = $db.authority_evidence.provider_id == $encounter.provider_id
      return = {type: "single"}
    } as $authority_evidence

    db.get procedure {
      field_name = "id"
      field_value = $encounter.procedure_id
    } as $procedure

    db.query jurisdiction_rule {
      where = $db.jurisdiction_rule.state == "TX" && $db.jurisdiction_rule.procedure_category == $procedure.category && $db.jurisdiction_rule.active == true
      return = {type: "single"}
    } as $jurisdiction_rule

    db.query product_lot {
      where = $db.product_lot.encounter_id == $encounter.id
      return = {type: "single"}
    } as $product_lot

    db.query comprehension {
      where = $db.comprehension.encounter_id == $encounter.id
      return = {type: "single"}
    } as $comprehension

    precondition ($provider != null && $authority_evidence != null && $procedure != null && $jurisdiction_rule != null && $product_lot != null && $comprehension != null) {
      error_type = "inputerror"
      error = "Required Gate evidence is incomplete. Attach or remediate evidence before evaluation."
    }

    var $encounter_evidence {
      value = {
        encounter_id : $encounter.public_id
        scheduled_on : $encounter.scheduled_at|format_timestamp:"Y-m-d":"UTC"
        patient_flags: $encounter.patient_flags
      }
    }

    function.run before_v1_gate {
      input = {
        encounter              : $encounter_evidence
        provider               : $provider
        authority_evidence     : $authority_evidence
        procedure              : $procedure
        product_lot            : $product_lot
        comprehension          : $comprehension
        rule_snapshot          : $jurisdiction_rule.rule_snapshot
        preprocedure_evidence_status: $encounter.preprocedure_evidence_status
        canonical_rule_snapshot: $jurisdiction_rule.canonical_rule_snapshot
      }
    } as $gate

    precondition ($gate.rule_snapshot_sha256 == $jurisdiction_rule.rule_snapshot_sha256) {
      error_type = "inputerror"
      error = "Stored rule snapshot hash mismatch; human review is required."
    }

    db.add gate_decision {
      data = {
        created_at              : "now"
        encounter_id            : $encounter.id
        verdict                 : $gate.verdict
        determination_scope     : $gate.determination_scope
        findings                : $gate.findings
        rule_snapshot           : $gate.rule_snapshot
        canonical_rule_snapshot : $gate.canonical_rule_snapshot
        rule_snapshot_sha256    : $gate.rule_snapshot_sha256
        evaluated_at            : "now"
        created_by              : $input.actor
      }
    } as $decision

    db.edit encounter {
      field_name = "id"
      field_value = $encounter.id
      data = {gate_decision_id: $decision.id}
    } as $encounter_with_decision

    function.run before_v1_transition {
      input = {
        encounter_id: $encounter.id
        to_state    : "GATE_EVALUATED"
        actor       : $input.actor
        action      : "gate_evaluated"
        reason      : "All seven deterministic checks evaluated against a frozen rule snapshot."
        payload     : {gate_decision_id: $decision.id, verdict: $gate.verdict, rule_snapshot_sha256: $gate.rule_snapshot_sha256}
      }
    } as $evaluated_transition

    conditional {
      if ($gate.verdict == "BLOCKED") {
        function.run before_v1_transition {
          input = {
            encounter_id: $encounter.id
            to_state    : "REMEDIATION"
            actor       : $input.actor
            action      : "gate_blocked"
            reason      : "One or more failed facts require documented remediation before a rerun."
            payload     : {gate_decision_id: $decision.id, verdict: $gate.verdict}
          }
        } as $blocked_transition
      }
      elseif ($gate.verdict == "REVIEW") {
        function.run before_v1_transition {
          input = {
            encounter_id: $encounter.id
            to_state    : "HUMAN_REVIEW"
            actor       : $input.actor
            action      : "gate_review_required"
            reason      : "Ambiguous or low-confidence evidence requires a named human review."
            payload     : {gate_decision_id: $decision.id, verdict: $gate.verdict}
          }
        } as $review_transition
      }
    }

    db.get encounter {
      field_name = "id"
      field_value = $encounter.id
    } as $current_encounter

    var $result {
      value = $gate
        |set:"id":$decision.id
        |set:"encounter_id":$encounter.public_id
        |set:"state":$current_encounter.state
        |set:"evaluated_at":$decision.evaluated_at
    }
  }

  response = $result
  tags = ["before", "gate", "state-machine"]
  guid = "IwvYAe_yQ_jgM1PH_Kjd6AsPQiQ"
}
