"""Project content and blog pages, swapped in for sites-conformes' ContentPage and
BlogEntryPage via ``SF_CONTENTPAGE_MODEL`` and ``SF_BLOGENTRYPAGE_MODEL`` so their
bodies can carry the FAQ block."""

import logging
from functools import cache

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import ProgrammingError, models, transaction
from django.urls import reverse
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from psycopg.errors import UndefinedTable
from sites_conformes.blog.models import AbstractBlogEntryPage
from sites_conformes.core.blocks.core import STREAMFIELD_COMMON_BLOCKS
from sites_conformes.core.models import AbstractContentPage, Category
from sites_conformes_faq.blocks import FaqBlock, seo_holder
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.blocks import (
    ListBlockValidationError,
    StreamBlockValidationError,
    StructBlockValidationError,
)
from wagtail.contrib.settings.models import BaseGenericSetting, register_setting
from wagtail.fields import StreamField

logger = logging.getLogger(__name__)


@cache
def warn_missing_table():
    """Once per process: tag blocks render by the dozen during the deployment window."""
    logger.warning(
        "cms_pages_tagsettings table missing: tag links stay on until migration 0006 runs"
    )


def faq_body():
    """The upstream page body, plus the FAQ block."""
    return StreamField(
        STREAMFIELD_COMMON_BLOCKS + [("faq", FaqBlock())],
        blank=True,
        use_json_field=True,
        collapsed=True,
    )


class FaqSeoMixin:
    """One live page only may carry the SEO markup of a question (see ``seo_holder``)."""

    def clean(self):
        super().clean()
        messages, stream_errors = [], {}
        for i, block in enumerate(self.body):
            if block.block_type != "faq":
                continue
            item_errors = {}
            for j, item in enumerate(block.value):
                question = item["question"]
                if question is None or not item["seo"]:
                    continue
                if holder := seo_holder(question, self):
                    url = reverse("wagtailadmin_pages:edit", args=[holder.pk])
                    item_errors[j] = StructBlockValidationError(
                        block_errors={
                            "seo": ValidationError(f"Déjà cochée sur « {holder.title} ».")
                        }
                    )
                    # Wagtail escapes messages; cms/pages/wagtail_hooks.py linkifies the URL.
                    messages.append(
                        f"La question « {question} » a déjà sa page de référence SEO : "
                        f"« {holder.title} » {url} Décochez-la ici ou là-bas."
                    )
            if item_errors:
                stream_errors[i] = ListBlockValidationError(block_errors=item_errors)
        if stream_errors:
            raise ValidationError(
                {
                    "body": StreamBlockValidationError(block_errors=stream_errors),
                    NON_FIELD_ERRORS: messages,
                }
            )


class ContentPage(FaqSeoMixin, AbstractContentPage):
    tags = ClusterTaggableManager(through="TagContentPage", blank=True)
    body = faq_body()

    content_panels = AbstractContentPage.content_panels + [FieldPanel("tags")]
    api_fields = AbstractContentPage.api_fields + [APIField("tags")]

    class Meta:
        verbose_name = "Page de contenu"


class TagContentPage(TaggedItemBase):
    content_object = ParentalKey(ContentPage, related_name="tagged_items")


class BlogEntryPage(FaqSeoMixin, AbstractBlogEntryPage):
    # Same model, field and related names as upstream: migrate_blog_entry_page_model
    # adopts the legacy tables by renaming them, and old revisions keep restoring.
    tags = ClusterTaggableManager(through="TagEntryPage", blank=True)
    categories = ParentalManyToManyField(
        Category, through="CategoryEntryPage", blank=True, verbose_name="Catégories"
    )
    body = faq_body()

    class Meta:
        verbose_name = "Page de blog"


class TagEntryPage(TaggedItemBase):
    content_object = ParentalKey(BlogEntryPage, related_name="entry_tags")


class CategoryEntryPage(models.Model):
    category = models.ForeignKey(
        Category, related_name="+", verbose_name="Catégorie", on_delete=models.CASCADE
    )
    page = ParentalKey(BlogEntryPage, related_name="entry_categories")


@register_setting(icon="tag")
class TagSettings(BaseGenericSetting):
    """Generic rather than per site: blocks rendered through ``{{ page.body }}`` have no request
    to find a site from."""

    links_enabled = models.BooleanField(
        "Tags cliquables et pages de tags",
        default=True,
        help_text=(
            "Décochez pour afficher les tags en texte simple sur tout le site et rendre les pages "
            "de tags indisponibles (erreur 404). Les blocs tag perdent aussi leur lien saisi à la "
            "main, quelle que soit sa cible. Ce réglage ne couvre pas les filtres par tag, à "
            "régler page par page sur les catalogues, le blog et l'agenda, et bloc par bloc sur "
            "les derniers billets ou événements. Il ne couvre pas non plus les liens saisis à la "
            "main vers /tags/ dans les contenus et les menus, qui mèneront à une erreur 404."
        ),
    )

    class Meta:
        verbose_name = "Tags"
        verbose_name_plural = "Tags"

    @classmethod
    def links_on(cls, request=None):
        """The deployment starts the new code before the migrate job: without this, tagged pages
        would answer 500 until then. Drop the ``try`` once 0006 ran in production."""
        try:
            # Savepoint: a failed query inside a transaction, as in Page.save, would break it.
            with transaction.atomic():
                return cls.load(request).links_enabled
        except ProgrammingError as error:
            if not isinstance(error.__cause__, UndefinedTable):
                raise
            warn_missing_table()
            return True
