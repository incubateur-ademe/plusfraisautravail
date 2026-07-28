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

output "cms_db_password" {
  value       = module.cms_db.password
  sensitive   = true
  description = "cms RDB password. Use `tofu output -raw cms_db_password` for one-off pg_restore/psql access."
}

output "cms_db_public_url" {
  value       = module.cms_db.database_url
  sensitive   = true
  description = "Full DSN over the public load-balancer endpoint. Use `tofu output -raw cms_db_public_url`."
}

output "cms_media_bucket" {
  value = module.cms_media.bucket_name
}

output "cms_manage_job_id" {
  value       = module.cms_manage.job_definition_id
  description = "Run with `scw jobs definition start $(tofu output -raw cms_manage_job_id)`."
}

# DNS records to create manually in OVH (the zone isn't managed by
# Terraform - see infra/README.md). Each custom_domain binding on the
# Scaleway side stays "pending" until the matching record exists and
# resolves, then Scaleway auto-issues the TLS cert.
#
# api.<base_domain> is a normal subdomain: a CNAME record works.
# <base_domain> itself is the zone apex - OVH (like all DNS providers)
# forbids a plain CNAME there. Use OVH's HTTPS-type DNS record in "Alias
# Mode" instead: priority 0, target = the cname_target value, settings
# left empty. See https://docs.ovhcloud.com/en/guides/web-cloud/domains/dns-zone-records
# ("Alias Mode" under the HTTPS/SVCB record types) - this is OVH's
# purpose-built apex-alias mechanism, not a workaround.
output "dns_records_to_create" {
  value = {
    (var.base_domain)        = "HTTPS record, priority 0 (Alias Mode) -> ${module.cms.cname_target}"
    "api.${var.base_domain}" = "CNAME -> ${module.api.cname_target}"
  }
  description = "Hostname -> required DNS record. Create these in the OVH DNS zone for plusfraisautravail.beta.gouv.fr."
}
