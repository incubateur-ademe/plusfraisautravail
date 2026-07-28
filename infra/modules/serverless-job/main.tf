terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = ">= 2.73"
    }
  }
}

# One-shot job definition - reuses the same image as the app's
# serverless-container (e.g. module.cms), just with a different startup
# command (manage.py instead of gunicorn). Applying this only registers the
# definition; nothing runs until you trigger it:
#   scw jobs definition start <job_definition_id>
resource "scaleway_job_definition" "this" {
  name         = "${var.app_name}-${var.environment}"
  cpu_limit    = var.cpu_limit
  memory_limit = var.memory_limit
  # Scaleway Jobs bill/allocate ephemeral disk separately from memory; the
  # manage.py commands this runs don't write large files, so the provider
  # minimum is enough.
  local_storage_capacity = var.local_storage_capacity
  image_uri              = var.registry_image
  command                = var.command
  region                 = var.region
  # No secret_reference blocks (Secret Manager) - this project doesn't use
  # Secret Manager elsewhere, and `env` here is the same plain Terraform map
  # already used for scaleway_container.secret_environment_variables, so
  # reusing it keeps one secret-handling story instead of two.
  env     = var.environment_variables
  timeout = "${var.timeout_seconds}s"
}
