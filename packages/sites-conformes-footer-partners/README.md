# sites-conformes-footer-partners

Sitewide "ils nous soutiennent" partner logos for [sites-conformes](https://github.com/betagouv/sites-conformes),
rendered in the DSFR footer's native `fr-footer__partners` block on every
page, instead of being limited to a StreamField block on a single page.

Markup follows the [DSFR footer spec](https://www.systeme-de-design.gouv.fr/version-courante/fr/composants/pied-de-page):
a main partner logo plus an unlimited list of secondary partner logos, all
sharing a configurable uniform height.

## Install

```bash
uv add --editable ../../packages/sites-conformes-footer-partners
```

This package overrides `sites_conformes_core/blocks/footer.html`, which the
`sites_conformes` package itself ships (under `sites_conformes/templates/`,
not `sites_conformes/core/templates/`). Django's `APP_DIRS` template loader
tries each installed app's `templates/` dir in `INSTALLED_APPS` order and
uses the first match, so add this app **before** `sites_conformes`:

```python
INSTALLED_APPS = [
    ...,
    "sites_conformes_footer_partners",
    "sites_conformes",
    "sites_conformes.core",
    ...,
]
```

Then in the Wagtail admin, under **Settings → Footer partners**, set the
title, main partner logo, other partner logos, and the shared logo height
(defaults to 5.625rem, per the DSFR docs).
