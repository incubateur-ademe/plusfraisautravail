# wagtail-notion-contact

Sync submissions of a sites-conformes contact `FormPage` (4 fields: name,
email, subject, message) into a Notion database, mirroring the pattern used
by [quefairedemesobjets](https://github.com/incubateur-ademe/quefairedemesobjets/blob/main/webapp/core/notion.py).

## Install

```bash
uv add --editable ../../packages/wagtail-notion-contact
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS += ["wagtail_notion_contact"]
```

Set the Notion API token (from a [Notion internal integration](https://www.notion.so/my-integrations)):

```bash
NOTION_TOKEN=secret_...
```

Then in the Wagtail admin, under **Settings → Notion contact sync**:
1. Pick the `FormPage` to watch (must have exactly 4 fields, in this order:
   name, email, subject, message).
2. Set the Notion database ID (the UUID in the database's URL) and share
   that database with your Notion integration.

Every new submission to the configured form is pushed to Notion as a new
row. Failures are logged, never raised to the site visitor.
