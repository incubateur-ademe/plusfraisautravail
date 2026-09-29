# wagtail-admin-treebeard

Manage a [django-treebeard](https://django-treebeard.readthedocs.io/) tree
(AL, MP or NS) as a Wagtail snippet:

- the standard snippet listing is shown in tree order, rows indented by depth,
  with drag and drop: drop a row on another one to nest it, or between two rows
  to move it there (reordering siblings on unsorted models). Everything else in
  the listing works as usual;
- the edit form gets treebeard's `MoveNodeForm` fields ("Relative to" /
  "Position"), which also serves as the keyboard alternative to drag and drop.

Searching, filtering and sorting by column give the plain paginated listing.

## Installation

```bash
uv add --editable ../../packages/wagtail-admin-treebeard
```

```python
INSTALLED_APPS = [
    ...,
    "wagtail_admin_treebeard",
    "treebeard",  # for its translations ("Relative to", "Child of", ...)
]
```

## Usage

On the treebeard model:

```python
from treebeard.al_tree import AL_Node
from wagtail.admin.panels import FieldPanel
from wagtail_admin_treebeard.forms import TreeNodeForm, tree_panel


class Category(AL_Node):
    name = models.CharField(max_length=80)
    parent = models.ForeignKey("self", null=True, blank=True, related_name="children_set", on_delete=models.CASCADE)
    sib_order = models.PositiveIntegerField()  # AL_Node only; not needed with node_order_by

    base_form_class = TreeNodeForm
    panels = [FieldPanel("name"), tree_panel()]
```

In `wagtail_hooks.py`:

```python
from wagtail.snippets.models import register_snippet
from wagtail_admin_treebeard.views import TreeSnippetViewSet


class CategoryViewSet(TreeSnippetViewSet):
    model = Category
    icon = "tag"
    list_display = ["name"]
    search_fields = ["name"]


register_snippet(CategoryViewSet)
```

Leave `node_order_by` undefined to let editors order siblings by drag and drop.
With `node_order_by` set, treebeard keeps siblings sorted: rows can only be
nested or brought back to the root, and the listing says so.

`TranslatableMixin` models are supported: the tree is filtered on the locale
selected in the listing.

## Development

```bash
uv sync --extra dev
uv run pytest        # AL, MP and NS models on a minimal Wagtail project (tests/)
uv run ruff check .
```
