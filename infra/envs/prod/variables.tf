# Not secret: GitHub repository variables in CI (infrastructure.yml),
# terraform.tfvars locally.
variable "cms_base_url" {
  type        = string
  default     = ""
  description = "Public origin the CMS builds absolute URLs on (WAGTAILADMIN_BASE_URL). Empty = the production domain. Set to the Scalingo proxy URL while testing before the DNS cutover."
}

variable "sentry_dsn" {
  type        = string
  default     = ""
  description = "Sentry DSN (sentry.incubateur.net) for the cms container (which also serves /api/). Empty disables Sentry."
}

variable "posthog_key" {
  type        = string
  default     = ""
  description = "PostHog project key rendered into every page by sites-conformes-posthog. Empty disables analytics."
}

variable "bastion_enabled" {
  type        = bool
  default     = false
  description = "Create the on-demand SSH bastion to the database's Private Network (`just bastion-up`)."
}

variable "bastion_allowed_ip_ranges" {
  type        = list(string)
  default     = []
  description = "IP ranges allowed to reach the SSH bastion, e.g. [\"203.0.113.7/32\"]. Required with bastion_enabled: without it the bastion would be open to the Internet."
}
