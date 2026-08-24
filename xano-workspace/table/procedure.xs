// Supported procedure catalogue. Current scope is Texas neurotoxin only.
table procedure {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text code filters=trim|upper
    text name filters=trim
    text category filters=trim|upper
    bool requires_patient_order
    bool requires_protocol
    bool requires_good_faith_exam
    bool active
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "code", op: "asc"}]}
  ]

  tags = ["before", "texas-neurotoxin"]
  guid = "0p3oIly9Tlu2wJFTSCVVlVFOb1o"
}
