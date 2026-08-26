// Search result awaiting named-human confirmation; a candidate alone is never a finding of fact.
table alert_candidate {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id? {
      table = "encounter"
    }
  
    text source_url filters=trim
    timestamp published_at?
    text matched_entity filters=trim
    enum status {
      values = ["CANDIDATE", "CONFIRMED", "DISMISSED"]
    }
  
    text confirmed_by? filters=trim
    timestamp confirmed_at?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "encounter_id", op: "asc"}]}
    {type: "btree", field: [{name: "status", op: "asc"}]}
  ]

  tags = ["before", "human-review"]
  guid = "1IyCecJ2-qea1PLo1WHY9gPPOyo"
}