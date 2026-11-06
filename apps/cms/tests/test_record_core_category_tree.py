import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection
from django.db.migrations.recorder import MigrationRecorder

from cms.pages.management.commands.record_core_category_tree import (
    CHAIN,
    CHAIN_WITH_TOP_LEVEL,
    CMS_PAGES_0004,
    CORE,
    TREE,
)

pytestmark = pytest.mark.django_db

CATEGORY_TABLE = "sites_conformes_core_category"
CASCADE_ONLY = {(CORE, "0091_category_parent_cascade")}


def set_state(rows=frozenset(), *, tree=False, has_0004=True, sql=()):
    """Turn the test database, which ran the new graph, into the state to check."""
    recorder = MigrationRecorder(connection)
    if not tree:
        recorder.record_unapplied(*TREE)
    if not has_0004:
        recorder.record_unapplied(*CMS_PAGES_0004)
    for row in rows:
        recorder.record_applied(*row)
    with connection.cursor() as cursor:
        for statement in sql:
            cursor.execute(statement)


def tree_rows():
    return MigrationRecorder(connection).migration_qs.filter(app=TREE[0], name=TREE[1]).count()


BEFORE_THE_TREE = f"ALTER TABLE {CATEGORY_TABLE} RENAME COLUMN sib_order TO sort_order"
NO_CATEGORY_TABLE = f"ALTER TABLE {CATEGORY_TABLE} RENAME TO sites_conformes_blog_category"


@pytest.mark.parametrize(
    "rows, has_0004",
    [(CHAIN_WITH_TOP_LEVEL, True), (CHAIN, False)],
    ids=["S1", "S2"],
)
def test_records_the_row_once_on_a_proven_state(rows, has_0004):
    set_state(rows, has_0004=has_0004)

    call_command("record_core_category_tree")
    call_command("record_core_category_tree")

    assert tree_rows() == 1


@pytest.mark.parametrize(
    "sql", [BEFORE_THE_TREE, NO_CATEGORY_TABLE], ids=["sort_order", "no_table"]
)
def test_does_nothing_when_core_never_reached_the_tree(sql):
    set_state(has_0004=False, sql=[sql])

    call_command("record_core_category_tree")
    call_command("record_core_category_tree")

    assert tree_rows() == 0


def test_does_nothing_on_a_database_built_from_the_new_graph():
    call_command("record_core_category_tree")

    assert tree_rows() == 1


def test_stays_quiet_once_migrate_ran_after_the_row_was_recorded():
    set_state(CHAIN, tree=True)

    call_command("record_core_category_tree")

    assert tree_rows() == 1


@pytest.mark.parametrize(
    "state",
    [
        pytest.param({"rows": CASCADE_ONLY, "has_0004": False, "sql": [BEFORE_THE_TREE]}, id="H91"),
        pytest.param({"rows": CHAIN_WITH_TOP_LEVEL, "has_0004": False}, id="H93"),
        pytest.param({"rows": CHAIN, "has_0004": True}, id="S2_with_0004"),
        pytest.param(
            {"rows": CHAIN_WITH_TOP_LEVEL | {(CORE, "0092_category_order_tree")}},
            id="unknown_core_name",
        ),
        pytest.param(
            {"rows": CHAIN | {("cms_pages", "0005_unknown")}, "has_0004": False},
            id="unknown_cms_pages_name",
        ),
        pytest.param(
            {"rows": CHAIN | {(CORE, "0082_renamed")}, "has_0004": False}, id="unknown_old_number"
        ),
        pytest.param(
            {"rows": CHAIN_WITH_TOP_LEVEL, "sql": [BEFORE_THE_TREE]}, id="chain_without_its_column"
        ),
        pytest.param({"has_0004": False}, id="tree_schema_without_any_row"),
        pytest.param({"sql": [BEFORE_THE_TREE]}, id="0004_without_the_chain"),
    ],
)
def test_stops_on_any_other_state(state):
    set_state(**state)

    with pytest.raises(CommandError, match="stopping before migrate"):
        call_command("record_core_category_tree")

    assert tree_rows() == 0


def test_stops_when_the_row_is_recorded_without_its_schema():
    set_state(tree=True, sql=[BEFORE_THE_TREE])

    with pytest.raises(CommandError, match="stopping before migrate"):
        call_command("record_core_category_tree")


def test_stops_when_sites_conformes_renames_the_tree_again(monkeypatch):
    monkeypatch.setattr(
        "cms.pages.management.commands.record_core_category_tree.TREE", (CORE, "0091_renamed_again")
    )

    with pytest.raises(CommandError, match="changed its history again"):
        call_command("record_core_category_tree")
