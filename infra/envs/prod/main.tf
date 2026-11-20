locals {
  environment = "prod"
  region      = "fr-par"
  base_domain = "plusfraisautravail.beta.gouv.fr"

  # Every hand-provided secret is one Secret Manager secret, named
  # pfat-prod-<name>. secrets.example.json lists them, `just secrets-push`
  # creates them from a filled copy (DEPLOY.md). All of them must exist: a
  # missing one fails the plan, naming it. Each use has its own, so that the
  # buckets and the e-mail can each get a restricted key.
  # A third-party credential we do not have is an empty secret: it is not
  # passed at all, and its feature is off. Not these: they must hold a key.
  secret_names = keys(jsondecode(file("${path.module}/secrets.example.json")))
  key_secret_names = [
    "cms-media-access-key-id", "cms-media-secret-key",
    "e2e-fixtures-access-key-id", "e2e-fixtures-secret-key",
  ]
  # trimspace: a value pasted from a file often ends with a newline.
  secret = { for name, version in data.scaleway_secret_version.app : name => trimspace(base64decode(version.data)) }

  # The alert API's own secrets (packages/pfat-api, served by the CMS): not
  # for cms_manage.
  api_secret_env = { for name, value in {
    VIGILANCE_APP_ID    = local.secret["vigilance-app-id"]
    RTE_CLIENT_ID       = local.secret["rte-client-id"]
    RTE_CLIENT_SECRET   = local.secret["rte-client-secret"]
    CLIMADIAG_API_TOKEN = local.secret["climadiag-api-token"]
  } : name => value if value != "" }

  cms_secret_env = merge(
    {
      # Private-network DSN: the container is attached to the DB's Private
      # Network (module.cms private_network_id).
      DATABASE_URL          = module.cms_db.private_database_url
      DJANGO_SECRET_KEY     = random_password.django_secret_key.result
      AWS_ACCESS_KEY_ID     = local.secret["cms-media-access-key-id"]
      AWS_SECRET_ACCESS_KEY = local.secret["cms-media-secret-key"]
    },
    { for name, value in {
      NOTION_TOKEN = local.secret["notion-token"]
      # Scaleway TEM takes an API secret key as SMTP password.
      EMAIL_HOST_PASSWORD = local.secret["email-host-password"]
    } : name => value if value != "" },
  )

  cms_env = {
    # Wide open: Scaleway's health probes do not send the container's domain
    # as Host, and Django would answer 400 to each of them. To narrow once
    # the probes' Host header is known.
    ALLOWED_HOSTS           = jsonencode(["*"])
    AWS_STORAGE_BUCKET_NAME = module.cms_media.bucket_name
    AWS_S3_ENDPOINT_URL     = module.cms_media.endpoint
    AWS_S3_REGION_NAME      = local.region
    DJANGO_SETTINGS_MODULE  = "cms.settings.production"
    # Public origin for absolute URLs. cms_base_url overrides it while the
    # site is tested on the Scalingo proxy hostname before the DNS cutover.
    WAGTAILADMIN_BASE_URL = coalesce(var.cms_base_url, "https://${local.base_domain}")
    # The Scalingo nginx proxy sets X-Forwarded-Host to the public hostname;
    # without this Django would build absolute URLs on the Scaleway hostname.
    USE_X_FORWARDED_HOST = "true"
    POSTHOG_KEY          = var.posthog_key
    SENTRY_DSN           = var.sentry_dsn
    # Outgoing mail (contact form), through Scaleway Transactional Email.
    DEFAULT_FROM_EMAIL = "ne-pas-repondre@${local.base_domain}" # a sender on the domain verified in TEM
    EMAIL_HOST         = "smtp.tem.scaleway.com"
    EMAIL_PORT         = "465" # implicit TLS
    EMAIL_HOST_USER    = data.scaleway_account_project.current.id
    # The alert and Climadiag API (packages/pfat-api), served under /api/.
    RTE_USE_SANDBOX = "false"
    # TEMPORARY: staging, the only X-AUTH-TOKEN we have is staging-only. Switch
    # to https://plusfraichemaville.fr/api/external-search-climadiag-info once
    # PFMV issues a production token.
    CLIMADIAG_API_URL = "https://staging.plusfraichemaville.fr/api/external-search-climadiag-info"
  }
}

data "scaleway_account_project" "current" {}

data "scaleway_secret_version" "app" {
  for_each    = toset(local.secret_names)
  secret_name = "pfat-${local.environment}-${each.key}"
  # Disabling a version rolls back to the one before.
  revision = "latest_enabled"

  lifecycle {
    postcondition {
      condition     = !contains(local.key_secret_names, each.key) || trimspace(base64decode(self.data)) != ""
      error_message = "The secret pfat-${local.environment}-${each.key} is empty: it must hold a Scaleway key."
    }
  }
}

resource "random_password" "django_secret_key" {
  length  = 64
  special = false
}

# Image of every container at creation: Scaleway checks that it exists, and on
# a first apply it is the only one pushed (DEPLOY.md). The deploys (cms.yml)
# then roll the real images out, tofu ignores the image from there on.
locals {
  bootstrap_image = "${scaleway_registry_namespace.pfat.endpoint}/cms:latest"
}

# Shared by every container image: one namespace holds several repositories.
resource "scaleway_registry_namespace" "pfat" {
  name      = "pfat"
  is_public = false
}

module "site" {
  for_each    = toset(["autodiag", "alert-widget", "climadiag"])
  source      = "../../modules/static-site"
  app_name    = each.key
  environment = local.environment
  bucket_name = "pfat-${each.key}"
}

moved {
  from = module.autodiag_site
  to   = module.site["autodiag"]
}

moved {
  from = module.alert_widget_site
  to   = module.site["alert-widget"]
}

moved {
  from = module.climadiag_site
  to   = module.site["climadiag"]
}

module "cms_db" {
  source      = "../../modules/managed-postgres"
  app_name    = "cms"
  environment = local.environment
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
  registry_image = local.bootstrap_image
  min_scale      = 1 # always warm: no cold start on the public site
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
  secret_environment_variables = merge(local.cms_secret_env, local.api_secret_env)
  custom_domain                = local.base_domain
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
  registry_image     = local.bootstrap_image
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
  # Rebuilt every night.
  force_destroy = true
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
  source             = "../../modules/serverless-container"
  app_name           = "e2e-dump"
  environment        = local.environment
  registry_image     = local.bootstrap_image
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
    AWS_DEFAULT_REGION = local.region
    AWS_ENDPOINT_URL   = module.e2e_fixtures.endpoint
  }
  secret_environment_variables = {
    SOURCE_DATABASE_URL   = local.e2e_dump_dsn
    AWS_ACCESS_KEY_ID     = local.secret["e2e-fixtures-access-key-id"]
    AWS_SECRET_ACCESS_KEY = local.secret["e2e-fixtures-secret-key"]
  }
}
