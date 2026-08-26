// Bound to explicit Gate enum contract.
// Post-schema function binding.
// Rebound to typed-status BEFORE functions.
// Bound after BEFORE v1 function revisions.
// Compiled after reusable BEFORE functions.
// Attach documented remediation through typed fields; no direct database editing is required.
query "v1/encounters/{encounter_id}/remediate" verb=POST {
  api_group = "BEFORE Public API"

  input {
    text encounter_id filters=trim
    text credential_type filters=trim|upper
    bool training_documented
    bool complication_training
    text delegation_agreement_id filters=trim
    text protocol_id filters=trim
    bool delegating_physician_active
    bool patient_specific_order_present
    bool order_contains_drug_dose_strength_route
    bool bls_current
    bool supervisor_onsite
    bool supervisor_immediately_available
    bool physician_emergency_appointment_available
    json patient_flags
    bool practitioner_patient_relationship_established
    bool adequate_medical_record_present
    bool performer_identity_disclosed
    text product_lot_no filters=trim
    enum product_alert_status {
      values = [
        "MATCHED_TO_NO_CAPTURED_ALERT"
        "ALERT_CANDIDATE"
        "CONFIRMED_ALERT"
        "UNKNOWN"
      ]
    }
  
    bool comprehension_passed
    int comprehension_score
    text actor filters=trim
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
  
    precondition ($encounter.state == "REMEDIATION" || $encounter.state == "HUMAN_REVIEW") {
      error_type = "inputerror"
      error = "Encounter must be in REMEDIATION or HUMAN_REVIEW."
    }
  
    db.get provider {
      field_name = "id"
      field_value = $encounter.provider_id
    } as $provider
  
    db.query authority_evidence {
      where = $db.authority_evidence.provider_id == $provider.id
      return = {type: "single"}
    } as $authority
  
    db.query product_lot {
      where = $db.product_lot.encounter_id == $encounter.id
      return = {type: "single"}
    } as $product
  
    db.query comprehension {
      where = $db.comprehension.encounter_id == $encounter.id
      return = {type: "single"}
    } as $comprehension
  
    precondition ($provider != null && $authority != null && $product != null && $comprehension != null) {
      error_type = "inputerror"
      error = "Required evidence records are missing."
    }
  
    db.edit provider {
      field_name = "id"
      field_value = $provider.id
      data = {credential_type: $input.credential_type}
    } as $updated_provider
  
    db.edit authority_evidence {
      field_name = "id"
      field_value = $authority.id
      data = {
        training_documented                      : $input.training_documented
        complication_training                    : $input.complication_training
        delegation_agreement_id                  : $input.delegation_agreement_id
        protocol_id                              : $input.protocol_id
        delegating_physician_active              : $input.delegating_physician_active
        patient_specific_order_present           : $input.patient_specific_order_present
        order_contains_drug_dose_strength_route  : $input.order_contains_drug_dose_strength_route
        bls_current                              : $input.bls_current
        supervisor_onsite                        : $input.supervisor_onsite
        supervisor_immediately_available         : $input.supervisor_immediately_available
        physician_emergency_appointment_available: $input.physician_emergency_appointment_available
        verified_at                              : "now"
        confidence                               : "HIGH"
      }
    } as $updated_authority
  
    db.edit product_lot {
      field_name = "id"
      field_value = $product.id
      data = {
        lot_no      : $input.product_lot_no
        alert_status: $input.product_alert_status
        confidence  : "HIGH"
        checked_at  : "now"
      }
    } as $updated_product
  
    db.edit comprehension {
      field_name = "id"
      field_value = $comprehension.id
      data = {
        score       : $input.comprehension_score
        passed      : $input.comprehension_passed
        attempts    : $comprehension.attempts + 1
        confidence  : "HIGH"
        completed_at: "now"
      }
    } as $updated_comprehension
  
    db.edit encounter {
      field_name = "id"
      field_value = $encounter.id
      data = {
        patient_flags                                : $input.patient_flags
        practitioner_patient_relationship_established: $input.practitioner_patient_relationship_established
        adequate_medical_record_present              : $input.adequate_medical_record_present
        performer_identity_disclosed                 : $input.performer_identity_disclosed
        preprocedure_evidence_status                 : ($input.practitioner_patient_relationship_established && $input.adequate_medical_record_present && $input.performer_identity_disclosed) ? "COMPLETE" : "MISSING"
      }
    } as $updated_encounter
  
    function.run before_v1_transition {
      input = {
        encounter_id: $encounter.id
        to_state    : "EVIDENCE_PENDING"
        actor       : $input.actor
        action      : "evidence_remediated"
        reason      : "Named human attached documented remediation for a deterministic rerun."
        payload     : {
        provider_id          : $provider.id
        authority_evidence_id: $authority.id
        product_lot_id       : $product.id
        comprehension_id     : $comprehension.id
      }
      }
    } as $transition
  }

  response = $transition.encounter
  tags = ["before", "remediation", "human-review"]
  guid = "4U2sZx5sRyEXyr917or2aQtFYT4"
}