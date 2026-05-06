terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.50"
    }
  }
}

resource "scaleway_registry_namespace" "this" {
  name      = var.registry_namespace
  region    = var.region
  is_public = false
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
  deploy                       = var.deploy
  environment_variables        = var.environment_variables
  secret_environment_variables = var.secret_environment_variables
}
