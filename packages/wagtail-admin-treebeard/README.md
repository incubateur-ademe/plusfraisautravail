# wagtail-admin-treebeard

Manage a [django-treebeard](https://django-treebeard.readthedocs.io/) tree
(AL, MP or NS) as a Wagtail snippet:

- the listing shows nodes nested under their parent, with drag and drop to
  move a node under another one or bring it back to the root;
- the edit form gets treebeard's `MoveNodeForm` fields ("Relative to" /
  "Position"), which also serves as the keyboard alternative to drag and drop.

Searching, filtering and sorting by column fall back to Wagtail's standard
flat table.

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
    node_order_by = ["name"]

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

`TranslatableMixin` models are supported: the tree is filtered on the locale
selected in the listing.

## Development

```bash
uv sync --extra dev
uv run pytest        # AL, MP and NS models on a minimal Wagtail project (tests/)
uv run ruff check .
```
