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

output "database_url" {
  value       = "postgresql://${var.db_user}:${random_password.db.result}@${scaleway_rdb_instance.this.private_network[0].ip}:${scaleway_rdb_instance.this.private_network[0].port}/${scaleway_rdb_database.this.name}"
  sensitive   = true
  description = "Full DSN - inject this straight into the container's secret_environment_variables.DATABASE_URL."
}
