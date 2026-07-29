# sites-conformes-rgaa

Rend les emojis décoratifs accessibles dans les textes riches
[sites-conformes](https://github.com/betagouv/sites-conformes), en les
enveloppant dans le balisage recommandé par le DSFR :

```html
<span role="img" aria-hidden="true">🔥</span>
```

`aria-hidden="true"` masque l'emoji aux lecteurs d'écran - il reste
purement décoratif, le texte environnant porte déjà le sens.

## Ce que fait ce package

1. **`sites_conformes_rgaa.emoji_wrapping`** : le module central, testé
   indépendamment. `wrap_emojis_in_html(html)` transforme une chaîne
   HTML, `wrap_emojis_in_streamfield_raw_data(raw_data)` parcourt
   récursivement la structure JSON brute d'un StreamField.
2. **Commande `wrap_emojis`** : parcourt toutes les pages (tous les
   `RichTextField` et `StreamField` détectés automatiquement via
   l'introspection des modèles Wagtail) et enveloppe les emojis trouvés.
3. **Hook `before_publish_page`** : enveloppe automatiquement les emojis
   d'une page à chaque publication, pour que les nouvelles pages n'aient
   jamais besoin de la commande manuelle.

Idempotent : ré-exécuter la commande ou republier une page déjà
enveloppée ne modifie rien (les spans déjà posés sont détectés et
ignorés).

## Installation

```bash
uv add --editable ../../packages/sites-conformes-rgaa
```

Ajouter à `INSTALLED_APPS` (pas de contrainte d'ordre - ce package ne
surcharge aucun template) :

```python
INSTALLED_APPS += ["sites_conformes_rgaa"]
```

## Utilisation

```bash
python manage.py wrap_emojis          # toutes les pages
python manage.py wrap_emojis --dry-run  # aperçu sans écrire
```

Les nouvelles publications sont couvertes automatiquement par le hook -
la commande sert surtout au rattrapage du contenu existant, ou en CI/CD
après une migration de contenu.

## Limites connues

Le vérificateur d'accessibilité Wagtail (axe-core, intégré à l'éditeur)
ne peut pas être étendu avec une règle personnalisée détectant les
emojis non enveloppés : les fonctions `evaluate` des checks axe
personnalisés sont figées dans le bundle JS compilé de Wagtail
(`wagtailadmin/js/userbar.js`), et ne peuvent pas être injectées depuis
une application Django. Voir la discussion dans `UPSTREAM_SUGGESTIONS.md`
à la racine du monorepo.
