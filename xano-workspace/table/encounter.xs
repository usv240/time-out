// Synthetic pre-procedure encounter and optimistic state-machine version.
table encounter {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text public_id filters=trim
    int clinic_id {
      table = "clinic"
    }
  
    text patient_id filters=trim
    int provider_id {
      table = "provider"
    }
  
    int procedure_id {
      table = "procedure"
    }
  
    timestamp scheduled_at
    enum state {
      values = [
        "DRAFT"
        "EVIDENCE_PENDING"
        "GATE_EVALUATED"
        "HUMAN_REVIEW"
        "REMEDIATION"
        "CONSENT_COMPILED"
        "BASELINE_CAPTURED"
        "AWAITING_ATTESTATION"
        "READY_FOR_PROCEDURE"
        "SEALED"
      ]
    }
  
    int gate_decision_id? {
      table = "gate_decision"
    }
  
    json patient_flags
    bool practitioner_patient_relationship_established?
    bool adequate_medical_record_present?
    bool performer_identity_disclosed?
    enum preprocedure_evidence_status?=MISSING {
      values = ["MISSING", "COMPLETE"]
    }
  
    int version
    bool synthetic
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "public_id", op: "asc"}]
    }
    {type: "btree", field: [{name: "state", op: "asc"}]}
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  tags = ["before", "state-machine", "synthetic-only"]
  guid = "598tuh8yRddMyWozTkXP-gOU-zc"
}