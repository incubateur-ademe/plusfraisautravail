"""Project content and blog pages, swapped in for sites-conformes' ContentPage and
BlogEntryPage via ``SF_CONTENTPAGE_MODEL`` and ``SF_BLOGENTRYPAGE_MODEL`` so their
bodies can carry the FAQ block."""

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.db import models
from django.urls import reverse
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey, ParentalManyToManyField
from sites_conformes.blog.models import AbstractBlogEntryPage, Category
from sites_conformes.core.blocks.core import STREAMFIELD_COMMON_BLOCKS
from sites_conformes.core.models import AbstractContentPage
from sites_conformes_faq.blocks import FaqBlock, seo_holder
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
from wagtail.blocks import (
    ListBlockValidationError,
    StreamBlockValidationError,
    StructBlockValidationError,
)
from wagtail.fields import StreamField


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
    blog_categories = ParentalManyToManyField(
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
