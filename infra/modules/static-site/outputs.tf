output "bucket_name" {
  value       = scaleway_object_bucket.this.name
  description = "Name of the bucket."
}

output "bucket_id" {
  value       = scaleway_object_bucket.this.id
  description = "Scaleway bucket resource ID."
}

output "website_endpoint" {
  value       = scaleway_object_bucket_website_configuration.this.website_endpoint
  description = "HTTP website endpoint (no TLS without a CDN in front)."
}

output "website_domain" {
  value       = scaleway_object_bucket_website_configuration.this.website_domain
  description = "Website endpoint domain (e.g. <bucket>.s3-website.<region>.scw.cloud)."
}
