output "container_id" {
  value = scaleway_container.this.id
}

output "domain_name" {
  value       = scaleway_container.this.domain_name
  description = "Public domain name of the container. Deprecated by the Scaleway provider in favor of public_endpoint - kept for backward compatibility with existing references."
}

output "public_endpoint" {
  value       = scaleway_container.this.public_endpoint
  description = "Full public URL of the container (scheme + domain)."
}

output "cname_target" {
  value       = var.custom_domain != "" ? trimsuffix(trimprefix(scaleway_container.this.public_endpoint, "https://"), "/") : null
  description = "Point custom_domain at this value in the external DNS zone (Scaleway only validates it, doesn't create it) - a CNAME record if custom_domain is a subdomain, or the provider's apex-alias record type if it's a bare zone apex (plain CNAME isn't valid there)."
}
