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

variable "registry_image" {
  type        = string
  description = "Full image reference. Reuse the same image as the app's serverless-container - same code, different command."
}

variable "startup_command" {
  type        = list(string)
  description = "Argv, e.g. [\"./manage_jobs.sh\"] or [\"python\", \"manage.py\", \"set_s3_cache_control\"]. Exec'd directly (no shell) - overrides the image's ENTRYPOINT. Chain multiple commands in a script baked into the image rather than a single \"cmd1 && cmd2\" string."
}

variable "cpu_limit" {
  type        = number
  description = "CPU limit (mvCPU). 140 = 0.14 vCPU."
  default     = 560
}

variable "memory_limit" {
  type        = number
  description = "Memory limit (MiB)."
  default     = 1024
}

variable "local_storage_capacity" {
  type        = number
  description = "Ephemeral local storage (MiB). Required by the provider even when the job writes nothing to disk."
  default     = 1024
}

variable "timeout_seconds" {
  type        = number
  default     = 300
  description = "Max job run duration in seconds before Scaleway kills it."
}

variable "environment_variables" {
  type        = map(string)
  default     = {}
  sensitive   = true
  description = "Env vars, including secrets (DB URL, AWS keys, ...) - scaleway_job_definition has no separate secret_environment_variables argument, unlike scaleway_container."
}
