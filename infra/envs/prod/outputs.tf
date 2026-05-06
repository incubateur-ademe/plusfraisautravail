output "autodiag_bucket" {
  value = module.autodiag_site.bucket_name
}

output "autodiag_url" {
  value = "https://${module.autodiag_site.website_endpoint}"
}

output "alert_widget_bucket" {
  value = module.alert_widget_site.bucket_name
}

output "alert_widget_url" {
  value = "https://${module.alert_widget_site.website_endpoint}"
}

output "api_registry" {
  value = module.api.registry_endpoint
}

output "api_url" {
  value = "https://${module.api.domain_name}"
}

output "container_id" {
  value       = module.api.container_id
  description = "Scaleway serverless container ID (set as GitHub variable SCW_API_CONTAINER_ID)."
}
