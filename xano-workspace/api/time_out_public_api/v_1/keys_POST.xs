// Issue a caller tag on demand. No signup, no approval, no storage.
//
// This is deliberately NOT a credential. Every endpoint in this group works with no
// key at all and always will: the product's argument is that a judge, a clinic or a
// competitor can verify it without asking anyone's permission, and a key you have to
// hold would break that.
//
// What it is for: the audit log records an actor against every write. Passing this
// tag lets a caller find their own calls in that log later, instead of sharing the
// default "public-api" actor with everyone else. That is the whole feature.
query "v1/keys" verb=POST {
  api_group = "Time-Out Public API"

  input {
    // Optional human label, so a caller can tell two of their own tags apart.
    text label? filters=trim
  }

  stack {
    security.create_uuid as $tag_uuid

    // Xano hands an absent optional text through as "", not null, so ?? never fires.
    var $label {
      value = ((($input.label ?? "")|strlen) > 0) ? $input.label : "unlabelled"
    }

    // Reject anything shaped like real personal data, the same way remediate does.
    // A label is free text that lands in an audit log, so it gets the same guard.
    precondition (!(($input.label ?? "")|contains:"@")) {
      error_type = "inputerror"
      error = "A label must not look like an email address. This sandbox refuses real personal data."
    }

    // Unbounded free text was accepted: a 300 character label came back in full.
    // It is echoed in a response and can reach an audit log, so it gets a ceiling.
    precondition ((($input.label ?? "")|strlen) <= 64) {
      error_type = "inputerror"
      error = "A label must be 64 characters or fewer."
    }
  }

  response = {
    key                : "tok_demo_" ~ $tag_uuid
    label              : $label
    required           : false
    header             : "X-Time-Out-Key"
    what_it_does       : "Tags your calls in the append-only audit log so you can find them again."
    what_it_does_not_do: "It grants nothing and gates nothing. Every endpoint works without it."
    scope              : "Texas neurotoxin synthetic sandbox. Never send real patient data."
  }

  tags = ["before", "public", "synthetic-only"]
  guid = "iJUtDFv1DCgHYGDPJsRexCFKcxg"
}
