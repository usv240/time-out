// Temporary: confirms the sponsor credentials are readable from Xano. Presence only, never values.
query "v1/live/envcheck" verb=GET {
  api_group = "Time-Out Public API"

  input {
  }

  stack {
  }

  response = {
    serpapi       : $env.SERPAPI_KEY|strlen
    nutrient      : $env.NUTRIENT_EXTRACTION_API_KEY|strlen
    namecom_user  : $env.NAMECOM_USERNAME|strlen
    namecom_token : $env.NAMECOM_TOKEN|strlen
    namecom_base  : $env.NAMECOM_BASE_URL
    namecom_domain: $env.NAMECOM_REGISTRY_DOMAIN
  }

  tags = ["before", "public"]
  guid = "ZIZg7gPE9KVUsY4IFC0yNjLVFRw"
}