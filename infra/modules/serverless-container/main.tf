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
  registry_image               = var.registry_image
  port                         = var.port
  cpu_limit                    = var.cpu_limit
  memory_limit                 = var.memory_limit
  min_scale                    = var.min_scale
  max_scale                    = var.max_scale
  timeout                      = var.timeout_seconds
  privacy                      = "public"
  protocol                     = "http1"
  http_option                  = "enabled"
  deploy                       = var.deploy
  private_network_id           = var.private_network_id != "" ? var.private_network_id : null
  environment_variables        = var.environment_variables
  secret_environment_variables = var.secret_environment_variables

  liveness_probe {
    http {
      path = var.health_check_path
    }
    # ponytail: bumped from 5 to 20 while debugging cms-prod never passing
    # its startup probe - revert once root-caused.
    failure_threshold = 20
    interval          = "30s"
    timeout           = "10s"
  }

  startup_probe {
    http {
      path = var.health_check_path
    }
    # ponytail: bumped from 10 to 20, same reason as liveness_probe above.
    failure_threshold = 20
    interval          = "30s"
    timeout           = "10s"
  }

  # Image rollouts are owned by deploy-api.yml / deploy-cms.yml (PATCH on the
  # container API), not by tofu. Without this, every `tofu apply` would try to
  # revert the running image to whatever bootstrap reference is in
  # terraform.tfvars.
  lifecycle {
    ignore_changes = [registry_image]
  }
}
