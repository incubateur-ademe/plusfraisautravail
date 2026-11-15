variable "app_name" {
  type        = string
  description = "Logical app name (e.g. cms)."
}

variable "environment" {
  type        = string
  description = "Environment name (e.g. prod, staging)."
  default     = "prod"
}

variable "bucket_name" {
  type        = string
  description = "Globally-unique Object Storage bucket name."
}

variable "public_read" {
  type        = bool
  default     = false
  description = "Allow anonymous s3:GetObject on every object (bucket policy; listing stays denied). Use for media meant to be served directly, e.g. CMS uploads - not for buckets holding anything sensitive."
}

variable "public_read_prefixes" {
  type        = list(string)
  default     = ["*"]
  description = "Object key patterns anonymous s3:GetObject applies to when public_read is on. Keep anything permission-gated out (e.g. Wagtail documents/*, which Django must serve itself so collection privacy applies)."
}

variable "force_destroy" {
  type        = bool
  default     = false
  description = "Let tofu destroy the bucket with its objects. Only for buckets whose content can be rebuilt."
}
