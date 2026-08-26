// Append-only deterministic safety determination for human review.
table gate_decision {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
  
    enum verdict {
      values = ["CLEAR", "BLOCKED", "REVIEW"]
    }
  
    text determination_scope filters=trim
    json findings
    json rule_snapshot
    text canonical_rule_snapshot
    text rule_snapshot_sha256 filters=trim|lower
    timestamp evaluated_at
    text created_by filters=trim
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree"
      field: [
        {name: "encounter_id", op: "asc"}
        {name: "evaluated_at", op: "desc"}
      ]
    }
    {
      type : "btree"
      field: [{name: "rule_snapshot_sha256", op: "asc"}]
    }
  ]

  tags = ["before", "append-only", "human-review"]
  guid = "XLCZ3KkgXcxWKtu3AOVsCfKWfoo"
}