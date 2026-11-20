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
}

provider "scaleway" {
  region = local.region
  zone   = "${local.region}-1"
  # Auth via env vars: SCW_ACCESS_KEY, SCW_SECRET_KEY, SCW_DEFAULT_PROJECT_ID, SCW_DEFAULT_ORGANIZATION_ID
}
