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
  description = "Globally-unique bucket name. Here: pfat-<app>."
}
