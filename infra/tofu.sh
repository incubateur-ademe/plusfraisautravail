#!/usr/bin/env bash
# tofu on infra/envs/prod, with the passphrase that encrypts its state: the
# secret pfat-prod-state-passphrase of Scaleway Secret Manager (DEPLOY.md 2.2).
# Used by the Justfile and by infrastructure.yml. Needs SCW_SECRET_KEY,
# SCW_DEFAULT_PROJECT_ID, curl and jq.
# Usage: infra/tofu.sh plan
set -euo pipefail

cd "$(dirname "$0")/envs/prod"

TF_VAR_state_passphrase=$(
    curl -fsS -H "X-Auth-Token: $SCW_SECRET_KEY" \
        "https://api.scaleway.com/secret-manager/v1beta1/regions/fr-par/secrets-by-path/versions/latest_enabled/access?project_id=$SCW_DEFAULT_PROJECT_ID&secret_path=/&secret_name=pfat-prod-state-passphrase" |
        jq -er '.data | @base64d'
) || {
    echo "Cannot read the secret pfat-prod-state-passphrase: \`just state-passphrase\` creates it, and the Scaleway key needs SecretManagerSecretAccess." >&2
    exit 1
}
export TF_VAR_state_passphrase

exec tofu "$@"
