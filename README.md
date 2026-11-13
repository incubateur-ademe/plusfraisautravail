# plusfraisautravail

Monorepo de l'écosystème [plusfraisautravail.beta.gouv.fr](https://plusfraisautravail.beta.gouv.fr) - un outil d'auto-évaluation permettant aux employeurs d'évaluer l'adaptation de leur site de travail aux vagues de chaleur.

## Organisation du dépôt

```
.
├── apps/
│   ├── cms/              # CMS Wagtail (Sites Conformes), sert aussi l'API sous /api/
│   ├── autodiag/         # SPA d'auto-évaluation (Vite + React + react-dsfr)
│   └── alert-widget/     # Widget d'alerte canicule embarquable
├── packages/
│   ├── pfat-api/         # API d'alertes et Climadiag (Django Ninja), montée par le CMS
│   └── api-client/       # Client TypeScript partagé pour l'API
├── infra/                # OpenTofu (Scaleway : buckets + serverless containers)
├── scripts/              # Scripts ponctuels
├── sources/              # Matériel source brut, notebooks d'exploration
└── .github/workflows/    # CI + workflows de déploiement par app
```

## Stack technique

- **Frontends :** npm workspaces, Vite, React 19, TypeScript, [`@codegouvfr/react-dsfr`](https://github.com/codegouvfr/react-dsfr).
- **CMS et API :** Python 3.12, [`uv`](https://docs.astral.sh/uv/), Django, Wagtail ([Sites Conformes](https://github.com/numerique-gouv/sites-conformes)), Django Ninja, [`meteole`](https://pypi.org/project/meteole/).
- **Infra :** OpenTofu -> Scaleway (buckets Object Storage, Serverless Containers, Container Registry). État stocké sur Scaleway Object Storage (backend compatible S3).
- **CI/CD :** GitHub Actions, filtrées par chemin pour chaque app.

## Développement

### Prérequis
- Node 22+
- Python 3.12+ et [`uv`](https://docs.astral.sh/uv/)

### Frontends
```bash
npm install
npm run dev:autodiag        # http://localhost:5173/autodiag/
npm run dev:alert-widget    # http://localhost:5173/alert-widget/  (proxifie /api -> :8080)
```

### CMS et API
```bash
cp apps/cms/.env.example apps/cms/.env  # renseigner VIGILANCE_APP_ID, RTE_*, CLIMADIAG_API_TOKEN pour l'API
just install-cms
just cms
```
L'API est servie par le CMS sous `/api/` ; OpenAPI : http://localhost:8080/api/docs

### Tests / lint
```bash
npm run build           # build tous les workspaces
just test-cms lint-cms  # tests du CMS, lint Python (CMS et packages)
just lint-js            # lint JS/TS de tous les workspaces
just install-hooks      # hooks pre-commit (ruff, gitleaks…)
```

Les conventions de code sont celles des outils standards, configurés à la racine et vérifiés par la CI :
- **Python** : [ruff](https://docs.astral.sh/ruff/) (lint + format), config dans [`ruff.toml`](ruff.toml) ;
- **TypeScript / React** : [ESLint](https://eslint.org/) avec les règles recommandées de typescript-eslint et React Hooks, config dans [`eslint.config.js`](eslint.config.js).

### Base iso-prod pour les tests e2e
Chaque nuit, un conteneur Scaleway privé, relié à la base par le réseau privé, publie un dump **anonymisé** de la base de prod (voir [`infra/e2e-dump`](infra/e2e-dump)). Pour travailler dessus en local :
```bash
createdb pfat_e2e       # une fois ; ou E2E_DATABASE_URL=… dans .env
just e2e-restore        # télécharge le dump, restaure, migre, crée l'admin e2e / e2e
just e2e-serve          # CMS sur http://localhost:8765, comme en prod (DEBUG off)
npm run test:e2e        # tests Playwright (e2e/), démarre le CMS s'il ne tourne pas
```
Le téléchargement utilise les clés `SCW_ACCESS_KEY` / `SCW_SECRET_KEY` du `.env`. `E2E_DUMP_FILE=chemin` restaure un dump local à la place.

Les tests tournent hors ligne : les médias sont remplacés par une image vide et tout autre domaine est bloqué. En CI, ils se lancent sur les PR qui portent le label `frontend`, et sur `main`.

### Storybook des SPA
Chaque SPA (`apps/autodiag`, `apps/alert-widget`, `apps/climadiag`) a son Storybook (`npm run storybook --workspace @pfat/<spa>`), avec des données fictives injectées dans les composants. Chaque story est vérifiée par Playwright :
```bash
just e2e-spa            # rendu et accessibilité (axe) de chaque story, parcours de l'autodiag
just e2e-spa-update-snapshots  # régénère les captures de référence (Docker, même image que la CI)
```
`E2E_COVERAGE=1` mesure ce que les tests e2e exercent, à part de la couverture des tests unitaires : côté serveur pour `npm run test:e2e` (rapport : `cd apps/cms && uv run coverage report --data-file=../../e2e/.cache/coverage/server.coverage --fail-under=0`), côté navigateur pour `just e2e-spa` (résumé affiché à la fin). En CI, les deux s'affichent dans le résumé des jobs.

Les captures (320, 768 et 1440 px) ne sont comparées que sous Linux, en CI ou via `just e2e-spa-update-snapshots` : les polices macOS donnent un autre rendu. Relire le diff des PNG avant de committer.

## CI/CD

Deux workflows d'entrée, un groupe par produit dans la barre latérale de chaque run :

- **💣 Pull request** (`review.yml`) : lint, tests et build des produits touchés par la PR. Le check à exiger est **✅ CI**.
- **🚀 Production** (`cd.yml`) : sur `main`, mêmes vérifications puis déploiement des produits touchés. Se lance aussi à la main pour un produit (`just deploy cms`) ou pour tous.

Le découpage par produit est dans [`.github/ci-areas.yml`](.github/ci-areas.yml) :

- **📰 CMS** (et l'API qu'il sert) - `cms.yml` : ruff, pytest avec couverture, puis image Docker poussée sur le registre Scaleway et Serverless Container redéployé.
- **🩺 Autodiag**, **🚨 Alert widget**, **🌡️ Climadiag** - `frontend.yml` : ESLint et build, puis synchronisation vers leur bucket Scaleway.
- **🏗️ Infrastructure** - `infrastructure.yml` : `tofu plan`, puis `tofu apply` sur `main`.

À côté de ce découpage, **🎭 E2E** (`e2e.yml`) lance les tests Playwright sur la base iso-prod, sur les PR qui portent le label `frontend` et sur `main`. **🌙 E2E dump** (`e2e-dump.yml`) produit chaque nuit le dump anonymisé de la prod.

Le taux de couverture Python s'affiche en haut de chaque run (annotation **📊 Python coverage**) et dans le résumé du job ✅ CI.

Voir [`DEPLOY.md`](./DEPLOY.md) pour la procédure de bootstrap initiale.

## Secrets / variables GitHub requis

**Secrets :**
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`
- `VIGILANCE_APP_ID`
- `RTE_CLIENT_ID`, `RTE_CLIENT_SECRET` (optionnels - sans ces secrets, l'endpoint `/api/alerts/electricity` répond 503)

**Variables :**
- `API_BASE_URL` - base de l'API utilisée au build des frontends : `/api` (même origine, le proxy l'envoie au CMS)

## Sources de données

L'API Vigilance de Météo-France ([`meteole`](https://pypi.org/project/meteole/)) renvoie, par département, des codes couleur (1=vert, 2=jaune, 3=orange, 4=rouge) pour chaque phénomène. L'API (`packages/pfat-api`) expose pour l'instant les phénomènes canicule (id `6`) et orages (id `3`), ainsi que les prévisions de tension du réseau électrique national via l'API Ecowatt de RTE.

## Remerciements

Merci à [Vincent Poirot](https://github.com/vvpoirot) pour l'exploration initiale de l'API Vigilance avec l'INRS, qui a servi de point de départ à ce travail.

## Licence

Copyright (c) 2026 ADEME

Ce code est publié sous la licence [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0), la même que [sites-conformes](https://github.com/numerique-gouv/sites-conformes), sur lequel repose le CMS. Elle figure dans la [liste des licences autorisées](https://www.data.gouv.fr/fr/pages/legal/licences/) pour les logiciels publiés par l'administration.
