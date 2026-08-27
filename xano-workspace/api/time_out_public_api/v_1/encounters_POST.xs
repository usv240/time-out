// Bound to explicit Gate enum contract.
// Post-schema function binding.
// Rebound to typed-status BEFORE functions.
// Bound after BEFORE v1 function revisions.
// Compiled after reusable BEFORE functions.
// Create a synthetic encounter and apply DRAFT -> EVIDENCE_PENDING through the audited state machine.
query "v1/encounters" verb=POST {
  api_group = "Time-Out Public API"

  input {
    int clinic_id
    int provider_id
    int procedure_id
    text patient_id filters=trim
    timestamp scheduled_at
    json patient_flags
  }

  stack {
    db.get clinic {
      field_name = "id"
      field_value = $input.clinic_id
    } as $clinic
  
    db.get provider {
      field_name = "id"
      field_value = $input.provider_id
    } as $provider
  
    db.get procedure {
      field_name = "id"
      field_value = $input.procedure_id
    } as $procedure
  
    precondition ($clinic != null && $clinic.synthetic && $provider != null && $provider.synthetic && $procedure != null && $procedure.active) {
      error_type = "inputerror"
      error = "Synthetic clinic, synthetic provider, and active procedure records are required."
    }
  
    security.create_uuid as $encounter_uuid
    db.add encounter {
      data = {
        created_at                  : "now"
        public_id                   : "SYN-ENC-" ~ $encounter_uuid
        clinic_id                   : $clinic.id
        patient_id                  : $input.patient_id
        provider_id                 : $provider.id
        procedure_id                : $procedure.id
        scheduled_at                : $input.scheduled_at
        state                       : "DRAFT"
        patient_flags               : $input.patient_flags
        preprocedure_evidence_status: "MISSING"
        version                     : 0
        synthetic                   : true
      }
    } as $encounter
  
    function.run before_v1_transition {
      input = {
        encounter_id: $encounter.id
        to_state    : "EVIDENCE_PENDING"
        actor       : "Public synthetic API"
        action      : "encounter_opened"
        reason      : "Synthetic encounter created for evidence attachment."
        payload     : {public_id: $encounter.public_id}
      }
    } as $transition
  }

  response = $transition.encounter
  tags = ["before", "synthetic-only"]
  guid = "8hX-fRZ1Dr7CcL69hwSTU1QTFv4"
}