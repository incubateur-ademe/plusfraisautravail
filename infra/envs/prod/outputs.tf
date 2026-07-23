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

output "climadiag_bucket" {
  value = module.climadiag_site.bucket_name
}

output "climadiag_url" {
  value = "https://${module.climadiag_site.website_endpoint}"
}

output "api_registry" {
  value = "${scaleway_registry_namespace.pfat.endpoint}/api"
}

output "api_url" {
  value = "https://${module.api.domain_name}"
}

output "container_id" {
  value       = module.api.container_id
  description = "Scaleway serverless container ID (set as GitHub variable SCW_API_CONTAINER_ID)."
}

output "cms_registry" {
  value = "${scaleway_registry_namespace.pfat.endpoint}/cms"
}

output "cms_url" {
  value = "https://${module.cms.domain_name}"
}

output "cms_container_id" {
  value       = module.cms.container_id
  description = "Scaleway serverless container ID (set as GitHub variable SCW_CMS_CONTAINER_ID)."
}

output "cms_db_host" {
  value = module.cms_db.host
}

output "cms_media_bucket" {
  value = module.cms_media.bucket_name
}
