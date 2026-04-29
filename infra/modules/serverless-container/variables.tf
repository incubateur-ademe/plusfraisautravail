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

variable "registry_namespace" {
  type        = string
  description = "Scaleway Container Registry namespace name."
}

variable "registry_image" {
  type        = string
  description = "Full image reference. Use a placeholder on first apply (deploy = false), then update once the image has been pushed."
  default     = ""
}

variable "deploy" {
  type        = bool
  description = "Whether to deploy the container. Set to false on first apply (no image pushed yet)."
  default     = false
}

variable "port" {
  type        = number
  default     = 8080
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
  type        = number
  default     = 0
}

variable "max_scale" {
  type        = number
  default     = 5
}

variable "timeout_seconds" {
  type        = number
  default     = 60
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
