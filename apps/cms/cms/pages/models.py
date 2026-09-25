"""Project content page, swapped in for sites-conformes' ContentPage via
``SF_CONTENTPAGE_MODEL`` so the body can carry the FAQ block."""

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.html import format_html
from modelcluster.contrib.taggit import ClusterTaggableManager
from modelcluster.fields import ParentalKey
from sites_conformes.core.blocks.core import STREAMFIELD_COMMON_BLOCKS
from sites_conformes.core.models import AbstractContentPage
from sites_conformes_faq.blocks import FaqBlock, faq_items, seo_holder
from taggit.models import TaggedItemBase
from wagtail.admin.panels import FieldPanel
from wagtail.api import APIField
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
        for question, seo in faq_items(self.body):
            if seo and (holder := seo_holder(question, self)):
                raise ValidationError(
                    format_html(
                        "La question « {} » a déjà sa page de référence SEO : "
                        '<a href="{}">{}</a>. Décochez-la ici ou là-bas.',
                        question,
                        reverse("wagtailadmin_pages:edit", args=[holder.pk]),
                        holder.title,
                    )
                )


class TagContentPage(TaggedItemBase):
    content_object = ParentalKey(ContentPage, related_name="tagged_items")
