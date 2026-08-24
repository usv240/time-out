// Human-reviewed rules-as-code. canonical_rule_snapshot is immutable once used by a decision.
table jurisdiction_rule {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    text rule_id filters=trim
    text state filters=trim|upper
    text procedure_category filters=trim|upper
    json direct_performer_credentials
    json delegated_path_credentials
    json credential_interpretation_review
    json required_evidence
    text supervision_model filters=trim
    json citation_urls
    text source filters=trim
    timestamp verified_at
    enum confidence {
      values = ["HIGH", "MEDIUM", "LOW"]
    }
    json rule_snapshot
    text canonical_rule_snapshot
    text rule_snapshot_sha256 filters=trim|lower
    bool active
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree|unique", field: [{name: "rule_id", op: "asc"}]}
    {type: "btree", field: [{name: "state", op: "asc"}, {name: "procedure_category", op: "asc"}]}
  ]

  tags = ["before", "rules-as-code"]
  guid = "GgudYgK544Cb-RaBBNEDoW4K3hA"
}
