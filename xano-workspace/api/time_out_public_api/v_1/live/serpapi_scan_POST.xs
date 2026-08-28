// Live SerpApi scan, run FROM Xano so a judge sees the sponsor API called on demand.
// Results are alert CANDIDATES only. A search never establishes that a product is
// counterfeit, that a licence is invalid, or that the law has changed.
query "v1/live/serpapi-scan" verb=POST {
  api_group = "Time-Out Public API"

  input {
    text q? filters=trim
  }

  stack {
    var $query {
      value = ($input.q|strlen) > 0 ? $input.q : "site:fda.gov warning letter med spa botox Texas"
    }
  
    api.request {
      url = "https://serpapi.com/search"
      method = "GET"
      params = {
        engine : "google"
        q      : $query
        num    : 5
        api_key: $env.SERPAPI_KEY
      }
    
      timeout = 30
    } as $serp
  
    precondition ($serp.response.status == 200) {
      error_type = "notfound"
      error = "SerpApi did not return results. The synthetic sandbox stays usable; try again shortly."
    }
  
    var $candidates {
      value = ```
        $serp.response.result.organic_results|slice:0:5|map:{
                title      : $$.title
                source_url : $$.link
                snippet    : $$.snippet
                status     : "CANDIDATE"
              }
        ```
    }
  }

  response = {
    query     : $query
    count     : $candidates|count
    candidates: $candidates
    boundary  : "Search result only. A named human must confirm or dismiss each candidate before it changes an encounter."
    scope     : "Live SerpApi call executed by Xano at request time."
  }

  tags = ["before", "public", "live"]
  guid = "AehOfu2zc7EWzy_cmP4E86fPCTE"
}