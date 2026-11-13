terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.73"
    }
  }
}

resource "scaleway_container_namespace" "this" {
  name        = "${var.app_name}-${var.environment}"
  description = "Container namespace for ${var.app_name} (${var.environment})."
  region      = var.region
}

resource "scaleway_container" "this" {
  name                         = "${var.app_name}-${var.environment}"
  namespace_id                 = scaleway_container_namespace.this.id
  image                        = var.registry_image
  port                         = var.port
  cpu_limit                    = var.cpu_limit
  memory_limit_bytes           = var.memory_limit * 1000000 # the API counts in MB
  min_scale                    = var.min_scale
  max_scale                    = var.max_scale
  timeout                      = var.timeout_seconds
  privacy                      = var.privacy
  protocol                     = "http1"
  https_connections_only       = false
  deploy                       = var.deploy
  private_network_id           = var.private_network_id != "" ? var.private_network_id : null
  environment_variables        = var.environment_variables
  secret_environment_variables = var.secret_environment_variables
  local_storage_limit_bytes    = var.local_storage_limit_bytes

  scaling_option {
    concurrent_requests_threshold = var.concurrent_requests_threshold
  }

  liveness_probe {
    http {
      path = var.health_check_path
    }
    failure_threshold = var.liveness_failure_threshold
    interval          = "30s"
    timeout           = "10s"
  }

  startup_probe {
    http {
      path = var.health_check_path
    }
    failure_threshold = 10
    interval          = "30s"
    timeout           = "10s"
  }

  # Image rollouts are owned by .github/workflows/cms.yml (PATCH on the
  # container API), not by tofu. Without this, every `tofu apply` would try to
  # revert the running image to whatever bootstrap reference is in
  # terraform.tfvars.
  lifecycle {
    ignore_changes = [image]
  }
}

# Scaleway validates that custom_domain resolves to this container before
# activating the binding, so the DNS record (see the cname_target output)
# must exist first - a subdomain gets a plain CNAME; a zone apex needs
# whatever apex-alias mechanism the DNS provider offers (e.g. OVH's HTTPS
# record in "Alias Mode", since CNAME isn't valid at an apex). This
# resource can be applied ahead of that and will just show as pending
# until the record exists and resolves.
resource "scaleway_container_domain" "this" {
  count        = var.custom_domain != "" ? 1 : 0
  container_id = scaleway_container.this.id
  hostname     = var.custom_domain
  region       = var.region
}
