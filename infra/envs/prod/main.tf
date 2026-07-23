locals {
  environment = "prod"

  # Only pass secrets that are actually set; an empty secret env var on a
  # Scaleway container is still a real env var pointing at nothing, which the
  # API would happily try to use. Use a conditional map and merge.
  api_secret_env = merge(
    var.vigilance_app_id == "" ? {} : { VIGILANCE_APP_ID = var.vigilance_app_id },
    var.rte_client_id == "" ? {} : { RTE_CLIENT_ID = var.rte_client_id },
    var.rte_client_secret == "" ? {} : { RTE_CLIENT_SECRET = var.rte_client_secret },
    var.climadiag_api_token == "" ? {} : { CLIMADIAG_API_TOKEN = var.climadiag_api_token },
  )

  api_env = {
    RTE_USE_SANDBOX   = var.rte_use_sandbox ? "true" : "false"
    CLIMADIAG_API_URL = var.climadiag_api_url
    # JSON-encoded list - pydantic-settings parses this as list[str].
    # Includes the deployed alert-widget/climadiag bucket origins so the
    # embeds can call the API without a CORS preflight failure.
    CORS_ORIGINS = jsonencode(concat(
      [
        "http://localhost:5173",
        "http://localhost:4173",
        "https://plusfraisautravail.beta.gouv.fr",
        # website_endpoint is "<bucket>.s3-website.<region>.scw.cloud" (with bucket).
        # website_domain is the region-only suffix - using it here would give an
        # origin that matches every bucket in the region, which is wrong.
        "https://${module.alert_widget_site.website_endpoint}",
        "https://${module.autodiag_site.website_endpoint}",
        "https://${module.climadiag_site.website_endpoint}",
      ],
      var.extra_cors_origins,
    ))
  }

  cms_secret_env = {
    DATABASE_URL      = module.cms_db.database_url
    DJANGO_SECRET_KEY = var.django_secret_key
    # ponytail: reusing the same account-wide Scaleway key already used for
    # tofu apply, rather than a bucket-scoped IAM application/key - the
    # deploying key doesn't have IAM write permission yet. Narrow this once
    # it does (see infra/modules/object-bucket/main.tf).
    AWS_ACCESS_KEY_ID     = var.scw_access_key
    AWS_SECRET_ACCESS_KEY = var.scw_secret_key
  }

  cms_env = {
    # Can't include module.cms.domain_name here - it's only known after the
    # container is created, and the container's env vars are set at create
    # time, so referencing it back would be a dependency cycle. Add the
    # Scaleway-assigned domain to cms_extra_allowed_hosts once you have it
    # (from `tofu output cms_url`) and re-apply, same as the api_image /
    # api_deploy bootstrap two-step.
    ALLOWED_HOSTS           = jsonencode(var.cms_extra_allowed_hosts)
    AWS_STORAGE_BUCKET_NAME = module.cms_media.bucket_name
    AWS_S3_ENDPOINT_URL     = module.cms_media.endpoint
    AWS_S3_REGION_NAME      = var.region
    DJANGO_SETTINGS_MODULE  = "sites_conformes.settings"
  }
}

# Shared by every serverless-container app (api, cms, ...) - Scaleway
# registry namespaces hold multiple image repos, no need for one per app.
resource "scaleway_registry_namespace" "pfat" {
  name      = "pfat"
  region    = var.region
  is_public = false
}

module "autodiag_site" {
  source      = "../../modules/static-site"
  app_name    = "autodiag"
  environment = local.environment
  bucket_name = "pfat-autodiag"
}

module "alert_widget_site" {
  source      = "../../modules/static-site"
  app_name    = "alert-widget"
  environment = local.environment
  bucket_name = "pfat-alert-widget"
}

module "climadiag_site" {
  source      = "../../modules/static-site"
  app_name    = "climadiag"
  environment = local.environment
  bucket_name = "pfat-climadiag"
}

module "api" {
  source                       = "../../modules/serverless-container"
  app_name                     = "api"
  environment                  = local.environment
  registry_image               = var.api_image
  deploy                       = var.api_deploy
  port                         = 8080
  min_scale                    = var.api_min_scale
  max_scale                    = 5
  environment_variables        = local.api_env
  secret_environment_variables = local.api_secret_env
}

module "cms_db" {
  source      = "../../modules/managed-postgres"
  app_name    = "cms"
  environment = local.environment
  node_type   = var.cms_db_node_type
}

module "cms_media" {
  source      = "../../modules/object-bucket"
  app_name    = "cms"
  environment = local.environment
  bucket_name = "pfat-cms-media"
}

module "cms" {
  source                       = "../../modules/serverless-container"
  app_name                     = "cms"
  environment                  = local.environment
  registry_image               = var.cms_image
  deploy                       = var.cms_deploy
  port                         = 8080
  min_scale                    = var.cms_min_scale
  max_scale                    = 3
  private_network_id           = module.cms_db.private_network_id
  environment_variables        = local.cms_env
  secret_environment_variables = local.cms_secret_env
}
