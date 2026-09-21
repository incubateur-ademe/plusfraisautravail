# sites-conformes-faq

Système de FAQ (questions / réponses) centralisées, gérées au sein de Sites
Conformes.

Fragments exposés dans le menu **Questions / réponses** de l'admin :

- **Question** : question, réponse (texte riche), auteurs, date, thème, lien.
  Un aperçu rend la question en accordéon DSFR comme sur le site.
- **Thème** : pour organiser la liste des questions.

Les auteurs réutilisent les **Personnes** de sites-conformes
(Fragments → Personnes) : le rôle, le nom et l'organisation de la personne
composent la ligne d'auteur affichée au-dessus de la réponse.

## Installation

```bash
uv add --editable ../../packages/sites-conformes-faq
```

```python
INSTALLED_APPS = [..., "sites_conformes.blog", ..., "sites_conformes_faq"]
```

## Bloc de page

`sites_conformes_faq.blocks.FaqBlock` s'ajoute au `body` d'un modèle de page :
une liste de questions (fragment + case « Page de référence SEO ») rendue en
groupe d'accordéons DSFR.

Balisage schema.org `FAQPage` : une question publiée sur une seule page est
balisée automatiquement sur cette page. Une question affichée sur plusieurs
pages n'est balisée que sur la page où la case est cochée, et une seule page
peut la cocher - `seo_holder()` sert à le valider dans le `clean()` de la page
(voir `cms.pages.models.ContentPage` dans ce dépôt).
