locals {
  environment = "prod"

  # Only pass secrets that are actually set; an empty secret env var on a
  # Scaleway container is still a real env var pointing at nothing, which the
  # API would happily try to use. Use a conditional map and merge.
  api_secret_env = merge(
    var.vigilance_app_id == "" ? {} : { VIGILANCE_APP_ID = var.vigilance_app_id },
    var.rte_client_id == "" ? {} : { RTE_CLIENT_ID = var.rte_client_id },
    var.rte_client_secret == "" ? {} : { RTE_CLIENT_SECRET = var.rte_client_secret },
  )

  api_env = {
    RTE_USE_SANDBOX = var.rte_use_sandbox ? "true" : "false"
    # JSON-encoded list - pydantic-settings parses this as list[str].
    # Includes the deployed alert-widget bucket origin so the embed can call
    # the API without a CORS preflight failure.
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
      ],
      var.extra_cors_origins,
    ))
  }
}

module "autodiag_site" {
  source      = "../../modules/static-site"
  app_name    = "autodiag"
  environment = local.environment
  bucket_name = "pfat-autodiag-prod"
}

module "alert_widget_site" {
  source      = "../../modules/static-site"
  app_name    = "alert-widget"
  environment = local.environment
  bucket_name = "pfat-alert-widget-prod"
}

module "api" {
  source                       = "../../modules/serverless-container"
  app_name                     = "api"
  environment                  = local.environment
  registry_namespace           = "pfat-prod"
  registry_image               = var.api_image
  deploy                       = var.api_deploy
  port                         = 8080
  min_scale                    = 0
  max_scale                    = 5
  environment_variables        = local.api_env
  secret_environment_variables = local.api_secret_env
}
