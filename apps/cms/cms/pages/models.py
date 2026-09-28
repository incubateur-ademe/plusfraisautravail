"""Project content page, swapped in for sites-conformes' ContentPage via
``SF_CONTENTPAGE_MODEL`` so the body can carry the FAQ block."""

from django.core.exceptions import NON_FIELD_ERRORS, ValidationError
from django.urls import reverse
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
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


class ContentPage(AbstractContentPage):
    tags = ClusterTaggableManager(through="TagContentPage", blank=True)
    body = StreamField(
        STREAMFIELD_COMMON_BLOCKS + [("faq", FaqBlock())],
        blank=True,
        use_json_field=True,
        collapsed=True,
    )

    content_panels = AbstractContentPage.content_panels + [FieldPanel("tags")]
    api_fields = AbstractContentPage.api_fields + [APIField("tags")]

    class Meta:
        verbose_name = "Page de contenu"

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


class TagContentPage(TaggedItemBase):
    content_object = ParentalKey(ContentPage, related_name="tagged_items")
