-- Columns rules.sql must declare (MASKED or NOT MASKED): every column of
-- every table and materialised view outside the system schemas, except the
-- types that cannot hold personal data. One "table.column" per row.
-- Used by dump.sh, on the production schema, and by the CI test
-- apps/cms/tests/test_e2e_dump_rules.py. Callers leave out excluded-tables.txt.
SELECT c.relname || '.' || a.attname
FROM pg_attribute a
JOIN pg_class c ON c.oid = a.attrelid
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p', 'm')
  AND a.attnum > 0
  AND NOT a.attisdropped
  AND n.nspname NOT IN ('pg_catalog', 'information_schema', 'anon', 'e2e_masks')
  AND n.nspname NOT LIKE 'pg\_%'
  AND format_type(a.atttypid, NULL) NOT IN (
    'smallint', 'integer', 'bigint', 'numeric', 'real', 'double precision',
    'boolean', 'date', 'time without time zone', 'timestamp without time zone',
    'timestamp with time zone', 'interval', 'uuid'
  )
ORDER BY 1;
