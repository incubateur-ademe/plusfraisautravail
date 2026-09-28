# sites-conformes-faq

Système de FAQ (questions / réponses) centralisées, gérées au sein de Sites
Conformes.

Fragments exposés dans le menu **Questions / réponses** de l'admin :

- **Question** : question, réponse (texte riche), auteurs, date, thème, lien.
  Un aperçu rend la question en accordéon DSFR comme sur le site.
- **Thème** : pour organiser la liste des questions.

Les auteurs réutilisent les **Personnes** de sites-conformes
(Fragments → Personnes) : le rôle, le nom et l'organisation de la personne
composent la ligne d'auteur, affichée au-dessus de la réponse seulement si
« Afficher les auteurs » est coché (sinon information interne).

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

Balisage schema.org `FAQPage` : la case « Page de référence SEO » est cochée
par défaut et une seule page publiée peut la cocher pour une question donnée.
Quand la question est réutilisée ailleurs, on la décoche sur les pages
secondaires - `seo_holder()` sert à le valider dans le `clean()` de la page
(voir `cms.pages.models.ContentPage` dans ce dépôt).
