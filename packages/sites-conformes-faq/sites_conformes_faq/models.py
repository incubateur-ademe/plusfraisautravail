from django import forms
from django.db import models
from django.template.loader import render_to_string
from modelcluster.fields import ParentalManyToManyField
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, MultiFieldPanel
from wagtail.fields import RichTextField
from wagtail.models import PreviewableMixin
from wagtail.search import index


class Theme(models.Model):
    name = models.CharField("Nom", max_length=100, unique=True)

    panels = [FieldPanel("name")]

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Thème"
        ordering = ["name"]


class Question(PreviewableMixin, index.Indexed, ClusterableModel):
    # no drafts/revisions (DraftStateMixin), add when editors ask for them
    question = models.CharField("Question", max_length=255)
    answer = RichTextField("Réponse")
    authors = ParentalManyToManyField(
        "sites_conformes_blog.Person",
        verbose_name="Auteurs",
        blank=True,
        help_text="Les auteurs se créent dans Fragments > Personnes. "
        "Affichés en italique au-dessus de la réponse (rôle - nom - organisation).",
    )
    date = models.DateField(
        "Date",
        null=True,
        blank=True,
        help_text="Date de la réponse ou de sa dernière mise à jour (non affichée).",
    )
    theme = models.ForeignKey(
        Theme,
        verbose_name="Thème",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="questions",
    )
    link_page = models.ForeignKey(
        "wagtailcore.Page",
        verbose_name="Lien interne",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Affiché en bouton « En savoir plus » sous la réponse.",
    )
    link_url = models.URLField(
        "Lien externe",
        max_length=2000,
        blank=True,
        default="",
        help_text="Ignoré si un lien interne est renseigné.",
    )

    panels = [
        FieldPanel("question"),
        FieldPanel("answer"),
        FieldPanel("authors", widget=forms.CheckboxSelectMultiple),
        MultiFieldPanel(
            [FieldPanel("link_page"), FieldPanel("link_url")],
            heading="En savoir plus",
        ),
        MultiFieldPanel([FieldPanel("theme"), FieldPanel("date")], heading="Organisation"),
    ]

    search_fields = [
        index.SearchField("question"),
        index.SearchField("answer"),
        index.AutocompleteField("question"),
    ]

    @property
    def link(self):
        return self.link_page.url if self.link_page else self.link_url

    @property
    def authors_line(self):
        return ", ".join(
            " - ".join(filter(None, [p.role, p.name, str(p.organization or "")]))
            for p in self.authors.all()
        )

    @property
    def accordion(self):
        """Dict for django-dsfr's {% dsfr_accordion %} tag."""
        # id is per question, so the same question listed twice on
        # one page would share an id - pass a prefix if that ever happens.
        return {
            "id": f"faq-{self.pk or 'preview'}",
            "title": self.question,
            "content": render_to_string("sites_conformes_faq/question.html", {"question": self}),
        }

    def get_preview_template(self, request, mode_name):
        return "sites_conformes_faq/preview.html"

    def __str__(self):
        return self.question

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["question"]
