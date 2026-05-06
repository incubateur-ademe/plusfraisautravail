# plusfraisautravail

Monorepo de l'écosystème [plusfraisautravail.beta.gouv.fr](https://plusfraisautravail.beta.gouv.fr) - un outil d'auto-évaluation permettant aux employeurs d'évaluer l'adaptation de leur site de travail aux vagues de chaleur.

## Organisation du dépôt

```
.
├── apps/
│   ├── autodiag/         # SPA d'auto-évaluation (Vite + React + react-dsfr)
│   └── alert-widget/     # Widget d'alerte canicule embarquable
├── api/                  # Passerelle FastAPI agrégeant les sources d'alerte (meteole/Vigilance)
├── packages/
│   └── api-client/       # Client TypeScript partagé pour l'API
├── infra/                # OpenTofu (Scaleway : buckets + serverless containers)
├── scripts/              # Scripts ponctuels
├── sources/              # Matériel source brut, notebooks d'exploration
└── .github/workflows/    # CI + workflows de déploiement par app
```

## Stack technique

- **Frontends :** npm workspaces, Vite, React 19, TypeScript, [`@codegouvfr/react-dsfr`](https://github.com/codegouvfr/react-dsfr).
- **API :** Python 3.12, [`uv`](https://docs.astral.sh/uv/), FastAPI, [`meteole`](https://pypi.org/project/meteole/).
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

### API
```bash
cd api
cp .env.example .env  # renseigner VIGILANCE_APP_ID
uv sync --extra dev
uv run uvicorn pfat_api.main:app --reload --port 8080
```
OpenAPI : http://localhost:8080/docs

### Tests / lint
```bash
npm run build           # build tous les workspaces
cd api && uv run pytest && uv run ruff check .
```

## Modèle de déploiement

- **autodiag** - bucket Scaleway, déployé par `deploy-autodiag.yml` lors d'un push sur `main`.
- **alert-widget** - bucket Scaleway, déployé par `deploy-alert-widget.yml` lors d'un push sur `main`.
- **api** - image construite et poussée sur le Container Registry Scaleway, puis le Serverless Container est redéployé par `deploy-api.yml`.
- **infra** - `tofu plan` s'exécute en CI sur les PR touchant `infra/**`. `tofu apply` est lancé via le workflow `terraform-apply.yml` lors d'un push sur `main`.

Voir [`DEPLOY.md`](./DEPLOY.md) pour la procédure de bootstrap initiale.

## Secrets / variables GitHub requis

**Secrets :**
- `SCW_ACCESS_KEY`, `SCW_SECRET_KEY`, `SCW_DEFAULT_PROJECT_ID`, `SCW_DEFAULT_ORGANIZATION_ID`
- `VIGILANCE_APP_ID`
- `RTE_CLIENT_ID`, `RTE_CLIENT_SECRET` (optionnels - sans ces secrets, l'endpoint `/alerts/electricity` répond 503)

**Variables :**
- `API_BASE_URL` - URL publique de l'API déployée (utilisée au build des frontends)
- `SCW_API_CONTAINER_ID` - ID du container Scaleway, sortie de `tofu apply`

## Sources de données

L'API Vigilance de Météo-France ([`meteole`](https://pypi.org/project/meteole/)) renvoie, par département, des codes couleur (1=vert, 2=jaune, 3=orange, 4=rouge) pour chaque phénomène. La passerelle API expose pour l'instant les phénomènes canicule (id `6`) et orages (id `3`), ainsi que les prévisions de tension du réseau électrique national via l'API Ecowatt de RTE.

## Remerciements

Merci à [Vincent Poirot](https://github.com/vvpoirot) pour l'exploration initiale de l'API Vigilance avec l'INRS, qui a servi de point de départ à ce travail.
