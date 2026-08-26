// Treatment-party consent signatures. Medical-director attestation is deliberately separate.
table consent_record {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
  
    text doctavian_doc_id? filters=trim
    text template_version filters=trim
    json signers
    timestamp signed_at?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "encounter_id", op: "asc"}]
    }
  ]

  tags = ["before", "consent"]
  guid = "SnNwCD0IC83uzkSfacXnSGKhwwk"
}