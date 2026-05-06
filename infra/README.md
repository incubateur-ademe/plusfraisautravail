# Infrastructure (OpenTofu / Scaleway)

Provisions every Scaleway resource for the monorepo: two website buckets (autodiag + alert-widget), one container registry namespace, one serverless container (API).

See **[`../DEPLOY.md`](../DEPLOY.md)** for the full bootstrap walkthrough and the day-to-day flow.

```
infra/
├── modules/
│   ├── static-site/           # bucket + website config + public-read policy
│   └── serverless-container/  # registry + container namespace + container
└── envs/
    └── prod/                  # one stack per environment
```
