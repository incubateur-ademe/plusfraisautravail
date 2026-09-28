"""Build the "Secteur d'activités" and "Régions" category trees from the tags the site
already uses, and put every content page carrying one of those tags in the matching
category. Idempotent: rerunning adds nothing. ``--dry-run`` reports and rolls back.

Tags stay in place; nothing is deleted."""

from django.core.management.base import BaseCommand
from django.db import transaction
from sites_conformes.core.models import Category

from cms.pages.models import ContentPage

# Root category -> child category -> tag slugs (several when the same thing was tagged twice).
CATEGORY_TREE = {
    "Secteur d'activités": {
        "Agriculture": ["agriculture"],
        "BTP": ["btp"],
        "Commerce": ["commerce"],
        "Gestion forestière": ["gestion-forestière"],
        "Industrie": ["industrie"],
        "Santé": ["santé"],
        "Service aux entreprises": ["service-aux-entreprises"],
        "Télécoms": ["télécoms"],
        "Tertiaire": ["tertiaire"],
    },
    "Régions": {
        "Auvergne-Rhône-Alpes": ["auvergne-rhône-alpes"],
        "Bourgogne-Franche-Comté": ["bourgogne-franche-comté"],
        "France entière": ["france-entière"],
        "Grand Est": ["grand-est"],
        "Hauts-de-France": ["hauts-de-france", "hauts-de-france_1"],
        "Île-de-France": ["île-de-france"],
        "Nouvelle-Aquitaine": ["nouvelle-aquitaine"],
        "Pays de la Loire": ["pays-de-la-loire"],
        "Provence-Alpes-Côte d'Azur": [
            "paca",
            "alpes-de-haute-provence",
            "alpes-de-haute-provence_1",
        ],
    },
}


class Command(BaseCommand):
    help = "Create the sector and region categories from the tags and categorise the pages."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only, change nothing.")

    def handle(self, *args, dry_run=False, **options):
        created, assigned = 0, 0
        with transaction.atomic():
            for root_name, children in CATEGORY_TREE.items():
                root = Category.objects.filter(name=root_name, parent=None).first()
                if root is None:
                    root = Category.add_root(name=root_name)
                    created += 1
                for name, tag_slugs in children.items():
                    category = root.get_children().filter(name=name).first()
                    if category is None:
                        category = root.add_child(name=name)
                        created += 1
                    for page in ContentPage.objects.filter(tags__slug__in=tag_slugs).distinct():
                        assigned += self.categorise(page, category)
            if dry_run:
                transaction.set_rollback(True)
        verb = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {created} categories, {assigned} page-category links.")
        )

    def categorise(self, page, category):
        """Add ``category`` to the page and to its latest revision, so the editor keeps it."""
        if page.categories.filter(pk=category.pk).exists():
            return 0
        page.categories.add(category)
        page.save(clean=False)
        revision = page.latest_revision
        if revision is not None:
            content = revision.content
            content["categories"] = sorted({*content.get("categories", []), category.pk})
            revision.content = content
            revision.save(update_fields=["content"])
        self.stdout.write(f"  {page.title} -> {category.name}")
        return 1
