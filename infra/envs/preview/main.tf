# Preview of a pull request: its own database, user and media bucket, and one
# public container running the CMS of the PR (apps/cms/Dockerfile.preview).
# One workspace per pull request (pr-<number>), applied by
# .github/workflows/preview.yml, destroyed by a manual run of it.
terraform {
  required_version = ">= 1.10"
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.92"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
  # Same bucket as infra/envs/prod; each workspace has its own state under env:/.
  backend "s3" {
    bucket       = "pfat-terraform"
    key          = "envs/preview/terraform.tfstate"
    region       = "fr-par"
    use_lockfile = true
    endpoints = {
      s3 = "https://s3.fr-par.scw.cloud"
    }
    skip_credentials_validation = true
    skip_region_validation      = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
    skip_s3_checksum            = true
    use_path_style              = true
  }
}

provider "scaleway" {
  region = "fr-par"
  zone   = "fr-par-1"
}

variable "image" {
  type        = string
  description = "Preview image the container is created with. Later images are rolled out by preview.yml."
}

locals {
  # pr-12 -> preview_pr_12: PostgreSQL names take no dash.
  name     = "preview_${replace(terraform.workspace, "-", "_")}"
  instance = data.scaleway_rdb_instance.production.private_network[0]
  # Over the Private Network, as the preview user; %s is the database.
  database_url = "postgresql://${scaleway_rdb_user.preview.name}:${random_password.database.result}@${local.instance.ip}:${local.instance.port}/%s?sslmode=require"
  # The production database (modules/managed-postgres), which a preview must not reach.
  production_database = "cms"
}

# Fails the plan in any other workspace: `default` would create cms-default.
# Not a precondition of the output, which would also fail `tofu validate`.
resource "terraform_data" "workspace" {
  lifecycle {
    precondition {
      condition     = can(regex("^pr-[0-9]+$", terraform.workspace))
      error_message = "Select the workspace of the pull request first: tofu workspace select -or-create pr-<number>."
    }
  }
}

# ── Database: on the production instance, behind its own user ────────────
data "scaleway_rdb_instance" "production" {
  name = "cms-prod"
}

resource "scaleway_rdb_database" "preview" {
  instance_id = data.scaleway_rdb_instance.production.id
  name        = local.name
  # Destroyed before its user, who owns its tables.
  depends_on = [scaleway_rdb_user.preview]
}

resource "random_password" "database" {
  length  = 32
  special = false # goes into a URL as it is
}

resource "scaleway_rdb_user" "preview" {
  instance_id = data.scaleway_rdb_instance.production.id
  name        = local.name
  password    = random_password.database.result
  is_admin    = false
}

# A new user has no permission on any database: "all" on its own only. That it
# is denied production's is checked by the container at each start
# (apps/cms/preview_entrypoint.sh).
resource "scaleway_rdb_privilege" "preview" {
  instance_id   = data.scaleway_rdb_instance.production.id
  user_name     = scaleway_rdb_user.preview.name
  database_name = scaleway_rdb_database.preview.name
  permission    = "all"

  # Scaleway reports "custom" once the restore has created tables, and the
  # provider would set "all" again at each push.
  lifecycle {
    ignore_changes = [permission]
  }
}

# ── Media: its own bucket, filled from production's by preview.yml ───────
module "media" {
  source               = "../../modules/object-bucket"
  app_name             = "cms"
  environment          = terraform.workspace
  bucket_name          = "pfat-preview-${terraform.workspace}"
  public_read          = true
  public_read_prefixes = ["images/*", "original_images/*"] # as production's
  force_destroy        = true
}

# A key that reaches the preview buckets only (DEPLOY.md 4): never the
# account's key nor production's media key, in a container running unreviewed
# code next to the production database.
data "scaleway_secret_version" "media" {
  for_each    = toset(["access-key-id", "secret-key"])
  secret_name = "pfat-preview-media-${each.key}"
  # Disabling a version rolls back to the one before.
  revision = "latest_enabled"

  lifecycle {
    postcondition {
      condition     = trimspace(base64decode(self.data)) != ""
      error_message = "The secret pfat-preview-media-${each.key} is empty: it must hold a Scaleway key restricted to the preview buckets."
    }
  }
}

resource "random_password" "django_secret_key" {
  length  = 64
  special = false
}

module "cms" {
  source             = "../../modules/serverless-container"
  app_name           = "cms"
  environment        = terraform.workspace
  registry_image     = var.image
  private_network_id = local.instance.pn_id
  health_check_path  = "/"
  # Stopped while nobody looks at it.
  min_scale    = 0
  max_scale    = 1
  cpu_limit    = 1000
  memory_limit = 2048
  environment_variables = {
    # Scaleway's probes do not send the container's domain as Host (see prod).
    ALLOWED_HOSTS           = jsonencode(["*"])
    AWS_STORAGE_BUCKET_NAME = module.media.bucket_name
    AWS_S3_ENDPOINT_URL     = module.media.endpoint
    AWS_S3_REGION_NAME      = "fr-par"
    # Media straight from the bucket: production's go through its nginx proxy.
    AWS_S3_CUSTOM_DOMAIN = "${module.media.bucket_name}.s3.fr-par.scw.cloud"
  }
  # No API, Notion, e-mail, Sentry or PostHog secret.
  secret_environment_variables = {
    DATABASE_URL            = format(local.database_url, local.name)
    PRODUCTION_DATABASE_URL = format(local.database_url, local.production_database)
    DJANGO_SECRET_KEY       = random_password.django_secret_key.result
    AWS_ACCESS_KEY_ID       = trimspace(base64decode(data.scaleway_secret_version.media["access-key-id"].data))
    AWS_SECRET_ACCESS_KEY   = trimspace(base64decode(data.scaleway_secret_version.media["secret-key"].data))
  }
  # The user exists and has its permissions before the container starts.
  depends_on = [scaleway_rdb_privilege.preview]
}

output "url" {
  value = trimsuffix(module.cms.public_endpoint, "/")
}

output "media_bucket" {
  value = module.media.bucket_name
}
