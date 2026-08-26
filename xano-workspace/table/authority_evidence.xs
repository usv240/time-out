// Typed evidence used to assess the documented authority and supervision pathway.
table authority_evidence {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int provider_id {
      table = "provider"
    }
  
    bool training_documented
    bool complication_training
    text delegation_agreement_id? filters=trim
    text protocol_id? filters=trim
    int supervisor_id? {
      table = "provider"
    }
  
    bool delegating_physician_active
    bool patient_specific_order_present
    bool order_contains_drug_dose_strength_route
    bool bls_current
    bool supervisor_onsite
    bool supervisor_immediately_available
    bool physician_emergency_appointment_available
    timestamp verified_at?
    enum confidence {
      values = ["HIGH", "MEDIUM", "LOW"]
    }
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "provider_id", op: "asc"}]
    }
  ]

  tags = ["before", "evidence"]
  guid = "ec4TdbeD8-ngxpMG71-5Alv_pak"
}