from django.utils.functional import cached_property
from wagtail.admin.ui.tables import BooleanColumn, UsageCountColumn
from wagtail.models import ReferenceIndex
from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import (
    IndexView,
    SnippetViewSet,
    SnippetViewSetGroup,
    UsageView,
)

from .blocks import faq_items
from .models import Question, Theme


class QuestionIndexView(IndexView):
    def get_base_queryset(self):
        return (
            super()
            .get_base_queryset()
            .annotate(usage_count=ReferenceIndex.usage_count_subquery(Question))
        )


class QuestionUsageView(UsageView):
    """Wagtail's usage view, plus whether each page carries the question's SEO markup.

    The reference index is built from the page row, i.e. its live content (or its
    initial content if never published), so the SEO flag reads that same content."""

    def is_seo_holder(self, row):
        body = getattr(row["object"].specific, "body", [])
        return any(q.pk == self.object.pk and seo for q, seo in faq_items(body))

    @cached_property
    def columns(self):
        return [
            *super().columns,
            BooleanColumn("seo", label="Référence SEO", accessor=self.is_seo_holder),
            BooleanColumn("live", label="Publiée", accessor=lambda row: row["object"].live),
        ]


class QuestionViewSet(SnippetViewSet):
    model = Question
    icon = "help"
    index_view_class = QuestionIndexView
    usage_view_class = QuestionUsageView
    list_display = [
        "question",
        "theme",
        "date",
        UsageCountColumn("usage_count", label="Utilisation", sort_key="usage_count"),
    ]
    list_filter = ["theme", "authors"]
    search_fields = ["question", "answer"]


class ThemeViewSet(SnippetViewSet):
    model = Theme
    icon = "tag"


class FaqViewSetGroup(SnippetViewSetGroup):
    menu_label = "Questions / réponses"
    menu_icon = "help"
    items = [QuestionViewSet, ThemeViewSet]


register_snippet(FaqViewSetGroup)
