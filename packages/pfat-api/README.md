# pfat-api

Alert sources for plusfraisautravail.beta.gouv.fr, served by the CMS under `/api/`:

- `GET /api/alerts/meteo`: Météo-France Vigilance, metropolitan departments at jaune or above.
- `GET /api/alerts/electricity`: RTE Ecowatt, grid tension today and the next 3 days.
- `GET /api/sources`: freshness of the Vigilance data.
- `GET /api/climadiag/search?search=…`: PlusFraîcheMaVille Climadiag search, token kept server-side.

The OpenAPI documentation is at `/api/docs`.

Mount it in the project's URLs, after Wagtail's `api/v2/`:

```python
from pfat_api.api import api

urlpatterns = [..., path("api/", api.urls)]
```

Configure it with a `PFAT_API` dict in the Django settings (every key is optional):

| Key | Default |
|---|---|
| `vigilance_app_id` | `None`: `/alerts/meteo` answers 503 |
| `rte_client_id`, `rte_client_secret` | `None`: `/alerts/electricity` answers 503 |
| `rte_use_sandbox` | `False` |
| `climadiag_api_url` | the PlusFraîcheMaVille staging URL |
| `climadiag_api_token` | `None`: `/climadiag/search` answers 503 |
| `cache_ttl_seconds` | `3600`, for the Vigilance data (RTE is cached 15 min) |
| `cache_alias` | `"default"`: use a cache shared by every worker (database, Redis) so the RTE rate limit holds |
