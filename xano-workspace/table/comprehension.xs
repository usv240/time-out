// Versioned teach-back evidence bound to the same frozen rule snapshot.
table comprehension {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
  
    text question_set_version filters=trim
    text rule_snapshot_sha256? filters=trim|lower
    json items
    int score
    int threshold
    bool passed
    int attempts
    enum confidence {
      values = ["HIGH", "MEDIUM", "LOW"]
    }
  
    timestamp completed_at?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "encounter_id", op: "asc"}]
    }
  ]

  tags = ["before", "evidence"]
  guid = "XI2-G5_vYowotkmeyWHyUak3jVc"
}