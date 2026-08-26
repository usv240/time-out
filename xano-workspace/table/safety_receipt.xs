// Bounded evidence record; it is a receipt, not a notary or safety certification.
table safety_receipt {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
  
    int gate_decision_id {
      table = "gate_decision"
    }
  
    text payload_sha256 filters=trim|lower
    text dns_txt_name? filters=trim
    timestamp published_at?
    text attestation_id? filters=trim
    json payload
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "encounter_id", op: "asc"}]
    }
    {
      type : "btree|unique"
      field: [{name: "payload_sha256", op: "asc"}]
    }
  ]

  tags = ["before", "receipt", "human-review"]
  guid = "6JOJaUAwubX3HcIUEjipcRudySg"
}