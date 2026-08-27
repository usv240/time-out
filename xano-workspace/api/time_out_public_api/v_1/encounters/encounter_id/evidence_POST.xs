// Bound to explicit Gate enum contract.
// Post-schema function binding.
// Rebound to typed-status BEFORE functions.
// Bound after BEFORE v1 function revisions.
// Compiled after reusable BEFORE functions.
// Attach a typed, cached document extraction result. Low confidence routes to human review.
query "v1/encounters/{encounter_id}/evidence" verb=POST {
  api_group = "Time-Out Public API"

  input {
    text encounter_id filters=trim
    text kind filters=trim|upper
    text dws_file_id? filters=trim
    text cache_key? filters=trim
    json fields
    json confidence
    json page_coords
    enum review_status {
      values = ["PENDING", "HUMAN_REVIEW", "APPROVED", "REJECTED"]
    }
  
    text actor? filters=trim
  }

  stack {
    db.get encounter {
      field_name = "public_id"
      field_value = $input.encounter_id
    } as $encounter
  
    precondition ($encounter != null && $encounter.synthetic) {
      error_type = "notfound"
      error = "Synthetic encounter not found."
    }
  
    precondition ($encounter.state == "EVIDENCE_PENDING" || $encounter.state == "DRAFT") {
      error_type = "inputerror"
      error = "Evidence can only be attached while the encounter is DRAFT or EVIDENCE_PENDING."
    }
  
    db.add intake_doc {
      data = {
        created_at   : "now"
        encounter_id : $encounter.id
        kind         : $input.kind
        dws_file_id  : $input.dws_file_id
        cache_key    : $input.cache_key
        fields       : $input.fields
        confidence   : $input.confidence
        page_coords  : $input.page_coords
        review_status: $input.review_status
      }
    } as $document
  
    conditional {
      if ($encounter.state == "DRAFT") {
        function.run before_v1_transition {
          input = {
            encounter_id: $encounter.id
            to_state    : "EVIDENCE_PENDING"
            actor       : $input.actor
            action      : "evidence_attached"
            reason      : "Typed extraction attached to the synthetic encounter."
            payload     : {
            intake_doc_id: $document.id
            review_status: $input.review_status
          }
          }
        } as $pending_transition
      }
    }
  
    conditional {
      if ($input.review_status == "HUMAN_REVIEW") {
        function.run before_v1_transition {
          input = {
            encounter_id: $encounter.id
            to_state    : "HUMAN_REVIEW"
            actor       : $input.actor
            action      : "low_confidence_evidence"
            reason      : "Low-confidence extraction requires named-human sign-off."
            payload     : {intake_doc_id: $document.id}
          }
        } as $review_transition
      }
    }
  
    db.get encounter {
      field_name = "id"
      field_value = $encounter.id
    } as $current_encounter
  }

  response = {document: $document, encounter: $current_encounter}
  tags = ["before", "evidence", "human-review"]
  guid = "-9tm0Ixt2-k3RmFKZ2Uo2kjLtl8"
}