# sites-conformes-posthog

Charge et configure PostHog sur toutes les pages, et identifie les
utilisateurs connectés au CMS afin de pouvoir exclure l'équipe des insights
(comme sur [quefairedemesobjets](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/webapp/static/to_compile/controllers/shared/analytics.ts)).

La configuration vit dans le code, pas dans **Réglages → Scripts** : elle
passe par le proxy nginx du site (`api_host: "/ph"`, voir
`infra/scalingo-proxy/servers.conf.erb`) et ne doit pas dériver au gré des
synchronisations de contenu. Ne collez donc **pas** de `posthog.init(...)`
dans les scripts personnalisés - il ferait doublon.

## Réglages

- `POSTHOG_KEY` (settings Django, depuis la variable d'environnement du même
  nom) : la clé de projet. Vide = pas de PostHog (dev, tests). En prod elle
  arrive par OpenTofu (`var.posthog_key`, variable GitHub `POSTHOG_KEY`).

## Installation

```bash
uv add --editable ../../packages/sites-conformes-posthog
```

Ce package surcharge `sites_conformes_core/base.html` (fourni par
`sites_conformes`). Il doit être placé **avant** `sites_conformes` dans
`INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    ...,
    "sites_conformes_posthog",
    "sites_conformes",
    "sites_conformes.core",
    ...,
]
```

Deux blocs sont étendus avec `{{ block.super }}` : `tracking` (dans le
`<head>`, loader + `posthog.init`) et `body_tracking_scripts`
(`posthog.identify` si `request.user.is_authenticated`).

## Configuration côté PostHog

Dans **PostHog → Project Settings → Filter out internal and test users**,
ajouter un filtre pour exclure l'équipe, par exemple :

```
email contains "@beta.gouv.fr"
```

ou tout autre critère basé sur `email`/`admin`, les deux propriétés
envoyées par `posthog.identify()`.
