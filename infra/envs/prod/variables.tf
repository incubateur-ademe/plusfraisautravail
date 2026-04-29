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
}

variable "api_image" {
  type        = string
  description = "Full image reference for the API container (e.g. rg.fr-par.scw.cloud/pfat-prod/api:sha-abc123). Leave empty on first apply."
  default     = ""
}

variable "api_deploy" {
  type        = bool
  description = "Set to true once an image has been pushed to the registry."
  default     = false
}
