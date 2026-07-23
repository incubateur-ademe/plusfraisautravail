variable "region" {
  type    = string
  default = "fr-par"
}

variable "zone" {
  type    = string
  default = "fr-par-1"
}

variable "vigilance_app_id" {
  type        = string
  description = "Météo-France Vigilance API application ID."
  sensitive   = true
  default     = ""
}

variable "rte_client_id" {
  type        = string
  description = "RTE Ecowatt OAuth2 client ID. Leave empty to disable the /alerts/electricity endpoint (returns 503)."
  sensitive   = true
  default     = ""
}

variable "rte_client_secret" {
  type        = string
  description = "RTE Ecowatt OAuth2 client secret. Leave empty to disable the /alerts/electricity endpoint (returns 503)."
  sensitive   = true
  default     = ""
}

variable "rte_use_sandbox" {
  type        = bool
  description = "If true, the API hits the RTE sandbox endpoint instead of production. Defaults to false (prod)."
  default     = false
}

variable "api_image" {
  type        = string
  description = "Full image reference for the API container (e.g. rg.fr-par.scw.cloud/pfat/api:sha-abc123). Leave empty on first apply."
  default     = ""
}

variable "api_deploy" {
  type        = bool
  description = "Set to true once an image has been pushed to the registry."
  default     = false
}

variable "climadiag_api_token" {
  type        = string
  description = "X-AUTH-TOKEN for the PlusFraîcheMaVille Climadiag commune-search API. Leave empty to disable /climadiag/search (returns 503)."
  sensitive   = true
  default     = ""
}

variable "climadiag_api_url" {
  type        = string
  description = "PlusFraîcheMaVille Climadiag commune-search API URL."
  default     = "https://plusfraichemaville.fr/api/external-search-climadiag-info"
}

variable "extra_cors_origins" {
  type        = list(string)
  description = "Extra origins to whitelist on the API in addition to the bucket website domains and the canonical Wagtail host. Use for staging or custom domains."
  default     = []
}

variable "api_min_scale" {
  type        = number
  description = "Minimum number of always-warm API container instances. Set to 1 to eliminate cold-starts (the embed widget is triggered on every page load of the main site, so cold-start latency is user-visible)."
  default     = 1
}
