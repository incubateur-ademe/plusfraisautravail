# sites-conformes-posthog

Identifie les utilisateurs connectés au CMS auprès de PostHog, afin de
pouvoir exclure les statistiques de l'équipe des insights (comme fait sur
[quefairedemesobjets](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/webapp/static/to_compile/controllers/shared/analytics.ts)).

Ne fait qu'identifier - la clé/config PostHog elle-même reste dans
**Réglages → Analytics** (`CustomScriptsSettings.head_scripts`), là où
`posthog.init(...)` est déjà collé. Ce package ajoute uniquement un
`posthog.identify(...)` quand `request.user.is_authenticated`, en plus du
script existant.

## Installation

```bash
uv add --editable ../../packages/sites-conformes-posthog
```

Ce package surcharge `sites_conformes_core/base.html`, que le package
`sites_conformes` fournit lui-même (dans `sites_conformes/templates/`).
Comme pour les autres packages `sites-conformes-*` de ce dépôt, il doit
être placé **avant** `sites_conformes` dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    ...,
    "sites_conformes_posthog",
    "sites_conformes",
    "sites_conformes.core",
    ...,
]
```

`base.html` a déjà un bloc `{% block body_tracking_scripts %}` dédié, donc
ce package n'a pas besoin de copier tout le fichier - juste ce bloc, avec
`{{ block.super }}` pour garder le script PostHog existant.

## Configuration côté PostHog

Le code ne fait qu'identifier - c'est dans **PostHog → Project Settings →
Filter out internal and test users** qu'il faut ajouter un filtre pour
exclure ces utilisateurs des insights, par exemple :

```
email contains "@beta.gouv.fr"
```

ou tout autre critère basé sur `email`/`admin`, les deux propriétés
envoyées par `posthog.identify()`.
