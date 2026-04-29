terraform {
  required_providers {
    scaleway = {
      source  = "scaleway/scaleway"
      version = "~> 2.50"
    }
  }
}

resource "scaleway_object_bucket" "this" {
  name   = var.bucket_name
  region = var.region
  tags = merge(
    {
      app         = var.app_name
      environment = var.environment
      managed_by  = "terraform"
    },
    var.tags,
  )
}

resource "scaleway_object_bucket_acl" "this" {
  bucket = scaleway_object_bucket.this.id
  acl    = "public-read"
}

resource "scaleway_object_bucket_website_configuration" "this" {
  bucket = scaleway_object_bucket.this.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "index.html"
  }
}

resource "scaleway_object_bucket_policy" "public_read" {
  bucket = scaleway_object_bucket.this.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicRead"
        Effect    = "Allow"
        Principal = "*"
        Action    = ["s3:GetObject"]
        Resource  = ["${scaleway_object_bucket.this.name}/*"]
      },
    ]
  })
}
