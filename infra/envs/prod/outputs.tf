output "autodiag_bucket" {
  value = module.autodiag_site.bucket_name
}

output "autodiag_url" {
  value = "https://${module.autodiag_site.website_domain}"
}

output "alert_widget_bucket" {
  value = module.alert_widget_site.bucket_name
}

output "alert_widget_url" {
  value = "https://${module.alert_widget_site.website_domain}"
}

output "api_registry" {
  value = module.api.registry_endpoint
}

output "api_url" {
  value = "https://${module.api.domain_name}"
}
