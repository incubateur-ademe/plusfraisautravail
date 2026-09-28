import datetime
import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from sites_conformes.blog.models import Organization, Person
from sites_conformes_faq.models import Question, Theme
from wagtail.models import Site


@pytest.fixture
def question():
    org = Organization.objects.create(name="Com'Inject", slug="com-inject")
    person = Person.objects.create(
        name="Marion Paris", role="Retour d'expérience", organization=org
    )
    q = Question.objects.create(
        question="Quelles températures sont atteintes dans les ateliers ?",
        answer=(
            '<p>Environ 40 °C en été. <a href="https://inrs.fr/">INRS</a> '
            'et <a href="/solutions/">nos solutions</a>.</p>'
        ),
        theme=Theme.objects.create(name="Bâtiments et équipements"),
        link_url="https://example.org/plus",
    )
    q.authors.add(person)
    q.save()
    return q


@pytest.fixture(autouse=True)
def plain_static(settings):
    # Production settings use the manifest storage, which needs collectstatic.
    settings.STORAGES = {
        **settings.STORAGES,
        "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    }


@pytest.fixture
def admin(client):
    user = get_user_model().objects.create_superuser("admin", "admin@example.org", "pw")
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_authors_line_and_link(question):
    assert question.authors_line == "Retour d'expérience - Marion Paris - Com'Inject"
    assert question.link == "https://example.org/plus"


@pytest.mark.django_db
def test_link_text_defaults_to_en_savoir_plus(question):
    html = question.accordion["content"]
    assert ">En savoir plus</a>" in html
    question.link_text = "Consulter l'ouvrage"
    assert ">Consulter l&#x27;ouvrage</a>" in question.accordion["content"]


@pytest.mark.django_db
def test_external_links_open_in_new_tab(question):
    html = question.accordion["content"]
    assert (
        'href="https://inrs.fr/"' in html
        and 'target="_blank" rel="noopener external" href="https://inrs.fr/"' in html
    )
    assert 'target="_blank" rel="noopener external" href="/solutions/"' not in html
    assert "fr-icon-external-link-line" in html and "nouvelle fenêtre" in html
    question.link_url = ""
    question.link_page = Site.objects.get(is_default_site=True).root_page
    internal = question.accordion["content"]
    assert (
        "fr-icon-arrow-right-line" in internal
        and 'target="_blank" rel="noopener external" href="/"' not in internal
    )


@pytest.mark.django_db
def test_authors_hidden_unless_asked(question):
    assert "Marion Paris" not in question.accordion["content"]
    question.show_authors = True
    assert (
        "<em>Retour d&#x27;expérience - Marion Paris - Com&#x27;Inject</em>"
        in question.accordion["content"]
    )


@pytest.mark.django_db
def test_date_defaults_to_today():
    assert Question(question="?", answer="").date == datetime.date.today()


@pytest.mark.django_db
def test_admin_listing_shows_question(admin, question):
    response = admin.get(reverse("wagtailsnippets_sites_conformes_faq_question:list"))
    assert response.status_code == 200
    assert question.question in response.content.decode()


@pytest.mark.django_db
def test_preview_renders_accordion(admin, question):
    url = reverse(
        "wagtailsnippets_sites_conformes_faq_question:preview_on_edit", args=[question.pk]
    )
    # Draftail posts the answer as contentstate JSON, not HTML.
    answer = json.dumps(
        {"blocks": [{"type": "unstyled", "text": "Environ 40 °C en été."}], "entityMap": {}}
    )
    assert admin.post(url, {"question": question.question, "answer": answer}).status_code == 200
    html = admin.get(url).content.decode()
    assert "fr-accordion" in html
    assert question.question in html
    assert "Environ 40" in html
