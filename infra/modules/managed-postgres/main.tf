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

# Excludes every character that's structurally significant in a
# postgresql://user:PASSWORD@host:port/db DSN - @ : / # ? (URL structural
# chars) and [ ] (reserved for IPv6 literals) - since a password containing
# any of them silently corrupts DSN parsing instead of erroring loudly
# (confirmed: a stray '#' truncates the DSN mid-string and Django crashes on
# an unrelated line deep in settings import; '[' raises "Invalid IPv6 URL").
# Verified character-by-character against urllib.parse.urlparse. This
# password is only ever consumed programmatically (never typed by a human),
# so there's no reason to risk any of them.
resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!$%&*()-_=+{}<>"
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

  private_network {
    pn_id       = scaleway_vpc_private_network.this.id
    enable_ipam = true
  }

  load_balancer {}
}

resource "scaleway_rdb_database" "this" {
  instance_id = scaleway_rdb_instance.this.id
  name        = var.db_name
}
