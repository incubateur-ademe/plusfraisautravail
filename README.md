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
just test-cms lint-cms  # tests et lint du CMS et de l'API
```

## Modèle de déploiement

- **autodiag** - bucket Scaleway, déployé par `deploy-autodiag.yml` lors d'un push sur `main`.
- **alert-widget** - bucket Scaleway, déployé par `deploy-alert-widget.yml` lors d'un push sur `main`.
- **cms** (et l'API qu'il sert) - image construite et poussée sur le Container Registry Scaleway, puis le Serverless Container est redéployé par `deploy-cms.yml`.
- **infra** - `tofu plan` s'exécute en CI sur les PR touchant `infra/**`. `tofu apply` est lancé via le workflow `terraform-apply.yml` lors d'un push sur `main`.

Voir [`DEPLOY.md`](./DEPLOY.md) pour la procédure de bootstrap initiale.

## Secrets / variables GitHub requis

**Secrets :**
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`
- `VIGILANCE_APP_ID`
- `RTE_CLIENT_ID`, `RTE_CLIENT_SECRET` (optionnels - sans ces secrets, l'endpoint `/api/alerts/electricity` répond 503)

**Variables :**
- `API_BASE_URL` - base de l'API utilisée au build des frontends : `/api` (même origine, le proxy l'envoie au CMS)
- `SCW_CMS_CONTAINER_ID` - ID du container Scaleway du CMS, sortie de `tofu apply`

## Sources de données

L'API Vigilance de Météo-France ([`meteole`](https://pypi.org/project/meteole/)) renvoie, par département, des codes couleur (1=vert, 2=jaune, 3=orange, 4=rouge) pour chaque phénomène. L'API (`packages/pfat-api`) expose pour l'instant les phénomènes canicule (id `6`) et orages (id `3`), ainsi que les prévisions de tension du réseau électrique national via l'API Ecowatt de RTE.

## Remerciements

Merci à [Vincent Poirot](https://github.com/vvpoirot) pour l'exploration initiale de l'API Vigilance avec l'INRS, qui a servi de point de départ à ce travail.
