from wagtail.snippets.models import register_snippet

from tests.testapp.models import ALCategory, MPCategory, NSCategory
from wagtail_admin_treebeard.views import TreeSnippetViewSet

for model in (ALCategory, MPCategory, NSCategory):
    register_snippet(
        type(
            f"{model.__name__}ViewSet",
            (TreeSnippetViewSet,),
            {"model": model, "search_fields": ["name"]},
        )
    )
