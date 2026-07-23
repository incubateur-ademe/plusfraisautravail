variable "region" {
  type    = string
  default = "fr-par"
}

variable "zone" {
  type    = string
  default = "fr-par-1"
}

# ponytail: only needed so cms's container can reuse the same account key as
# S3 media credentials (see cms_secret_env in main.tf) - not read by the
# provider block itself, which still auths via the SCW_ACCESS_KEY/
# SCW_SECRET_KEY env vars directly. Duplicated here on purpose so the value
# can be re-injected into a resource; TF_VAR_* env vars populate these the
# same way they populate every other secret in this file.
variable "scw_access_key" {
  type        = string
  description = "Scaleway access key - reused as the cms container's S3 media credentials until a bucket-scoped IAM key can be created (see infra/modules/object-bucket)."
  sensitive   = true
  default     = ""
}

variable "scw_secret_key" {
  type        = string
  description = "Scaleway secret key - reused as the cms container's S3 media credentials until a bucket-scoped IAM key can be created (see infra/modules/object-bucket)."
  sensitive   = true
  default     = ""
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
  # TEMPORARY: pointed at staging because the only X-AUTH-TOKEN we have so far
  # is staging-only (401s against the prod host). Switch back to
  # https://plusfraichemaville.fr/api/external-search-climadiag-info once PFMV
  # issues a production token.
  default = "https://staging.plusfraichemaville.fr/api/external-search-climadiag-info"
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

variable "django_secret_key" {
  type        = string
  description = "Django SECRET_KEY for the cms app. Generate with: python -c \"import secrets; print(secrets.token_urlsafe(50))\""
  sensitive   = true
  default     = ""
}

variable "cms_image" {
  type        = string
  description = "Full image reference for the cms container (e.g. rg.fr-par.scw.cloud/pfat/cms:sha-abc123). Leave empty on first apply."
  default     = ""
}

variable "cms_deploy" {
  type        = bool
  description = "Set to true once an image has been pushed to the registry."
  default     = false
}

variable "cms_min_scale" {
  type        = number
  description = "Minimum number of always-warm cms container instances. 0 is fine here (unlike api_min_scale) - a CMS admin backend isn't hit on every page load of the public site, so occasional cold starts are acceptable."
  default     = 0
}

variable "cms_db_node_type" {
  type        = string
  description = "Scaleway RDB node class for the cms Postgres instance."
  default     = "DB-DEV-S"
}

variable "cms_extra_allowed_hosts" {
  type        = list(string)
  description = "Hostnames for Django's ALLOWED_HOSTS. The container's own Scaleway domain isn't knowable until after the first apply (it would create a dependency cycle) - set it here from `tofu output cms_url` after the first apply, then re-apply. Also add any custom domain here once one is set up."
  default     = []
}
