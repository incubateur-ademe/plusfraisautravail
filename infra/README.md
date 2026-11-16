# Infrastructure (OpenTofu / Scaleway)

Every Scaleway resource of the monorepo, in one stack: `envs/prod`. `envs/preview` adds, per pull request labelled `preview`, a database, a user and a container.

See **[`../DEPLOY.md`](../DEPLOY.md)** to bootstrap it on a new project and for the day-to-day flow.

```
infra/
├── modules/
│   ├── static-site/           # website bucket of a SPA
│   ├── object-bucket/         # private bucket, optional public read on prefixes
│   ├── managed-postgres/      # RDB instance on its Private Network
│   └── serverless-container/  # container namespace + container (+ custom domain)
├── envs/prod/                 # the stack
├── envs/preview/              # preview of a pull request, one workspace each (DEPLOY.md 4)
├── e2e-dump/                  # image of the nightly anonymised dump
└── scalingo-proxy/            # nginx in front of the public hostname
```

Secrets: Scaleway Secret Manager secrets named `pfat-prod-…`, one per value, read by the stack. GitHub only holds the Scaleway key.
