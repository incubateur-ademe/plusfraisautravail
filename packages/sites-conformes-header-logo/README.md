# sites-conformes-header-logo

Remplace le texte du titre de service (`fr-header__service-title`) du
header [sites-conformes](https://github.com/betagouv/sites-conformes) par
un logo image, quand un logo est configuré.

**Non conforme DSFR** : le [référentiel DSFR](https://www.systeme-de-design.gouv.fr/version-courante/fr/composants/en-tete)
prévoit un titre de service textuel, pas une image libre. C'est un choix
assumé pour ce site (cf. le ticket associé) - si aucun logo n'est
configuré, le rendu retombe sur le texte standard, donc l'installation de
ce package est sans risque pour les sites qui n'en ont pas besoin.

## Installation

```bash
uv add --editable ../../packages/sites-conformes-header-logo
```

Ce package surcharge `sites_conformes_core/blocks/header.html`, que le
package `sites_conformes` fournit lui-même (dans `sites_conformes/templates/`,
pas `sites_conformes/core/templates/`). Comme pour `sites-conformes-footer-partners`,
il doit être placé **avant** `sites_conformes` dans `INSTALLED_APPS` :

```python
INSTALLED_APPS = [
    ...,
    "sites_conformes_header_logo",
    "sites_conformes",
    "sites_conformes.core",
    ...,
]
```

Ensuite, dans l'admin Wagtail, sous **Réglages → Logo du header**,
renseignez le logo et son texte alternatif (obligatoire, doit reprendre le
nom du service). Sans logo configuré, le header affiche le titre textuel
habituel.
