locals {
  environment = "prod"

  # The alert API's secrets (packages/pfat-api, served by the CMS). Only pass
  # secrets that are actually set; an empty secret env var on a Scaleway
  # container is still a real env var pointing at nothing, which the API would
  # happily try to use. Use a conditional map and merge.
  api_secret_env = merge(
    var.vigilance_app_id == "" ? {} : { VIGILANCE_APP_ID = var.vigilance_app_id },
    var.rte_client_id == "" ? {} : { RTE_CLIENT_ID = var.rte_client_id },
    var.rte_client_secret == "" ? {} : { RTE_CLIENT_SECRET = var.rte_client_secret },
    var.climadiag_api_token == "" ? {} : { CLIMADIAG_API_TOKEN = var.climadiag_api_token },
  )

  cms_secret_env = merge(
    # Private-network DSN: the container is attached to the DB's Private
    # Network (module.cms private_network_id). The earlier "Waiting for
    # database..." hang was this attachment missing, not the network itself.
    { DATABASE_URL = module.cms_db.private_database_url },
    var.django_secret_key == "" ? {} : { DJANGO_SECRET_KEY = var.django_secret_key },
    var.notion_token == "" ? {} : { NOTION_TOKEN = var.notion_token },
    # Scaleway TEM takes an API secret key as SMTP password: the same
    # account-wide key as below unless a dedicated one is set (same caveat).
    var.email_host_password == "" && var.s3_bucket_scw_secret_key == "" ? {} : {
      EMAIL_HOST_PASSWORD = var.email_host_password != "" ? var.email_host_password : var.s3_bucket_scw_secret_key #gitleaks:allow
    },
    # reusing the same account-wide Scaleway key already used for
    # tofu apply, rather than a bucket-scoped IAM application/key - the
    # deploying key doesn't have IAM write permission yet. Narrow this once
    # it does (see infra/modules/object-bucket/main.tf).
    var.s3_bucket_scw_access_key_id == "" ? {} : { AWS_ACCESS_KEY_ID = var.s3_bucket_scw_access_key_id },
    var.s3_bucket_scw_secret_key == "" ? {} : { AWS_SECRET_ACCESS_KEY = var.s3_bucket_scw_secret_key }, #gitleaks:allow
  )

  cms_env = {
    # Can't include module.cms.public_endpoint here - it's only known after the
    # container is created, and the container's env vars are set at create
    # time, so referencing it back would be a dependency cycle. Add the
    # Scaleway-assigned domain to cms_extra_allowed_hosts once you have it
    # (from `tofu output cms_url`) and re-apply, same as the cms_image /
    # cms_deploy bootstrap two-step.
    ALLOWED_HOSTS           = jsonencode(var.cms_extra_allowed_hosts)
    AWS_STORAGE_BUCKET_NAME = module.cms_media.bucket_name
    AWS_S3_ENDPOINT_URL     = module.cms_media.endpoint
    AWS_S3_REGION_NAME      = var.region
    DJANGO_SETTINGS_MODULE  = "cms.settings.production"
    # Public origin for absolute URLs. cms_base_url overrides it while the
    # site is tested on the Scalingo proxy hostname before the DNS cutover.
    WAGTAILADMIN_BASE_URL = coalesce(var.cms_base_url, "https://${var.base_domain}")
    # The Scalingo nginx proxy sets X-Forwarded-Host to the public hostname;
    # without this Django would build absolute URLs on the Scaleway hostname.
    USE_X_FORWARDED_HOST = "true"
    POSTHOG_KEY          = var.posthog_key
    SENTRY_DSN           = var.sentry_dsn
    DEFAULT_FROM_EMAIL   = var.default_from_email
    EMAIL_HOST           = var.email_host
    EMAIL_PORT           = var.email_port
    EMAIL_HOST_USER      = var.email_host_user
    # The alert and Climadiag API (packages/pfat-api), served under /api/.
    RTE_USE_SANDBOX   = var.rte_use_sandbox ? "true" : "false"
    CLIMADIAG_API_URL = var.climadiag_api_url
  }
}

# Shared by every serverless-container app (cms, ...) - Scaleway
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
  # Media are served unsigned through the Scalingo nginx proxy (/media/ ->
  # this bucket) so they can be cached. The earlier 403s were the policy
  # locking out the project's own key - see the module for the fix.
  public_read = true
  # documents/* stays private: Wagtail serves documents through its own view
  # (WAGTAILDOCS_SERVE_METHOD = serve_view) so collection privacy applies.
  public_read_prefixes = ["images/*", "original_images/*"]
}

module "cms" {
  source         = "../../modules/serverless-container"
  app_name       = "cms"
  environment    = local.environment
  registry_image = var.cms_image
  deploy         = var.cms_deploy
  port           = 8080
  min_scale      = var.cms_min_scale
  max_scale      = 3
  # gunicorn serves 16 requests at once (apps/cms/entrypoint.sh): start another
  # instance before the queue builds up. Scaleway's default (50) never triggered.
  concurrent_requests_threshold = 12
  timeout_seconds               = 300
  # Wagtail + the sites_conformes migration set needs more headroom than the
  # module default (280 mvCPU / 512 MiB) to boot within the startup probe
  # budget. Doubling to 1120 mvCPU was measured and changed nothing: pages
  # are bound by ~40-60 sequential DB queries, not CPU - see CACHES.
  cpu_limit                    = 560
  memory_limit                 = 1024
  environment_variables        = local.cms_env
  secret_environment_variables = merge(local.cms_secret_env, local.api_secret_env) # API secrets: not for cms_manage
  custom_domain                = var.base_domain
  private_network_id           = module.cms_db.private_network_id
  # Probe a real Wagtail render, not just SELECT 1: a container that answers
  # /healthz/ but can't serve pages should still get restarted.
  health_check_path = "/"
  # First failure + 2 retries: restart after ~90s of a stuck container
  # instead of ~2.5 min.
  liveness_failure_threshold = 3
}

# Management commands (apps/cms/manage_jobs.sh: migrate, createcachetable),
# run by cms.yml at each deploy, before the CMS rollout, with POST /run. Same image and env as
# module.cms, started with manage_server.py instead of gunicorn. A private
# container rather than a Serverless Job: Jobs cannot join the database's
# Private Network, and the database has no public endpoint.
module "cms_manage" {
  source             = "../../modules/serverless-container"
  app_name           = "cms-manage"
  environment        = local.environment
  registry_image     = var.cms_image
  deploy             = var.cms_deploy
  command            = ["python", "manage_server.py"]
  privacy            = "private"
  private_network_id = module.cms_db.private_network_id
  health_check_path  = "/"
  min_scale          = 0
  max_scale          = 1
  cpu_limit          = 560
  memory_limit       = 1024
  # A deploy's migrations.
  timeout_seconds = 1800
  # No Sentry here: a failed migration can quote a row in its error.
  environment_variables        = merge(local.cms_env, { SENTRY_DSN = "" })
  secret_environment_variables = local.cms_secret_env # no API secrets: no API here
}

# ── SSH bastion, on demand ───────────────────────────────────────────────
# The database is reachable from its Private Network only. For an occasional
# admin session (just cms-shell-prod, pg_dump...), `just bastion-up` creates a
# Public Gateway with an SSH bastion on that network, `just bastion-down`
# removes it (about EUR 0.03/hour while it exists). Any apply from main also
# removes it, bastion_enabled being false there. SSH keys: those of the
# Scaleway project.
resource "scaleway_vpc_public_gateway_ip" "bastion" {
  count = var.bastion_enabled ? 1 : 0
}

resource "scaleway_vpc_public_gateway" "bastion" {
  count           = var.bastion_enabled ? 1 : 0
  name            = "bastion-${local.environment}"
  type            = "VPC-GW-S"
  ip_id           = scaleway_vpc_public_gateway_ip.bastion[0].id
  bastion_enabled = true
  bastion_port    = 61000
  # Scaleway's default is 0.0.0.0/0.
  allowed_ip_ranges = var.bastion_allowed_ip_ranges

  lifecycle {
    precondition {
      condition     = length(var.bastion_allowed_ip_ranges) > 0
      error_message = "Set bastion_allowed_ip_ranges (terraform.tfvars, or `just bastion-up <your IP>`)."
    }
  }
}

resource "scaleway_vpc_gateway_network" "bastion" {
  count              = var.bastion_enabled ? 1 : 0
  gateway_id         = scaleway_vpc_public_gateway.bastion[0].id
  private_network_id = module.cms_db.private_network_id
  # SSH access only: no NAT, and no default route pushed to the containers.
  enable_masquerade = false
  ipam_config {
    push_default_route = false
  }
}

# ── e2e fixtures ─────────────────────────────────────────────────────────
# Nightly anonymised dump of the CMS database, used by the e2e tests (CI and
# local). Single fixed key: s3://pfat-e2e-fixtures/cms/latest.dump.
# Private: no public_read. Only an *anonymised* dump ever lands here - the
# raw dump stays inside the Scaleway job that anonymises it.
module "e2e_fixtures" {
  source      = "../../modules/object-bucket"
  app_name    = "e2e"
  environment = local.environment
  bucket_name = "pfat-e2e-fixtures"
}

# Read-only user the dump job connects with: it can read the CMS database,
# never write to it.
resource "random_password" "e2e_dump" {
  length = 32
  # Same DSN-safe set as module.cms_db's password (see modules/managed-postgres).
  special          = true
  override_special = "!$%&*()-_=+{}<>"
}

resource "scaleway_rdb_user" "e2e_dump" {
  instance_id = module.cms_db.instance_id
  name        = "e2e_dump"
  password    = random_password.e2e_dump.result
  is_admin    = false
}

# Over the Private Network: the dump container is attached to it, like the CMS.
locals {
  e2e_dump_dsn = "postgresql://${scaleway_rdb_user.e2e_dump.name}:${urlencode(random_password.e2e_dump.result)}@${module.cms_db.host}:${module.cms_db.port}/${module.cms_db.database_name}?sslmode=require"
}

resource "scaleway_rdb_privilege" "e2e_dump" {
  instance_id   = module.cms_db.instance_id
  user_name     = scaleway_rdb_user.e2e_dump.name
  database_name = module.cms_db.database_name
  permission    = "readonly"
}

# Nightly anonymised dump (infra/e2e-dump), run when .github/workflows/e2e-dump.yml
# POSTs /run. A private container, not a Serverless Job: Jobs cannot join a
# Private Network, so they would need the database's public endpoint.
# - privacy private: every request needs a Scaleway IAM key (X-Auth-Token);
# - attached to the database's Private Network, read-only user e2e_dump;
# - min_scale 0: billed only while a dump runs (a few minutes a night).
# The image is built by the CMS deploy (cms.yml), so the masking rules match
# the schema actually deployed, and that deploy rolls it out on this container.
module "e2e_dump" {
  source      = "../../modules/serverless-container"
  app_name    = "e2e-dump"
  environment = local.environment
  # Placeholder: Scaleway checks that the image exists when the container is
  # created, and the e2e-dump image may not be pushed yet (the CMS deploy of
  # the same push builds it). That deploy rolls the real image out (cms.yml),
  # tofu then ignores the image. Scaled to zero and private: the placeholder
  # never starts unless called.
  registry_image     = "rg.fr-par.scw.cloud/pfat/cms:latest"
  privacy            = "private"
  private_network_id = module.cms_db.private_network_id
  health_check_path  = "/"
  min_scale          = 0
  max_scale          = 1
  # Local Postgres + the copy of the database and its dump.
  cpu_limit                 = 1000
  memory_limit              = 2048
  local_storage_limit_bytes = 4000000000
  # A dump takes a few minutes.
  timeout_seconds = 1800
  environment_variables = {
    E2E_DUMP_PREFIX    = "s3://${module.e2e_fixtures.bucket_name}/cms"
    AWS_DEFAULT_REGION = "fr-par"
    AWS_ENDPOINT_URL   = module.e2e_fixtures.endpoint
  }
  secret_environment_variables = {
    SOURCE_DATABASE_URL   = local.e2e_dump_dsn
    AWS_ACCESS_KEY_ID     = var.s3_bucket_scw_access_key_id
    AWS_SECRET_ACCESS_KEY = var.s3_bucket_scw_secret_key #gitleaks:allow
  }
}
