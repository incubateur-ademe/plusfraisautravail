"""Record sites_conformes_core.0091_category_tree on a database that already ran the
migrations it folded, so that ``migrate`` neither stops on the inconsistent history nor
replays it on columns that exist.

Only the proven states are touched. c1d2446e rewrote the history without ``replaces``:
- the previous chain ran, with or without its top-level step: record the row;
- core never reached the category tree: nothing to do, ``migrate`` runs it;
- the row is already there: nothing to do.
Anything else stops the job before ``migrate``, for a human to read. Drop this call from
manage_jobs.sh once prod is done, as for the content pages.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.recorder import MigrationRecorder
from sites_conformes.core.models import Category

CORE = "sites_conformes_core"
TREE = (CORE, "0091_category_tree")
CMS_PAGES_0004 = ("cms_pages", "0004_contentpage_categories_alter_blogentrypage_body_and_more")
CHAIN = frozenset({(CORE, "0091_category_parent_cascade"), (CORE, "0092_category_sib_order")})
CHAIN_WITH_TOP_LEVEL = CHAIN | {
    (CORE, "0093_index_page_filter_categories_top_level"),
    ("sites_conformes_blog", "0072_index_page_filter_categories_top_level"),
    ("sites_conformes_events", "0043_index_page_filter_categories_top_level"),
}
WATCHED_APPS = (
    CORE,
    "sites_conformes_blog",
    "sites_conformes_events",
    "sites_conformes_forms",
    "cms_pages",
)


def category_columns():
    table = Category._meta.db_table
    with connection.cursor() as cursor:
        if table not in connection.introspection.table_names(cursor):
            return set()
        return {
            column.name for column in connection.introspection.get_table_description(cursor, table)
        }


class Command(BaseCommand):
    help = "Record core 0091_category_tree on a database that ran the chain it folded (idempotent)."

    def handle(self, *args, **options):
        on_disk = MigrationLoader(None).disk_migrations
        if TREE not in on_disk:
            raise CommandError(f"{TREE} is not on disk: sites-conformes changed its history again.")

        recorder = MigrationRecorder(connection)
        applied = set(recorder.applied_migrations())
        old = applied & CHAIN_WITH_TOP_LEVEL
        unknown = {
            key
            for key in applied - CHAIN_WITH_TOP_LEVEL
            if key[0] in WATCHED_APPS and key not in on_disk
        }
        columns = category_columns()
        has_tree_schema = "sib_order" in columns and "sort_order" not in columns
        has_0004 = CMS_PAGES_0004 in applied

        if (
            not unknown
            and TREE in applied
            and has_tree_schema
            and old in (set(), CHAIN, CHAIN_WITH_TOP_LEVEL)
        ):
            self.stdout.write(f"{TREE[1]} is already recorded: nothing to do.")
        elif (
            not unknown
            and TREE not in applied
            and not old
            and "sib_order" not in columns
            and not has_0004
        ):
            self.stdout.write(
                "Core never reached the category tree: nothing to do, migrate will run it."
            )
        elif (
            not unknown
            and TREE not in applied
            and has_tree_schema
            and ((old == CHAIN_WITH_TOP_LEVEL and has_0004) or (old == CHAIN and not has_0004))
        ):
            recorder.record_applied(*TREE)
            self.stdout.write(
                self.style.SUCCESS(f"Recorded {TREE[1]}, over {len(old)} folded migrations.")
            )
        else:
            raise CommandError(
                "Unknown migration state, stopping before migrate. "
                f"Folded migrations applied: {sorted(old)}. "
                f"Unknown migrations: {sorted(unknown)}. {TREE[1]} applied: {TREE in applied}. "
                f"cms_pages 0004 applied: {has_0004}. "
                f"Category columns: {sorted(columns & {'sib_order', 'sort_order'})}."
            )
