"""Move the update dates the editors typed in the page bodies ("Date de dernière mise à
jour : 26 juin 2026", "Mis à jour le 20/05/2026"...) to ContentPage.last_update_date,
which the template now shows at the end of the content.

The home page and the legal notice hide the date instead (show_update_date), and keep
whatever date their body carries.

Only top-level paragraph blocks are read. The date sentence is cut out of its paragraph
(with its italics and line breaks), and the block is dropped when nothing is left. The
latest date found wins; a date already in the field is kept. The page and its latest
revision are both updated, so a pending draft keeps the change.
Idempotent: rerunning changes nothing. ``--dry-run`` reports and rolls back."""

import json
import re
from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction
from wagtail.blocks import StreamValue
from wagtail.models import Site

from cms.pages.models import ContentPage

# ponytail: the pages the user wants without the date, besides the home pages; editors
# untick the others in the admin.
HIDDEN_SLUGS = ("mentions-legales",)
MONTHS = (
    "janvier février mars avril mai juin juillet août septembre octobre novembre décembre"
).split()
DATE = (
    r"(?:date de )?(?:dernière )?mise? à jour\s*(?:le|:)?\s*"
    r"(?:(?P<day>\d{1,2})(?:er)?\s+(?P<month>" + "|".join(MONTHS) + r")\s+(?P<year>20\d\d)"
    r"|(?P<d>\d{1,2})/(?P<m>\d{1,2})/(?P<y>20\d\d))"
)
# The sentence, with the line breaks before it and its italics: <br/><i>Date ... 2026</i>
SENTENCE = re.compile(
    r"(?:<br/>)*(<(i|em)>)?(?:<br/>)*" + DATE + r"\.?(?:<br/>)*(?(1)</\2>)", re.IGNORECASE
)
EMPTY_PARAGRAPH = re.compile(r"<p[^>]*>(?:\s|<br/>)*</p>")
TRAILING_RULE = re.compile(r"(?:<hr/>\s*)+$")


def parse(match):
    if match["day"]:
        return date(int(match["year"]), MONTHS.index(match["month"].lower()) + 1, int(match["day"]))
    return date(int(match["y"]), int(match["m"]), int(match["d"]))


def cut_dates(blocks):
    """Return the blocks without the date sentences, and the latest date found."""
    kept, dates = [], []
    for block in blocks:
        html = block["value"]
        if block["type"] != "paragraph" or not SENTENCE.search(html):
            kept.append(block)
            continue
        dates += [parse(match) for match in SENTENCE.finditer(html)]
        html = TRAILING_RULE.sub("", EMPTY_PARAGRAPH.sub("", SENTENCE.sub("", html)))
        if html.strip():
            kept.append({**block, "value": html})
    return kept, max(dates, default=None)


class Command(BaseCommand):
    help = "Move the update dates typed in the page bodies to the update date field."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report only, change nothing.")

    def handle(self, *args, dry_run=False, **options):
        moved, hidden = 0, 0
        home_ids = set(Site.objects.values_list("root_page_id", flat=True))
        with transaction.atomic():
            for page in ContentPage.objects.order_by("path"):
                if page.pk in home_ids or page.slug in HIDDEN_SLUGS:
                    hidden += self.hide_date(page)
                else:
                    moved += self.move_dates(page)
            if dry_run:
                transaction.set_rollback(True)
        verb = "Would move" if dry_run else "Moved"
        self.stdout.write(
            self.style.SUCCESS(
                f"{verb} the update date of {moved} pages, hid it on {hidden} pages."
            )
        )

    def hide_date(self, page):
        if not page.show_update_date:
            return 0
        page.show_update_date = False
        page.save(clean=False)
        revision = page.latest_revision
        if revision is not None:
            revision.content = {**revision.content, "show_update_date": False}
            revision.save(update_fields=["content"])
        self.stdout.write(f"  {page.url_path}: date hidden")
        return 1

    def move_dates(self, page):
        blocks, found = cut_dates(list(page.body.raw_data))
        revision = page.latest_revision
        draft = revision.content if revision else {}
        draft_blocks, draft_found = cut_dates(json.loads(draft.get("body") or "[]"))
        if found is None and draft_found is None:
            return 0

        if found is not None:
            page.body = StreamValue(page.body.stream_block, blocks, is_lazy=True)
            page.last_update_date = page.last_update_date or found
            page.save(clean=False)
        if draft_found is not None:
            revision.content = {
                **draft,
                "body": json.dumps(draft_blocks),
                "last_update_date": draft.get("last_update_date") or draft_found.isoformat(),
            }
            revision.save(update_fields=["content"])
        self.stdout.write(f"  {page.url_path}: {found or '-'} (brouillon : {draft_found or '-'})")
        return 1
