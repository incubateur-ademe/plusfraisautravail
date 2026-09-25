"""FAQ block for page bodies: a list of Question snippets rendered as a DSFR
accordion group, with schema.org FAQPage markup for the questions whose
« Page de référence SEO » box is checked here. Checked by default; only one
live page may have it checked for a given question (``seo_holder``)."""

import json

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from wagtail import blocks
from wagtail.models import Page, ReferenceIndex
from wagtail.rich_text import expand_db_html
from wagtail.snippets.blocks import SnippetChooserBlock


class FaqItemBlock(blocks.StructBlock):
    question = SnippetChooserBlock("sites_conformes_faq.Question", label="Question")
    seo = blocks.BooleanBlock(
        label="Page de référence SEO",
        required=False,
        default=True,
        help_text="Cette page porte le balisage schema.org FAQPage de la question. Une seule "
        "page par question : décochez si la question est déjà référencée sur une autre page.",
    )


class FaqBlock(blocks.ListBlock):
    def __init__(self, **kwargs):
        super().__init__(FaqItemBlock(), **kwargs)

    class Meta:
        icon = "help"
        label = "Questions / réponses"
        group = _("DSFR components")
        template = "sites_conformes_faq/faq_block.html"

    def get_context(self, value, parent_context=None):
        context = super().get_context(value, parent_context=parent_context)
        page = (parent_context or {}).get("page")
        items = [item for item in value if item["question"] is not None]
        context["accordions"] = [item["question"].accordion for item in items]
        seo = [item["question"] for item in items if item["seo"]]
        context["seo_json"] = faq_jsonld(seo) if seo else ""
        return context


def pages_using(question):
    """Live pages whose published body references the question."""
    page_ct = ReferenceIndex._get_base_content_type(Page)
    ids = (
        ReferenceIndex.get_references_to(question)
        .filter(base_content_type=page_ct)
        .values_list("object_id", flat=True)
    )
    return Page.objects.live().filter(pk__in=[int(pk) for pk in ids])


def faq_items(body):
    """Top-level FAQ items of a page body, as (question, seo) pairs."""
    for block in body:
        if block.block_type == "faq":
            for item in block.value:
                if item["question"] is not None:
                    yield item["question"], bool(item["seo"])


def seo_holder(question, exclude_page):
    """The other live page that already claims the SEO markup for this question, if any."""
    for other in pages_using(question).exclude(pk=exclude_page.pk).specific():
        if any(q.pk == question.pk and seo for q, seo in faq_items(getattr(other, "body", []))):
            return other
    return None


def faq_jsonld(questions):
    data = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": q.question,
                "acceptedAnswer": {"@type": "Answer", "text": expand_db_html(q.answer)},
            }
            for q in questions
        ],
    }
    # "</" would close the <script> early; JSON allows the escaped slash.
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("</", "<\\/"))
