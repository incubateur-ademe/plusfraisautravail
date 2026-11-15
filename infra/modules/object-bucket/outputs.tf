output "bucket_name" {
  value = scaleway_object_bucket.this.name
}

output "endpoint" {
  value       = "https://s3.${scaleway_object_bucket.this.region}.scw.cloud"
  description = "S3 API endpoint. Never served as a website (unlike the static-site module), regardless of public_read."
}
