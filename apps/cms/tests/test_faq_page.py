"""The FAQ block on the swapped ContentPage and BlogEntryPage: rendering, schema.org FAQPage
markup (checkbox checked by default) and the one-SEO-holder-per-question rule."""

import pytest
from django.core.exceptions import ValidationError
from sites_conformes.blog.models import BlogIndexPage
from sites_conformes_faq.blocks import FaqItemBlock
from sites_conformes_faq.models import Question
from wagtail.blocks.base import get_error_json_data
from wagtail.models import Site, get_page_models

from cms.pages.models import BlogEntryPage, ContentPage

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


def make_page(title, question, seo=True):
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


def test_seo_box_is_checked_by_default():
    assert FaqItemBlock().get_default()["seo"] is True


def test_checked_page_gets_faqpage_markup(client, question):
    page = make_page("Page A", question)
    html = client.get(page.url).content.decode()
    assert "fr-accordion" in html
    assert '"@type": "FAQPage"' in html
    assert question.question in html


def test_unchecked_page_has_no_markup(client, question):
    a = make_page("Page A", question, seo=False)
    b = make_page("Page B", question)
    assert '"@type": "FAQPage"' not in client.get(a.url).content.decode()
    assert '"@type": "FAQPage"' in client.get(b.url).content.decode()


def test_admin_linkifies_error_urls(client):
    from django.contrib.auth import get_user_model

    client.force_login(get_user_model().objects.create_superuser("admin", "a@example.org", "pw"))
    assert ".messages .errorlist li" in client.get("/cms-admin/").content.decode()


def test_second_holder_is_rejected(question):
    b = make_page("Page B", question)
    a = ContentPage(title="Page A", slug="page-a")
    a.body = [("faq", [{"question": question, "seo": True}])]
    # Page.save() runs full_clean(), so the rejection happens on insert.
    with pytest.raises(ValidationError) as err:
        Site.objects.get(is_default_site=True).root_page.add_child(instance=a)
    assert f"« Page B » /cms-admin/pages/{b.pk}/edit/" in str(err.value.error_dict["__all__"])
    # Block-level error, so the admin highlights the item's checkbox.
    assert get_error_json_data(err.value.error_dict["body"][0]) == {
        "blockErrors": {
            0: {
                "blockErrors": {
                    0: {"blockErrors": {"seo": {"messages": ["Déjà cochée sur « Page B »."]}}}
                }
            }
        }
    }


def make_blog_entry(title, question):
    root = Site.objects.get(is_default_site=True).root_page
    blog = root.add_child(instance=BlogIndexPage(title="Actualités", slug="actualites"))
    entry = BlogEntryPage(title=title, slug="article")
    entry.body = [("faq", [{"question": question, "seo": True}])]
    blog.add_child(instance=entry)
    entry.save_revision().publish()
    return entry


def test_swapped_model_is_the_only_blog_entry_page():
    labels = {m._meta.label for m in get_page_models()}
    assert "cms_pages.BlogEntryPage" in labels
    assert "sites_conformes_blog.BlogEntryPage" not in labels


def test_blog_entry_gets_faqpage_markup(client, question):
    entry = make_blog_entry("Article", question)
    html = client.get(entry.url).content.decode()
    assert "fr-accordion" in html
    assert '"@type": "FAQPage"' in html


def test_blog_entry_holder_blocks_a_content_page(question):
    entry = make_blog_entry("Article", question)
    page = ContentPage(title="Page A", slug="page-a")
    page.body = [("faq", [{"question": question, "seo": True}])]
    with pytest.raises(ValidationError) as err:
        Site.objects.get(is_default_site=True).root_page.add_child(instance=page)
    assert f"« Article » /cms-admin/pages/{entry.pk}/edit/" in str(err.value.error_dict["__all__"])
