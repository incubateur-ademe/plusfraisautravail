variable "app_name" {
  type        = string
  description = "Logical app name (e.g. cms)."
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. prod, staging)."
  default     = "prod"
}
