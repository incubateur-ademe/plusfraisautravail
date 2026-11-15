output "website_endpoint" {
  value       = scaleway_object_bucket_website_configuration.this.website_endpoint
  description = "HTTP website endpoint (no TLS without a CDN in front)."
}
