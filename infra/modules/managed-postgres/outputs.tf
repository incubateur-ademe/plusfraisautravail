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

# Password is percent-encoded: the generated one contains URL-reserved
# characters and consumers (dj-database-url, libpq) decode a URI password.
output "private_database_url" {
  value       = "postgresql://${var.db_user}:${urlencode(random_password.db.result)}@${scaleway_rdb_instance.this.private_network[0].ip}:${scaleway_rdb_instance.this.private_network[0].port}/${scaleway_rdb_database.this.name}?sslmode=require"
  sensitive   = true
  description = "Private-network DSN — use when the container is attached to the same VPC as the RDB instance."
}
