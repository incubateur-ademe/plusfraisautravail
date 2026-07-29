# sites-conformes-footer-partners

Logos partenaires ("ils nous soutiennent") affichés sur tout le site pour
[sites-conformes](https://github.com/betagouv/sites-conformes), rendus dans
le bloc natif `fr-footer__partners` du pied de page DSFR sur toutes les
pages, plutôt que limités à un bloc StreamField sur une seule page.

Le balisage suit la [spécification du pied de page DSFR](https://www.systeme-de-design.gouv.fr/version-courante/fr/composants/pied-de-page) :
un logo de partenaire principal, suivi d'une liste illimitée de logos de
partenaires secondaires, tous partageant une hauteur uniforme configurable.

## Installation

```bash
uv add --editable ../../packages/sites-conformes-footer-partners
```

Ce package surcharge `sites_conformes_core/blocks/footer.html`, template que
le package `sites_conformes` fournit lui-même (dans `sites_conformes/templates/`,
pas `sites_conformes/core/templates/`). Le chargeur de templates `APP_DIRS`
de Django essaie le dossier `templates/` de chaque application installée
dans l'ordre de `INSTALLED_APPS` et retient la première correspondance :
il faut donc placer cette application **avant** `sites_conformes` :

```python
INSTALLED_APPS = [
    ...,
    "sites_conformes_footer_partners",
    "sites_conformes",
    "sites_conformes.core",
    ...,
]
```

Ensuite, dans l'admin Wagtail, sous **Réglages → Footer partners**,
renseignez le titre, le logo du partenaire principal, les autres logos
partenaires, et la hauteur commune des logos (5,625rem par défaut, comme
recommandé par le DSFR).
