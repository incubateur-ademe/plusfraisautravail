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

variable "public_read" {
  type        = bool
  default     = false
  description = "Allow anonymous s3:GetObject on every object (bucket ACL + policy). Use for media meant to be served directly, e.g. CMS uploads - not for buckets holding anything sensitive."
}
