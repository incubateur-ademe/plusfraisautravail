variable "app_name" {
  type        = string
  description = "Logical app name (e.g. cms)."
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

variable "bucket_name" {
  type        = string
  description = "Globally-unique Object Storage bucket name."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Extra tags merged with the standard app/environment/managed_by set."
}
