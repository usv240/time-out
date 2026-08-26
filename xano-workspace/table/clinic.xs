// Synthetic Texas clinic context. BEFORE never stores real clinic data in the demo workspace.
table clinic {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text synthetic_key filters=trim
    text name filters=trim
    text state filters=trim|upper
    text license_no? filters=trim
    int medical_director_id? {
      table = "provider"
    }
  
    bool synthetic
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {
      type : "btree|unique"
      field: [{name: "synthetic_key", op: "asc"}]
    }
    {type: "btree", field: [{name: "created_at", op: "desc"}]}
  ]

  tags = ["before", "synthetic-only"]
  guid = "aaZhWKXg24hZE7pUu05l9EQKezg"
}