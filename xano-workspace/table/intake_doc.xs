// Cached typed extraction result. Low confidence remains pending until named human review.
table intake_doc {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
  
    text kind filters=trim|upper
    text dws_file_id? filters=trim
    text cache_key? filters=trim
    json fields
    json confidence
    json page_coords
    enum review_status {
      values = ["PENDING", "HUMAN_REVIEW", "APPROVED", "REJECTED"]
    }
  
    text reviewer_id? filters=trim
    timestamp reviewed_at?
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "encounter_id", op: "asc"}]}
    {type: "btree", field: [{name: "review_status", op: "asc"}]}
  ]

  tags = ["before", "evidence"]
  guid = "tB5B0u3htkqHfKyd-Mn6_xYfcAs"
}