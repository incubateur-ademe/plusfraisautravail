output "bucket_name" {
  value = scaleway_object_bucket.this.name
}

output "bucket_id" {
  value = scaleway_object_bucket.this.id
}

output "endpoint" {
  value       = "https://s3.${var.region}.scw.cloud"
  description = "S3 API endpoint (this bucket is private and never served as a website, unlike the static-site module)."
}
