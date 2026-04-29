# Infrastructure (Terraform / Scaleway)

Manages all Scaleway resources for the monorepo.

## Layout

```
infra/
├── modules/
│   ├── static-site/           # Object bucket + website config + public-read policy
│   └── serverless-container/  # Container Registry namespace + Container namespace + Container
└── envs/
    └── prod/                  # one stack per environment
```

## Bootstrap (one-time)

1. Set Scaleway credentials in your shell:
   ```fish
   set -x SCW_ACCESS_KEY ...
   set -x SCW_SECRET_KEY ...
   set -x SCW_DEFAULT_PROJECT_ID ...
   set -x SCW_DEFAULT_ORGANIZATION_ID ...
   ```
2. Create the state bucket manually (Terraform can't manage its own state bucket):
   ```bash
   aws --endpoint-url=https://s3.fr-par.scw.cloud s3 mb s3://pfat-tfstate \
     --region fr-par
   ```
   (Use `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` as `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`.)
3. Copy and fill the tfvars:
   ```bash
   cd envs/prod
   cp terraform.tfvars.example terraform.tfvars
   ```

## First apply (chicken-and-egg)

The Serverless Container needs an image reference, but the Container Registry must exist first. Two-step apply:

```bash
cd envs/prod
terraform init
terraform apply -var 'api_deploy=false'   # creates buckets + registry, but no container deploy
# now build & push the API image (see api/README.md, .github/workflows/deploy-api.yml)
terraform apply                           # set api_image + api_deploy=true in tfvars
```

## Plan in CI

`terraform-plan.yml` runs `terraform plan` on every PR touching `infra/**`. Apply is manual (locally) for now.

## Resources created (prod)

| Resource | Name |
|---|---|
| Bucket | `pfat-autodiag-prod` |
| Bucket | `pfat-alert-widget-prod` |
| Container Registry namespace | `pfat-prod` |
| Container namespace | `api-prod` |
| Container | `api-prod` |
