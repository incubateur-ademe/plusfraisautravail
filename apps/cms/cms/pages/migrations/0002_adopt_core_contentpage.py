"""Adopt pages created with sites-conformes' own ContentPage before
``SF_CONTENTPAGE_MODEL`` pointed at ``cms_pages.ContentPage``.

Upstream warns the swap must happen before the first migration; prod
predates it. Same trick as upstream's ``migrate_from_sites_faciles``: copy
the rows into our tables, then rename the content type row in place so
every FK to it (pages, revisions, log entries, permissions, search index)
follows without being touched.

Idempotent: no-op once the old table is gone or empty. Old tables are left
behind on purpose - drop them by hand once prod looks right.
"""

from django.db import migrations

OLD_APP, NEW_APP = "sites_conformes_core", "cms_pages"
TABLES = [  # (model, column identifying a row)
    ("contentpage", "page_ptr_id"),
    ("tagcontentpage", "id"),
]


def _columns(cursor, table):
    cursor.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        [table],
    )
    return {row[0] for row in cursor.fetchall()}


def _copy_rows(cursor, model, key):
    old, new = f"{OLD_APP}_{model}", f"{NEW_APP}_{model}"
    old_cols = _columns(cursor, old)
    if not old_cols:
        return
    cols = ", ".join(f'"{c}"' for c in sorted(old_cols & _columns(cursor, new)))
    cursor.execute(
        f'INSERT INTO "{new}" ({cols}) SELECT {cols} FROM "{old}" '
        f'WHERE "{key}" NOT IN (SELECT "{key}" FROM "{new}")'
    )


def _rename_content_type(cursor, model):
    q = "SELECT id FROM django_content_type WHERE app_label = %s AND model = %s"
    cursor.execute(q, [OLD_APP, model])
    if (old := cursor.fetchone()) is None:
        return
    cursor.execute(q, [NEW_APP, model])
    if new := cursor.fetchone():
        # post_migrate already created ours (a dev DB that ran 0001 earlier).
        # Only safe to drop if nothing points at it yet.
        cursor.execute("SELECT count(*) FROM wagtailcore_page WHERE content_type_id = %s", [new[0]])
        if cursor.fetchone()[0]:
            raise RuntimeError(
                f"Both {OLD_APP}.{model} and {NEW_APP}.{model} content types are in use; "
                "merge them by hand before applying this migration."
            )
        cursor.execute("DELETE FROM django_content_type WHERE id = %s", [new[0]])
    cursor.execute("UPDATE django_content_type SET app_label = %s WHERE id = %s", [NEW_APP, old[0]])


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        for model, key in TABLES:
            _copy_rows(cursor, model, key)
            _rename_content_type(cursor, model)
        # Copied tag rows keep their ids; move the sequence past them.
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('cms_pages_tagcontentpage', 'id'), "
            "COALESCE((SELECT max(id) FROM cms_pages_tagcontentpage), 0) + 1, false)"
        )


class Migration(migrations.Migration):
    dependencies = [
        ("cms_pages", "0001_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("wagtailcore", "0097_baselogentry_uuid_action_timestamp_indexes"),
    ]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
