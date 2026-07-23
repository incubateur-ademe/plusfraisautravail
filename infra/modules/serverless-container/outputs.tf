output "container_id" {
  value = scaleway_container.this.id
}

output "domain_name" {
  value       = scaleway_container.this.domain_name
  description = "Public domain name of the container."
}
