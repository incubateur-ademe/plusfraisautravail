terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.73"
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
  name = "${var.app_name}-${var.environment}"
}

resource "scaleway_rdb_instance" "this" {
  name              = "${var.app_name}-${var.environment}"
  node_type         = "DB-DEV-S" # the smallest class: fine for a low-traffic CMS
  engine            = "PostgreSQL-16"
  is_ha_cluster     = false
  disable_backup    = false
  volume_type       = "sbs_5k"
  volume_size_in_gb = 10
  user_name         = "cms" # changing it recreates the instance
  password          = random_password.db.result

  # Private Network only, no load_balancer (public endpoint): the CMS
  # containers reach it there, people through the on-demand SSH bastion.
  # An endpoint created before survives without it: see DEPLOY.md.
  private_network {
    pn_id       = scaleway_vpc_private_network.this.id
    enable_ipam = true
  }

  # The production data: a plan that would destroy or replace it fails.
  # Removing the whole module block is not caught (the rule goes with it).
  lifecycle {
    prevent_destroy = true
  }
}

resource "scaleway_rdb_database" "this" {
  instance_id = scaleway_rdb_instance.this.id
  name        = "cms"

  lifecycle {
    prevent_destroy = true
  }
}
