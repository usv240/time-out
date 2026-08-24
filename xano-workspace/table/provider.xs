// Provider evidence subject. Values are synthetic and do not assert legal authority.
table provider {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text synthetic_key filters=trim
    int clinic_id {
      table = "clinic"
    }
    text name filters=trim
    text credential_type filters=trim|upper
    text license_no? filters=trim
    text license_state filters=trim|upper
    text license_status filters=trim|upper
    date license_expires
    text board_status filters=trim|upper
    enum evidence_confidence {
      values = ["HIGH", "MEDIUM", "LOW"]
    }
    bool synthetic
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "synthetic_key", op: "asc"}]}
    {type: "btree", field: [{name: "clinic_id", op: "asc"}]}
  ]

  tags = ["before", "synthetic-only"]
  guid = "ByTffRRTkeZFKE9hqp7WHaJXU-U"
}
