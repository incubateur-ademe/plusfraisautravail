output "autodiag_url" {
  value = "https://${module.site["autodiag"].website_endpoint}"
}

output "alert_widget_url" {
  value = "https://${module.site["alert-widget"].website_endpoint}"
}

output "climadiag_url" {
  value = "https://${module.site["climadiag"].website_endpoint}"
}

# Names only, never the values: a key missing from the secret, or misspelt,
# shows in the plan of the pull request.
output "secret_names" {
  value = nonsensitive(keys(local.secrets))
}

output "cms_url" {
  value = trimsuffix(module.cms.public_endpoint, "/")
}

output "cms_db_host" {
  value = module.cms_db.host
}

output "cms_db_password" {
  value       = module.cms_db.password
  sensitive   = true
  description = "cms RDB password. Use `tofu output -raw cms_db_password` for one-off pg_restore/psql access."
}

output "cms_db_port" {
  value = module.cms_db.port
}

output "cms_db_name" {
  value = module.cms_db.database_name
}

output "bastion_ip" {
  value       = try(scaleway_vpc_public_gateway_ip.bastion[0].address, null)
  description = "SSH bastion to the database's Private Network, while `just bastion-up` keeps it (port 61000)."
}

output "cms_manage_url" {
  value       = module.cms_manage.public_endpoint
  description = "Private container: POST /run with an X-Auth-Token header (Scaleway IAM secret key) runs manage_jobs.sh."
}

# DNS records to create manually in OVH (the zone isn't managed by
# Terraform - see infra/README.md). Each custom_domain binding on the
# Scaleway side stays "pending" until the matching record exists and
# resolves, then Scaleway auto-issues the TLS cert.
#
# <base_domain> itself is the zone apex - OVH (like all DNS providers)
# forbids a plain CNAME there. Use OVH's HTTPS-type DNS record in "Alias
# Mode" instead: priority 0, target = the cname_target value, settings
# left empty. See https://docs.ovhcloud.com/en/guides/web-cloud/domains/dns-zone-records
# ("Alias Mode" under the HTTPS/SVCB record types) - this is OVH's
# purpose-built apex-alias mechanism, not a workaround.
output "dns_records_to_create" {
  value = {
    (local.base_domain) = "HTTPS record, priority 0 (Alias Mode) -> ${module.cms.cname_target}"
  }
  description = "Hostname -> required DNS record. Create these in the OVH DNS zone for plusfraisautravail.beta.gouv.fr."
}
