from wagtail.snippets.models import register_snippet
from wagtail.snippets.views.snippets import SnippetViewSet, SnippetViewSetGroup

from .models import Question, Theme


class QuestionViewSet(SnippetViewSet):
    model = Question
    icon = "help"
    list_display = ["question", "theme", "date"]
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
