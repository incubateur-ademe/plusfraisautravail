terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.50"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

# Excludes @ and / - both break DSN parsing in a postgresql:// connection
# string, and this password is only ever consumed programmatically (never
# typed by a human), so there's no reason to risk it.
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "scaleway_vpc_private_network" "this" {
  name   = "${var.app_name}-${var.environment}"
  region = var.region
}

resource "scaleway_rdb_instance" "this" {
  name              = "${var.app_name}-${var.environment}"
  node_type         = var.node_type
  engine            = var.engine
  is_ha_cluster     = false
  disable_backup    = false
  volume_type       = var.volume_type
  volume_size_in_gb = var.volume_size_in_gb
  region            = var.region
  user_name         = var.db_user
  password          = random_password.db.result

  # enable_ipam lets Scaleway auto-assign the private IP - no manual
  # subnet/CIDR bookkeeping needed. This is the only network path to the
  # instance; there's no public load-balancer endpoint, so only resources
  # attached to this same Private Network (the cms container) can reach it.
  private_network {
    pn_id       = scaleway_vpc_private_network.this.id
    enable_ipam = true
  }
}

resource "scaleway_rdb_database" "this" {
  instance_id = scaleway_rdb_instance.this.id
  name        = var.db_name
}
