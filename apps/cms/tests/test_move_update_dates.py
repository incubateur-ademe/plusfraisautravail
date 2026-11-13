"""move_update_dates_to_field moves the update dates typed in the bodies to the field,
cutting the date sentence out of its paragraph. The HTML cases come from prod."""

import json
from datetime import date

import pytest
from django.core.management import call_command
from wagtail.models import Site

from cms.pages.management.commands.move_update_dates_to_field import cut_dates
from cms.pages.models import ContentPage


def paragraph(html):
    return {"type": "paragraph", "value": html, "id": "p"}


@pytest.mark.parametrize(
    ("html", "left", "found"),
    [
        (
            '<p data-block-key="a"><i>Date de dernière mise à jour : 26 juin 2026</i></p>',
            None,
            date(2026, 6, 26),
        ),
        ('<p data-block-key="a"><i>Mis à jour le 20 mai 2026</i></p>', None, date(2026, 5, 20)),
        (
            '<p data-block-key="a"><i>Dernière mise à jour : 1er octobre 2026</i></p>',
            None,
            date(2026, 10, 1),
        ),
        (
            '<p data-block-key="a">Crédits photos : INRS<br/><br/>'
            "<i>Dernière mise à jour : 27 janvier 2026</i></p>",
            '<p data-block-key="a">Crédits photos : INRS</p>',
            date(2026, 1, 27),
        ),
        (
            '<p data-block-key="a"><i>Date de première publication : avril 2026<br/>'
            "Dernière mise à jour : 26 octobre 2026</i></p>",
            '<p data-block-key="a"><i>Date de première publication : avril 2026</i></p>',
            date(2026, 10, 26),
        ),
        (
            '<p data-block-key="a">Mis à jour le 10/10/2025<br/></p>'
            '<h2 data-block-key="b">1. Site</h2>',
            '<h2 data-block-key="b">1. Site</h2>',
            date(2025, 10, 10),
        ),
        (
            '<ul><li>Météo France</li></ul><hr/><p data-block-key="a">'
            "<i>Date de dernière mise à jour : 1er octobre 2026</i></p>",
            "<ul><li>Météo France</li></ul>",
            date(2026, 10, 1),
        ),
        (
            '<p data-block-key="a"><i><br/>Mis à jour le 20 mai 2026</i></p>',
            None,
            date(2026, 5, 20),
        ),
    ],
)
def test_cuts_the_date_sentence_out(html, left, found):
    blocks, latest = cut_dates([paragraph(html)])

    assert latest == found
    assert blocks == ([paragraph(left)] if left else [])


def test_keeps_the_latest_date_and_the_other_blocks():
    other = {"type": "highlight", "value": {"text": "Mise à jour : la société a fermé."}}
    blocks, latest = cut_dates(
        [
            paragraph("<p><i>Date de dernière mise à jour : 16 juin 2026</i></p>"),
            other,
            paragraph("<p><i>Date de dernière mise à jour : 22 juillet 2026</i></p>"),
        ]
    )

    assert latest == date(2026, 7, 22)
    assert blocks == [other]


@pytest.fixture
def page(db):
    root = Site.objects.get(is_default_site=True).root_page
    page = ContentPage(
        title="Isoler",
        slug="isoler",
        body=json.dumps(
            [
                paragraph("<p>Isoler les combles.</p>"),
                paragraph("<p><i>Mis à jour le 20 mai 2026</i></p>"),
            ]
        ),
    )
    root.add_child(instance=page)
    page.save_revision().publish()
    page.title = "Isoler (brouillon)"
    page.save_revision()  # pending draft: it must get the change too
    return ContentPage.objects.get(pk=page.pk)


def test_moves_the_date_to_the_field_in_the_page_and_its_draft(page):
    call_command("move_update_dates_to_field")

    page = ContentPage.objects.get(pk=page.pk)
    assert page.last_update_date == date(2026, 5, 20)
    assert [block.value.source for block in page.body] == ["<p>Isoler les combles.</p>"]
    draft = page.latest_revision.content
    assert draft["title"] == "Isoler (brouillon)"
    assert draft["last_update_date"] == "2026-05-20"
    assert [block["value"] for block in json.loads(draft["body"])] == ["<p>Isoler les combles.</p>"]
    assert page.get_latest_revision_as_object().last_update_date == date(2026, 5, 20)


def test_keeps_a_date_already_in_the_field(page):
    page.last_update_date = date(2026, 9, 1)
    page.save()

    call_command("move_update_dates_to_field")

    assert ContentPage.objects.get(pk=page.pk).last_update_date == date(2026, 9, 1)


def test_is_idempotent_and_dry_run_changes_nothing(page):
    call_command("move_update_dates_to_field", dry_run=True)
    assert ContentPage.objects.get(pk=page.pk).last_update_date is None

    call_command("move_update_dates_to_field")
    call_command("move_update_dates_to_field")
    assert len(ContentPage.objects.get(pk=page.pk).body) == 1


def test_hides_the_date_on_the_home_page_and_the_legal_notice(page):
    site = Site.objects.get(is_default_site=True)
    legal = ContentPage(
        title="Mentions légales",
        slug="mentions-legales",
        body=json.dumps([paragraph("<p>Mis à jour le 10/10/2025</p><h2>1. Site</h2>")]),
    )
    site.root_page.add_child(instance=legal)
    legal.save_revision().publish()
    site.root_page = page
    site.save()

    call_command("move_update_dates_to_field")

    for hidden in (page, legal):
        hidden = ContentPage.objects.get(pk=hidden.pk)
        assert hidden.show_update_date is False
        assert hidden.latest_revision.content["show_update_date"] is False
        assert hidden.last_update_date is None
    legal = ContentPage.objects.get(pk=legal.pk)
    assert "Mis à jour le 10/10/2025" in legal.body.raw_data[0]["value"]
