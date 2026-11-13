"""The nightly e2e dump (infra/e2e-dump) must decide on every column that can hold text.

A migration that adds such a column must declare it in
infra/e2e-dump/rules.sql (MASKED or NOT MASKED), or list its table in
excluded-tables.txt. Otherwise this test fails, before the column can reach
the dump unmasked. The dump job runs the same check on the production schema.
"""

import re
from fnmatch import fnmatch
from pathlib import Path

import pytest
from django.db import connection

E2E_DUMP = Path(__file__).resolve().parents[3] / "infra" / "e2e-dump"


def _declared_columns():
    rules = (E2E_DUMP / "rules.sql").read_text()
    return set(re.findall(r"ON COLUMN (\w+\.\w+) IS", rules))


def _excluded_tables():
    lines = (E2E_DUMP / "excluded-tables.txt").read_text().splitlines()
    return {line.strip() for line in lines if line.strip() and not line.startswith("#")}


def _columns_to_declare():
    with connection.cursor() as cursor:
        cursor.execute((E2E_DUMP / "columns-to-declare.sql").read_text())
        columns = {row[0] for row in cursor.fetchall()}
    excluded = _excluded_tables()  # pg_dump patterns: wagtail_localize_*
    return {
        column
        for column in columns
        if not any(fnmatch(column.split(".")[0], pattern) for pattern in excluded)
    }


@pytest.mark.django_db
def test_every_column_is_declared():
    undeclared = _columns_to_declare() - _declared_columns()
    assert not undeclared, (
        "Declare these columns in infra/e2e-dump/rules.sql "
        f"(MASKED WITH ... or NOT MASKED): {sorted(undeclared)}"
    )


@pytest.mark.django_db
def test_no_rule_targets_a_missing_column():
    # A rule on a column that no longer exists makes the dump job fail.
    stale = _declared_columns() - _columns_to_declare()
    assert not stale, f"Remove these rules from infra/e2e-dump/rules.sql: {sorted(stale)}"
