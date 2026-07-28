variable "app_name" {
  type        = string
  description = "Logical app name (e.g. api)."
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. prod, staging)."
  default     = "prod"
}

variable "region" {
  type        = string
  description = "Scaleway region."
  default     = "fr-par"
}

variable "registry_image" {
  type        = string
  description = "Full image reference. Must already exist in the registry, even on first apply - Scaleway validates the image at container-create time regardless of `deploy`."
  default     = ""
}

variable "deploy" {
  type        = bool
  description = "Whether to roll the container out to traffic. Does not affect image validation - `registry_image` must exist in the registry either way."
  default     = false
}

variable "port" {
  type    = number
  default = 8080
}

variable "cpu_limit" {
  type        = number
  description = "CPU limit (mvCPU). 140 = 0.14 vCPU."
  default     = 280
}

variable "memory_limit" {
  type        = number
  description = "Memory limit (MiB)."
  default     = 512
}

variable "min_scale" {
  type    = number
  default = 0
}

variable "max_scale" {
  type    = number
  default = 5
}

variable "timeout_seconds" {
  type    = number
  default = 300
}

variable "environment_variables" {
  type        = map(string)
  default     = {}
  description = "Plain-text env vars."
}

variable "secret_environment_variables" {
  type        = map(string)
  default     = {}
  sensitive   = true
  description = "Secret env vars (e.g. VIGILANCE_APP_ID)."
}

variable "private_network_id" {
  type        = string
  default     = ""
  description = "Private Network ID to attach the container to (e.g. for a DB reachable only over the private network). Leave empty for public-only containers like api."
}

variable "health_check_path" {
  type        = string
  default     = "/healthz/"
  description = "HTTP path for liveness and startup probes."
}

variable "custom_domain" {
  type        = string
  default     = ""
  description = "Custom hostname to bind to the container (e.g. api.example.com, or a bare zone apex like example.com). Requires a DNS record pointing this hostname at the container's public_endpoint to already exist first - a CNAME for a subdomain, or the DNS provider's apex-alias equivalent for a bare domain. See the cname_target output. Leave empty to skip."
}
