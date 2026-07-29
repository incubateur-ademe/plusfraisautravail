"""Wrap decorative emojis automatically whenever a page is published.

Wagtail's before_publish_page hook fires too late to affect what gets
published: by that point PublishPageRevisionAction reconstructs the page
from the revision's already-serialized JSON
(`self.object = self.revision.as_object()`), so mutating the in-memory
page instance in that hook has no effect. Listening to page_published
instead and, if wrapping changed anything, saving and publishing one more
revision - guaranteed to terminate after at most one extra round-trip,
since wrap_emojis_in_html/wrap_emojis_in_streamfield_raw_data are
idempotent (the second pass finds nothing left to wrap).
"""

from django.dispatch import receiver
from wagtail.fields import RichTextField, StreamField
from wagtail.signals import page_published

from sites_conformes_rgaa.emoji_wrapping import (
    wrap_emojis_in_html,
    wrap_emojis_in_streamfield_raw_data,
)


def wrap_emojis_on_page(page) -> bool:
    """Wrap emojis in every RichTextField/StreamField on this page instance.
    Returns True if anything changed (caller is responsible for saving)."""
    changed = False
    for field in page._meta.concrete_fields:
        if isinstance(field, RichTextField):
            value = getattr(page, field.name)
            new_value, field_changed = wrap_emojis_in_html(value)
            if field_changed:
                setattr(page, field.name, new_value)
                changed = True
        elif isinstance(field, StreamField):
            raw_data = list(getattr(page, field.name).raw_data)
            new_raw_data, field_changed = wrap_emojis_in_streamfield_raw_data(raw_data)
            if field_changed:
                setattr(page, field.name, field.stream_block.to_python(new_raw_data))
                changed = True
    return changed


@receiver(page_published)
def wrap_emojis_on_publish(sender, instance, revision, **kwargs):
    if not wrap_emojis_on_page(instance):
        return
    instance.save_revision().publish()
