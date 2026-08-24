// Append-only state transition record. payload_hash makes retries and evidence linkage inspectable.
table audit_event {
  auth = false

  schema {
    int id
    timestamp created_at?=now
    int encounter_id {
      table = "encounter"
    }
    text actor filters=trim
    text action filters=trim
    enum from_state {
      values = ["DRAFT", "EVIDENCE_PENDING", "GATE_EVALUATED", "HUMAN_REVIEW", "REMEDIATION", "CONSENT_COMPILED", "BASELINE_CAPTURED", "AWAITING_ATTESTATION", "READY_FOR_PROCEDURE", "SEALED"]
    }
    enum to_state {
      values = ["DRAFT", "EVIDENCE_PENDING", "GATE_EVALUATED", "HUMAN_REVIEW", "REMEDIATION", "CONSENT_COMPILED", "BASELINE_CAPTURED", "AWAITING_ATTESTATION", "READY_FOR_PROCEDURE", "SEALED"]
    }
    text reason filters=trim
    text payload_hash filters=trim|lower
    json payload
    int encounter_version
  }

  index = [
    {type: "primary", field: [{name: "id"}]}
    {type: "btree", field: [{name: "encounter_id", op: "asc"}, {name: "created_at", op: "asc"}]}
  ]

  tags = ["before", "append-only", "audit"]
  guid = "46yKZDm6MZ_ZZVn3n-G8zat9u8A"
}
