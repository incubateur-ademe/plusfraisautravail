variable "app_name" {
  type        = string
  description = "Logical app name (e.g. autodiag, alert-widget)."
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. prod, staging)."
  default     = "prod"
}

variable "bucket_name" {
  type        = string
  description = "Globally-unique bucket name. Suggested: pfat-<app>-<environment>."
}

variable "region" {
  type        = string
  description = "Scaleway region."
  default     = "fr-par"
}

variable "tags" {
  type        = map(string)
  description = "Extra tags to merge onto the bucket."
  default     = {}
}
