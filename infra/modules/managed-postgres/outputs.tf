output "instance_id" {
  value = scaleway_rdb_instance.this.id
}

output "private_network_id" {
  value       = scaleway_vpc_private_network.this.id
  description = "Pass this to the serverless-container module's private_network_id so the app can reach the DB."
}

output "host" {
  value = scaleway_rdb_instance.this.private_network[0].ip
}

output "port" {
  value = scaleway_rdb_instance.this.private_network[0].port
}

output "database_name" {
  value = scaleway_rdb_database.this.name
}

output "user" {
  value = var.db_user
}

output "password" {
  value     = random_password.db.result
  sensitive = true
}

output "public_host" {
  value       = try(scaleway_rdb_instance.this.load_balancer[0].ip, null)
  description = "Public load-balancer IP for the RDB instance."
}

output "public_port" {
  value       = try(scaleway_rdb_instance.this.load_balancer[0].port, null)
  description = "Public load-balancer port."
}

output "database_url" {
  value = try(
    "postgresql://${var.db_user}:${random_password.db.result}@${scaleway_rdb_instance.this.load_balancer[0].ip}:${scaleway_rdb_instance.this.load_balancer[0].port}/${scaleway_rdb_database.this.name}?sslmode=require",
    "postgresql://${var.db_user}:${random_password.db.result}@${scaleway_rdb_instance.this.private_network[0].ip}:${scaleway_rdb_instance.this.private_network[0].port}/${scaleway_rdb_database.this.name}",
  )
  sensitive   = true
  description = "Full DSN - prefers the public load-balancer when available, falls back to private-network IP."
}
