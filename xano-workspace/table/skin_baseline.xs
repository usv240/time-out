// Standardized synthetic baseline capture metadata; never a real person's face in this workspace.
table skin_baseline {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
    json capture_meta
    json concerns
    text overlay_url? filters=trim
    timestamp captured_at
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "encounter_id", op: "asc"}]}
  ]

  tags = ["before", "evidence", "synthetic-only"]
  guid = "2ssrAeAa4VgJDDHc4IGI8KVk8Wc"
}
