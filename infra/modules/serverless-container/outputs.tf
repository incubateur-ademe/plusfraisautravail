output "registry_endpoint" {
  value       = scaleway_registry_namespace.this.endpoint
  description = "Container registry endpoint (push images here)."
}

output "registry_namespace_id" {
  value       = scaleway_registry_namespace.this.id
}

output "container_id" {
  value       = scaleway_container.this.id
}

output "domain_name" {
  value       = scaleway_container.this.domain_name
  description = "Public domain name of the container."
}
