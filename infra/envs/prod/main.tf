locals {
  environment = "prod"
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
  source             = "../../modules/serverless-container"
  app_name           = "api"
  environment        = local.environment
  registry_namespace = "pfat-prod"
  registry_image     = var.api_image
  deploy             = var.api_deploy
  port               = 8080
  min_scale          = 0
  max_scale          = 5
  secret_environment_variables = {
    VIGILANCE_APP_ID = var.vigilance_app_id
  }
}
