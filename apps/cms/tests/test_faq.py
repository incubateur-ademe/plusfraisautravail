import json

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from sites_conformes.blog.models import Organization, Person
from sites_conformes_faq.models import Question, Theme


@pytest.fixture
def question():
    org = Organization.objects.create(name="Com'Inject", slug="com-inject")
    person = Person.objects.create(
        name="Marion Paris", role="Retour d'expérience", organization=org
    )
    q = Question.objects.create(
        question="Quelles températures sont atteintes dans les ateliers ?",
        answer="<p>Environ 40 °C en été.</p>",
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
