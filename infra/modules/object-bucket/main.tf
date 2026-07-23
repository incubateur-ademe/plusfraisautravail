terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.50"
    }
  }
}

data "scaleway_account_project" "default" {
  name = "default"
}

resource "scaleway_object_bucket" "this" {
  name   = var.bucket_name
  region = var.region
  tags = merge(
    {
      app         = var.app_name
      environment = var.environment
      managed_by  = "opentofu"
    },
    var.tags,
  )
}

resource "scaleway_object_bucket_acl" "this" {
  bucket = scaleway_object_bucket.this.id
  acl    = "private"
}

# App-scoped IAM identity for programmatic S3 access (media upload/read from
# Django), kept separate from any human/org-wide credentials.
resource "scaleway_iam_application" "this" {
  name = "${var.app_name}-${var.environment}-media"
}

# This grants project-wide Object Storage capability to the application -
# the object_bucket_policy below is what actually narrows access down to
# this one bucket.
resource "scaleway_iam_policy" "this" {
  name           = "${var.app_name}-${var.environment}-media"
  application_id = scaleway_iam_application.this.id
  rule {
    project_ids          = [data.scaleway_account_project.default.id]
    permission_set_names = ["ObjectStorageFullAccess"]
  }
}

resource "scaleway_iam_api_key" "this" {
  application_id = scaleway_iam_application.this.id
  description    = "S3 media access for ${var.app_name} (${var.environment})"
}

resource "scaleway_object_bucket_policy" "this" {
  bucket = scaleway_object_bucket.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AppAccess"
        Effect = "Allow"
        Principal = {
          SCW = "application_id:${scaleway_iam_application.this.id}"
        }
        Action = ["s3:*"]
        Resource = [
          scaleway_object_bucket.this.name,
          "${scaleway_object_bucket.this.name}/*",
        ]
      },
    ]
  })
}
