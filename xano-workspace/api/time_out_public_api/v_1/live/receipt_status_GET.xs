// Live receipt status, read FROM Xano so no name.com credential reaches a browser.
//
// A receipt carries two records on the clinic's own domain, answering two different
// questions:
//   _timeout.<receipt-id>  the digest  — is this the receipt that was issued?
//   _status.<receipt-id>   the status  — is it still good?
//
// Conflating them is how a stale record ends up looking authoritative. A missing
// status record resolves to UNKNOWN, never to valid: an unpublished receipt and a
// good one must not look the same to a patient.
query "v1/live/receipt-status" verb=GET {
  api_group = "Time-Out Public API"

  input {
    text receipt_id? filters=trim
    text domain? filters=trim
  }

  stack {
    // The clinic's own verification domain, provisioned during onboarding.
    var $domain {
      value = ($input.domain|strlen) > 0 ? $input.domain : "cedarparkaesthetics.com"
    }

    var $receipt {
      value = ($input.receipt_id|strlen) > 0 ? $input.receipt_id : "SYN-RECEIPT-SYN-ENC-BLOCKED-002"
    }

    var $want_host {
      value = "_status." ~ ($receipt|to_lower)
    }

    api.request {
      url = $env.NAMECOM_BASE_URL ~ "/core/v1/domains/" ~ $domain ~ "/records"
      method = "GET"
      headers = [
        "Authorization: Basic " ~ ($env.NAMECOM_USERNAME ~ ":" ~ $env.NAMECOM_TOKEN|base64_encode)
      ]

      timeout = 30
    } as $dns

    precondition ($dns.response.status == 200) {
      error_type = "notfound"
      error = "name.com sandbox did not answer. The receipt page keeps its cached state."
    }

    var $record {
      value = $dns.response.result.records|filter:($$.host == $want_host && $$.type == "TXT")|first
    }

    var $answer {
      value = $record == null ? "" : $record.answer
    }

    var $status {
      value = ($answer|contains:"status=REVOKED") ? "REVOKED" : (($answer|contains:"status=VALID") ? "VALID" : "UNKNOWN")
    }

    var $reason_token {
      value = $record == null ? null : ($answer|split:" "|filter:($$|starts_with:"reason=")|first)
    }

    var $at_token {
      value = $record == null ? null : ($answer|split:" "|filter:($$|starts_with:"at=")|first)
    }
  }

  response = {
    found   : $record != null
    status  : $status
    reason  : $reason_token == null ? "" : ($reason_token|replace:"reason=":"")
    at      : $at_token == null ? "" : ($at_token|replace:"at=":"")
    domain  : $domain
    fqdn    : $record.fqdn
    answer  : $answer
    source  : "Live name.com CORE sandbox read executed by Xano at request time."
    note    : "A missing status record reports UNKNOWN, never valid. Absence is not validity."
    caveat  : "A status record says whether this receipt is still current. It does not certify that the procedure was safe, and it stays mutable by whoever owns the domain."
  }

  tags = ["before", "public", "live"]
  guid = "KSaKkFsSshK5RjdGPKxWqI2SPAI"
}
