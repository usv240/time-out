// Live name.com read-back, run FROM Xano. Reads the receipt's published TXT record
// through the CORE sandbox API and compares it to the digest the caller holds.
// Sandbox DNS does not propagate publicly and a TXT record is mutable by its owner:
// this is a verification channel, not a notary.
query "v1/live/receipt-verify" verb=POST {
  api_group = "Time-Out Public API"

  input {
    text host? filters=trim
    text digest? filters=trim
  }

  stack {
    var $domain {
      value = "timeout-receipts-demo.com"
    }
  
    var $want_host {
      value = ($input.host|strlen) > 0 ? $input.host : "receipt-syn-enc-blocked-002"
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
      error = "name.com sandbox did not answer. Cached verification remains available on the receipt page."
    }
  
    var $record {
      value = $dns.response.result.records|filter:($$.host == $want_host && $$.type == "TXT")|first
    }
  
    var $matches {
      value = ($input.digest|strlen) > 0 ? ($record.answer|contains:$input.digest) : false
    }
  }

  response = {
    published: $record != null
    matches  : $matches
    fqdn     : $record.fqdn
    answer   : $record.answer
    domain   : $domain
    scope    : "Live name.com CORE sandbox read-back executed by Xano at request time."
    caveat   : "Sandbox DNS does not propagate to public resolvers and a TXT record is mutable by its owner. This is a verification channel, not an immutable notary."
  }

  tags = ["before", "public", "live"]
  guid = "NPILIzDNmiJ_DH6lI9ZvWQZb_CE"
}