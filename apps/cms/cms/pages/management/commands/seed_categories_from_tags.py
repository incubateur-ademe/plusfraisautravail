"""Replace the page tags by categories.

Builds the category trees of CATEGORY_TREE (reusing the categories that already exist, by
name), puts every page carrying a mapped tag in the matching category, removes that tag
from the page, and switches the index pages of the migrated pages from the tag filter to
the category filter.
Pages and their latest revision are both updated, so a pending draft keeps the change.

Tags missing from CATEGORY_TREE are left on their pages and listed at the end.
Idempotent: rerunning changes nothing. ``--dry-run`` reports and rolls back."""

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction
from sites_conformes.core.models import Category
from wagtail.models import Page

# Root category -> child category -> tag slugs (several when the same thing was tagged twice).
# Roots and children are matched by name: "Levier" is the tree the editors built in prod.
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
    "Type de structure": {
        "Entreprise": ["entreprise"],
        "Collectivité": ["collectivité"],
        "EPIC": ["3-epic"],
    },
    "Levier": {
        "📒 Sensibilisation et formation": ["sensibilisation-formation"],
        "🏢 Bâtiments": ["batiments"],
        "🌳 Espaces extérieurs": ["exterieurs"],
        "⏱️ Organisation du travail": ["organisation-travail"],
    },
}


# Revisions saved before the ContentPage swap name the tag relation after the upstream model.
TAG_REVISION_KEYS = ("tagged_items", "contentpage_tags")


def tagged_page_models():
    """Concrete page models that have both tags and categories."""
    return [
        model
        for model in apps.get_models()
        if issubclass(model, Page)
        and hasattr(model, "tags")
        and "categories" in {f.name for f in model._meta.get_fields()}
    ]


def patch_latest_revision(page, patch):
    revision = page.latest_revision
    if revision is not None:
        revision.content = patch(revision.content)
        revision.save(update_fields=["content"])


class Command(BaseCommand):
    help = "Replace the page tags by categories, and the tag filters by category filters."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only, change nothing.")

    def handle(self, *args, dry_run=False, **options):
        with transaction.atomic():
            category_by_tag, created = self.build_trees()
            indexes, migrated = set(), 0
            for model in tagged_page_models():
                pages = model.objects.filter(tags__slug__in=category_by_tag).distinct()
                for page in pages.order_by("path"):
                    self.migrate_page(page, category_by_tag)
                    indexes.add(page.get_parent().specific)
                    migrated += 1
            for index in sorted(indexes, key=lambda page: page.path):
                self.switch_to_category_filter(index)
            self.report_leftover_tags()
            if dry_run:
                transaction.set_rollback(True)
        verb = "Would create" if dry_run else "Created"
        self.stdout.write(
            self.style.SUCCESS(f"{verb} {created} categories, migrated {migrated} pages.")
        )

    def build_trees(self):
        """Return {tag slug: category} and the number of categories created."""
        category_by_tag, created = {}, 0
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
                category_by_tag.update(dict.fromkeys(tag_slugs, category))
        return category_by_tag, created

    def migrate_page(self, page, category_by_tag):
        tags = [tag for tag in page.tags.all() if tag.slug in category_by_tag]
        categories = {category_by_tag[tag.slug] for tag in tags}
        page.categories.add(*categories)
        page.tags.remove(*(tag.name for tag in tags))  # modelcluster matches on names only
        page.save(clean=False)

        tag_ids = {tag.pk for tag in tags}

        def patch(content):
            return {
                **content,
                "categories": sorted({*content.get("categories", []), *(c.pk for c in categories)}),
                **{
                    key: [item for item in content[key] if item["tag"] not in tag_ids]
                    for key in TAG_REVISION_KEYS
                    if key in content
                },
            }

        patch_latest_revision(page, patch)
        names = ", ".join(sorted(c.name for c in categories))
        self.stdout.write(f"  {page.url_path}: {', '.join(t.name for t in tags)} -> {names}")

    def switch_to_category_filter(self, index):
        """Filter by category instead of tag: an editor may have hidden the category filter
        while its categories were empty (/solutions/ in prod)."""
        switched = {"filter_by_tag": False, "filter_by_category": True}
        if not hasattr(index, "filter_by_tag"):
            return
        if all(getattr(index, field) == value for field, value in switched.items()):
            return
        for field, value in switched.items():
            setattr(index, field, value)
        index.save(clean=False)
        patch_latest_revision(index, lambda content: {**content, **switched})
        self.stdout.write(f"  {index.url_path}: filters by category instead of tag")

    def report_leftover_tags(self):
        for model in tagged_page_models():
            for page in model.objects.exclude(tags=None).distinct().order_by("path"):
                tags = ", ".join(tag.slug for tag in page.tags.all())
                self.stdout.write(self.style.WARNING(f"  tags left on {page.url_path}: {tags}"))
