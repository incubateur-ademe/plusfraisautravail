# sites-conformes-faq

Questions / réponses gérées une seule fois dans le CMS (fragments Wagtail)
et réutilisables sur plusieurs pages (webinaire, solution, espace dédié…).

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

L'insertion des questions dans les pages (bloc StreamField) et le balisage
SEO `FAQPage` sont hors de ce package pour l'instant.
