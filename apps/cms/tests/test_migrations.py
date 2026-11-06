"""The migration graph is checked without a database: a repin of sites-conformes can
rewrite its history, and the test database setup only reports that as a setup error."""

from django.apps import apps
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.loader import MigrationLoader
from django.db.migrations.state import ProjectState
from django.utils import translation


def test_migration_graph_loads_and_matches_the_models():
    loader = MigrationLoader(None)

    # Translations off, as in makemigrations: otherwise every verbose_name reads as a change.
    with translation.override(None):
        autodetector = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(apps))
        changes = autodetector.changes(graph=loader.graph)

    assert changes == {}
