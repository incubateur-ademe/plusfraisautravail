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

# The state holds every secret of the stack. OpenTofu encrypts it, and the
# plans saved with -out, before they leave the machine: the bucket only ever
# holds ciphertext. The passphrase is the Secret Manager secret
# pfat-prod-state-passphrase, read by infra/tofu.sh.
variable "state_passphrase" {
  type      = string
  sensitive = true
}

terraform {
  encryption {
    key_provider "pbkdf2" "passphrase" {
      passphrase = var.state_passphrase
    }

    method "aes_gcm" "passphrase" {
      keys = key_provider.pbkdf2.passphrase
    }

    state {
      method = method.aes_gcm.passphrase
      # A state in clear is refused, read or written.
      enforced = true
    }

    plan {
      method = method.aes_gcm.passphrase
    }
  }
}
