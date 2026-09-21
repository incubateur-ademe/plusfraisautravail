"""The FAQ block on the swapped ContentPage: rendering, schema.org FAQPage
markup ownership, and the one-SEO-holder-per-question rule."""

import pytest
from django.core.exceptions import ValidationError
from sites_conformes_faq.models import Question
from wagtail.models import Site, get_page_models

from cms.pages.models import ContentPage

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def plain_static(settings):
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def question():
    return Question.objects.create(
        question="Existe-t-il une température maximale pour travailler ?",
        answer="<p>Non, mais l'employeur doit évaluer le risque.</p>",
    )


def make_page(title, question, seo=False):
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(title=title, slug=title.lower().replace(" ", "-"))
    page.body = [("faq", [{"question": question, "seo": seo}])]
    root.add_child(instance=page)
    page.save_revision().publish()
    return page


def test_swapped_model_is_the_only_content_page():
    labels = {m._meta.label for m in get_page_models()}
    assert "cms_pages.ContentPage" in labels
    assert "sites_conformes_core.ContentPage" not in labels


def test_single_page_gets_faqpage_markup(client, question):
    page = make_page("Page A", question)
    html = client.get(page.url).content.decode()
    assert "fr-accordion" in html
    assert '"@type": "FAQPage"' in html
    assert question.question in html


def test_shared_question_needs_an_explicit_holder(client, question):
    a = make_page("Page A", question)
    b = make_page("Page B", question, seo=True)
    assert '"@type": "FAQPage"' not in client.get(a.url).content.decode()
    assert '"@type": "FAQPage"' in client.get(b.url).content.decode()


def test_second_holder_is_rejected(question):
    make_page("Page B", question, seo=True)
    a = ContentPage(title="Page A", slug="page-a")
    a.body = [("faq", [{"question": question, "seo": True}])]
    # Page.save() runs full_clean(), so the rejection happens on insert.
    with pytest.raises(ValidationError, match="Page B"):
        Site.objects.get(is_default_site=True).root_page.add_child(instance=a)
