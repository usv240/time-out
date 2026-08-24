// Captured product-lot evidence. Alert clear is not an authenticity certification.
table product_lot {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
    text brand filters=trim
    text lot_no filters=trim
    date expiry
    enum alert_status {
      values = ["MATCHED_TO_NO_CAPTURED_ALERT", "ALERT_CANDIDATE", "CONFIRMED_ALERT", "UNKNOWN"]
    }
    enum confidence {
      values = ["HIGH", "MEDIUM", "LOW"]
    }
    timestamp checked_at?
    json source_refs
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "encounter_id", op: "asc"}]}
    {type: "btree", field: [{name: "lot_no", op: "asc"}]}
  ]

  tags = ["before", "evidence", "synthetic-only"]
  guid = "xiazyrmPHutLKkzzIaPCEUXp4Pk"
}
