# Scaleway Object Storage S3-compatible backend.
# Bootstrap: create the state bucket manually before the first `tofu init`.
#   just bootstrap-state
# (SCW_ACCESS_KEY / SCW_SECRET_KEY as AWS creds)
terraform {
  backend "s3" {
    bucket = "pfat-terraform"
    key    = "envs/prod/terraform.tfstate"
    region = "fr-par"
    # Lock object next to the state (S3 conditional write).
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
