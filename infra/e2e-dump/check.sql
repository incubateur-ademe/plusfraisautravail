-- Last gate before the upload (see dump.sh): any failure here aborts the run
-- and nothing leaves the container.
DO $$
DECLARE
    n bigint;
    t text;
BEGIN
    -- An empty copy (wrong database, revoked privilege) must not replace a good dump.
    IF NOT EXISTS (SELECT FROM wagtailcore_page WHERE depth > 1) THEN
        RAISE EXCEPTION 'no page: the copy of the database is empty';
    END IF;

    SELECT count(*) INTO n FROM auth_user
    WHERE email !~ '^user[0-9]+@example\.test$' OR username !~ '^user[0-9]+$' OR password <> '!';
    IF n > 0 THEN RAISE EXCEPTION 'auth_user: % rows not anonymised', n; END IF;

    SELECT count(*) INTO n FROM wagtailcore_revision
    WHERE content ? 'to_address' AND (
        content->>'to_address' <> 'formulaires@example.test'
        OR content->>'from_address' <> 'formulaires@example.test'
    );
    IF n > 0 THEN RAISE EXCEPTION 'revisions: % form addresses not anonymised', n; END IF;

    SELECT count(*) INTO n FROM wagtailcore_revision WHERE content ? 'wagtail_admin_comments';
    IF n > 0 THEN RAISE EXCEPTION 'revisions: % still carry comments', n; END IF;

    SELECT count(*) INTO n FROM sites_conformes_forms_formpage
    WHERE to_address <> 'formulaires@example.test' OR from_address <> 'formulaires@example.test';
    IF n > 0 THEN RAISE EXCEPTION 'formpage: % addresses not anonymised', n; END IF;

    -- Tables of excluded-tables.txt must have been dumped without rows
    -- (e2e.excluded_tables: their patterns as a regex, set by dump.sh).
    FOR t IN SELECT relname FROM pg_class
        WHERE relnamespace = 'public'::regnamespace AND relkind IN ('r', 'p')
            AND relname ~ ('^(' || current_setting('e2e.excluded_tables') || ')$')
    LOOP
        EXECUTE format('SELECT count(*) FROM %I', t) INTO n;
        IF n > 0 THEN RAISE EXCEPTION '%: % rows, should be empty', t, n; END IF;
    END LOOP;

    -- The extension must be gone: the dump has to restore on a plain Postgres.
    IF EXISTS (SELECT FROM pg_extension WHERE extname = 'anon')
        OR EXISTS (SELECT FROM pg_namespace WHERE nspname = 'e2e_masks') THEN
        RAISE EXCEPTION 'anon extension or masking functions still installed';
    END IF;
END $$;
