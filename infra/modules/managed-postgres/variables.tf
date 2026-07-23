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

variable "node_type" {
  type        = string
  description = "Scaleway RDB node class. DB-DEV-S is the smallest current class - fine for a low-traffic CMS."
  default     = "DB-DEV-S"
}

variable "engine" {
  type    = string
  default = "PostgreSQL-16"
}

variable "volume_type" {
  type        = string
  description = "Storage class for the instance volume."
  default     = "sbs_5k"
}

variable "volume_size_in_gb" {
  type    = number
  default = 10
}

variable "db_user" {
  type        = string
  description = "Superuser created on the instance. Changing this recreates the instance - pick it once."
  default     = "cms"
}

variable "db_name" {
  type    = string
  default = "cms"
}
