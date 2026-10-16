"""Create the "Secteur d'activités" and "Régions" category trees of seed_categories_from_tags,
without putting any page in them: editors categorise the pages themselves.
Idempotent: rerunning adds nothing. ``--dry-run`` reports and rolls back."""

from django.core.management.base import BaseCommand
from django.db import transaction
from sites_conformes.core.models import Category

from cms.pages.management.commands.seed_categories_from_tags import CATEGORY_TREE


class Command(BaseCommand):
    help = "Create the sector and region categories, without categorising any page."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only, change nothing.")

    def handle(self, *args, dry_run=False, **options):
        created = 0
        with transaction.atomic():
            for root_name, children in CATEGORY_TREE.items():
                root = Category.objects.filter(name=root_name, parent=None).first()
                if root is None:
                    root = Category.add_root(name=root_name)
                    created += 1
                for name in children:
                    if not root.get_children().filter(name=name).exists():
                        root.add_child(name=name)
                        created += 1
            if dry_run:
                transaction.set_rollback(True)
        verb = "Would create" if dry_run else "Created"
        self.stdout.write(self.style.SUCCESS(f"{verb} {created} categories."))
